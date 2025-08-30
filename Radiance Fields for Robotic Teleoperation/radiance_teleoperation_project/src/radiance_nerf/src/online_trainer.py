#!/usr/bin/env python3

"""
Radiance Fields for Robotic Teleoperation - 온라인 학습 시스템
Phase 3: Radiance Field 통합

이 모듈은 실시간으로 수집된 데이터를 사용하여 NeRF 모델을 온라인으로 훈련합니다.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
import time
import threading
from typing import Dict, List, Optional, Tuple
import rospy
from dataclasses import dataclass

# NerfStudio imports
try:
    from nerfstudio.models.base_model import Model
    from nerfstudio.cameras.rays import RayBundle
    from nerfstudio.data.datasets.base_dataset import InputDataset
    from nerfstudio.engine.trainer import Trainer
    from nerfstudio.utils.writer import EventName, TimeWriter
    NERFSTUDIO_AVAILABLE = True
except ImportError:
    NERFSTUDIO_AVAILABLE = False
    rospy.logwarn("NerfStudio가 설치되지 않았습니다.")

@dataclass
class OnlineTrainingConfig:
    """온라인 훈련 설정"""
    learning_rate: float = 1e-3
    batch_size: int = 4096
    num_rays_per_batch: int = 4096
    max_iterations: int = 1000
    save_interval: int = 100
    eval_interval: int = 50
    log_interval: int = 10
    device: str = "cuda"
    model_type: str = "nerfacto"  # nerfacto, instant-ngp, gaussian-splatting
    enable_online_learning: bool = True
    memory_efficient: bool = True

class OnlineTrainer:
    """
    온라인 NeRF 훈련기
    """
    
    def __init__(self, config: OnlineTrainingConfig, model: Optional[Model] = None):
        """
        온라인 훈련기 초기화
        
        Args:
            config: 훈련 설정
            model: NeRF 모델 (None이면 기본 모델 생성)
        """
        if not NERFSTUDIO_AVAILABLE:
            raise ImportError("NerfStudio가 필요합니다.")
        
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else "cpu")
        
        # 모델 초기화
        self.model = model if model is not None else self._create_default_model()
        self.model.to(self.device)
        
        # 옵티마이저 및 손실 함수
        self.optimizer = optim.Adam(self.model.parameters(), lr=config.learning_rate)
        self.criterion = nn.MSELoss()
        
        # 훈련 상태
        self.is_training = False
        self.current_iteration = 0
        self.training_losses = []
        self.eval_metrics = {}
        
        # 데이터 관리
        self.dataset = None
        self.dataloader = None
        
        # 스레드 안전
        self.lock = threading.Lock()
        
        # 성능 모니터링
        self.time_writer = TimeWriter()
        self.last_training_time = time.time()
        
        rospy.loginfo("온라인 훈련기가 초기화되었습니다.")
    
    def _create_default_model(self) -> Model:
        """기본 NeRF 모델 생성"""
        # 여기서는 간단한 예시로 구현
        # 실제로는 NerfStudio의 모델 팩토리를 사용해야 함
        class SimpleNeRF(nn.Module):
            def __init__(self):
                super().__init__()
                self.network = nn.Sequential(
                    nn.Linear(63, 256),  # 위치 + 방향 인코딩
                    nn.ReLU(),
                    nn.Linear(256, 256),
                    nn.ReLU(),
                    nn.Linear(256, 256),
                    nn.ReLU(),
                    nn.Linear(256, 4)  # RGB + 밀도
                )
            
            def forward(self, ray_bundle: RayBundle):
                # 간단한 포워드 패스
                positions = ray_bundle.origins.view(-1, 3)
                directions = ray_bundle.directions.view(-1, 3)
                
                # 위치 인코딩 (간단한 버전)
                pos_enc = self._positional_encoding(positions, 10)
                dir_enc = self._positional_encoding(directions, 4)
                
                # 입력 결합
                x = torch.cat([pos_enc, dir_enc], dim=-1)
                
                # 네트워크 통과
                output = self.network(x)
                
                # RGB와 밀도 분리
                rgb = torch.sigmoid(output[..., :3])
                density = torch.relu(output[..., 3:])
                
                return {
                    'rgb': rgb.view(*ray_bundle.origins.shape[:-1], 3),
                    'density': density.view(*ray_bundle.origins.shape[:-1], 1)
                }
            
            def _positional_encoding(self, x: torch.Tensor, L: int) -> torch.Tensor:
                """위치 인코딩"""
                encodings = [x]
                for i in range(L):
                    encodings.append(torch.sin(2**i * x))
                    encodings.append(torch.cos(2**i * x))
                return torch.cat(encodings, dim=-1)
        
        return SimpleNeRF()
    
    def set_dataset(self, dataset: InputDataset):
        """
        데이터셋 설정
        
        Args:
            dataset: 입력 데이터셋
        """
        with self.lock:
            self.dataset = dataset
            self.dataloader = DataLoader(
                dataset,
                batch_size=1,  # 온라인 학습에서는 배치 크기 1
                shuffle=False,
                num_workers=0
            )
            rospy.loginfo("데이터셋이 설정되었습니다.")
    
    def start_training(self):
        """훈련 시작"""
        with self.lock:
            if not self.is_training:
                self.is_training = True
                self.training_thread = threading.Thread(target=self._training_loop)
                self.training_thread.daemon = True
                self.training_thread.start()
                rospy.loginfo("온라인 훈련이 시작되었습니다.")
    
    def stop_training(self):
        """훈련 중지"""
        with self.lock:
            self.is_training = False
            rospy.loginfo("온라인 훈련이 중지되었습니다.")
    
    def _training_loop(self):
        """훈련 루프"""
        while self.is_training and not rospy.is_shutdown():
            try:
                if self.dataset is not None and len(self.dataset) > 0:
                    # 훈련 스텝 실행
                    loss = self._training_step()
                    
                    # 로깅
                    if self.current_iteration % self.config.log_interval == 0:
                        rospy.loginfo(f"Iteration {self.current_iteration}: Loss = {loss:.6f}")
                    
                    # 평가
                    if self.current_iteration % self.config.eval_interval == 0:
                        self._evaluate()
                    
                    # 모델 저장
                    if self.current_iteration % self.config.save_interval == 0:
                        self._save_checkpoint()
                    
                    self.current_iteration += 1
                
                # 짧은 대기
                time.sleep(0.01)
                
            except Exception as e:
                rospy.logerr(f"훈련 루프 오류: {e}")
                time.sleep(1.0)
    
    def _training_step(self) -> float:
        """
        단일 훈련 스텝
        
        Returns:
            훈련 손실
        """
        self.model.train()
        self.optimizer.zero_grad()
        
        # 최신 데이터 가져오기
        if len(self.dataset) == 0:
            return 0.0
        
        # 마지막 이미지 사용
        image_idx = len(self.dataset) - 1
        target_image = self.dataset.get_image(image_idx)
        ray_bundle = self.dataset.get_ray_bundle(image_idx)
        
        # GPU로 이동
        target_image = target_image.to(self.device)
        ray_bundle = ray_bundle.to(self.device)
        
        # 모델 포워드 패스
        outputs = self.model(ray_bundle)
        predicted_rgb = outputs['rgb']
        
        # 손실 계산
        loss = self.criterion(predicted_rgb, target_image)
        
        # 역전파
        loss.backward()
        self.optimizer.step()
        
        # 손실 기록
        self.training_losses.append(loss.item())
        
        return loss.item()
    
    def _evaluate(self):
        """모델 평가"""
        self.model.eval()
        
        with torch.no_grad():
            if len(self.dataset) > 0:
                # 최신 이미지로 평가
                image_idx = len(self.dataset) - 1
                target_image = self.dataset.get_image(image_idx)
                ray_bundle = self.dataset.get_ray_bundle(image_idx)
                
                # GPU로 이동
                target_image = target_image.to(self.device)
                ray_bundle = ray_bundle.to(self.device)
                
                # 모델 예측
                outputs = self.model(ray_bundle)
                predicted_rgb = outputs['rgb']
                
                # 메트릭 계산
                mse_loss = self.criterion(predicted_rgb, target_image)
                psnr = -10 * torch.log10(mse_loss)
                
                # 메트릭 저장
                self.eval_metrics[f"iter_{self.current_iteration}"] = {
                    'mse': mse_loss.item(),
                    'psnr': psnr.item()
                }
                
                rospy.loginfo(f"평가 - MSE: {mse_loss.item():.6f}, PSNR: {psnr.item():.2f}")
    
    def _save_checkpoint(self):
        """체크포인트 저장"""
        try:
            checkpoint = {
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'iteration': self.current_iteration,
                'config': self.config,
                'training_losses': self.training_losses,
                'eval_metrics': self.eval_metrics
            }
            
            # 체크포인트 파일명
            checkpoint_path = f"/tmp/nerf_checkpoint_{self.current_iteration}.pth"
            torch.save(checkpoint, checkpoint_path)
            
            rospy.loginfo(f"체크포인트가 저장되었습니다: {checkpoint_path}")
            
        except Exception as e:
            rospy.logerr(f"체크포인트 저장 실패: {e}")
    
    def load_checkpoint(self, checkpoint_path: str):
        """
        체크포인트 로드
        
        Args:
            checkpoint_path: 체크포인트 파일 경로
        """
        try:
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.current_iteration = checkpoint['iteration']
            self.training_losses = checkpoint['training_losses']
            self.eval_metrics = checkpoint['eval_metrics']
            
            rospy.loginfo(f"체크포인트가 로드되었습니다: {checkpoint_path}")
            
        except Exception as e:
            rospy.logerr(f"체크포인트 로드 실패: {e}")
    
    def render_image(self, camera_pose: torch.Tensor, image_size: Tuple[int, int] = (640, 480)) -> np.ndarray:
        """
        이미지 렌더링
        
        Args:
            camera_pose: 카메라 포즈 (4x4)
            image_size: 이미지 크기 (width, height)
            
        Returns:
            렌더링된 이미지
        """
        self.model.eval()
        
        with torch.no_grad():
            # 카메라 생성
            camera = self._create_camera_from_pose(camera_pose, image_size)
            ray_bundle = camera.generate_rays(camera_indices=0)
            ray_bundle = ray_bundle.to(self.device)
            
            # 렌더링
            outputs = self.model(ray_bundle)
            rendered_image = outputs['rgb']
            
            # numpy로 변환
            rendered_image = rendered_image.cpu().numpy()
            
            return rendered_image
    
    def _create_camera_from_pose(self, camera_pose: torch.Tensor, image_size: Tuple[int, int]):
        """포즈로부터 카메라 생성"""
        # NerfStudio 카메라 생성
        from nerfstudio.cameras.cameras import Cameras, CameraType
        
        return Cameras(
            camera_to_worlds=camera_pose.unsqueeze(0),
            fx=self.config.fx if hasattr(self.config, 'fx') else 615.0,
            fy=self.config.fy if hasattr(self.config, 'fy') else 615.0,
            cx=image_size[0] / 2,
            cy=image_size[1] / 2,
            camera_type=CameraType.PERSPECTIVE,
            image_height=image_size[1],
            image_width=image_size[0],
        )
    
    def get_training_stats(self) -> Dict:
        """훈련 통계 반환"""
        with self.lock:
            return {
                'current_iteration': self.current_iteration,
                'is_training': self.is_training,
                'latest_loss': self.training_losses[-1] if self.training_losses else 0.0,
                'avg_loss': np.mean(self.training_losses[-100:]) if self.training_losses else 0.0,
                'latest_psnr': self.eval_metrics.get(f"iter_{self.current_iteration}", {}).get('psnr', 0.0),
                'training_time': time.time() - self.last_training_time
            }
    
    def update_learning_rate(self, new_lr: float):
        """
        학습률 업데이트
        
        Args:
            new_lr: 새로운 학습률
        """
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = new_lr
        rospy.loginfo(f"학습률이 업데이트되었습니다: {new_lr}")
    
    def cleanup(self):
        """정리 작업"""
        self.stop_training()
        if hasattr(self, 'training_thread'):
            self.training_thread.join(timeout=1.0)
        rospy.loginfo("온라인 훈련기가 정리되었습니다.")

class OnlineTrainingManager:
    """
    온라인 훈련 관리자
    """
    
    def __init__(self, config: OnlineTrainingConfig):
        """
        훈련 관리자 초기화
        
        Args:
            config: 훈련 설정
        """
        self.config = config
        self.trainer = OnlineTrainer(config)
        self.is_initialized = False
        
        rospy.loginfo("온라인 훈련 관리자가 초기화되었습니다.")
    
    def initialize_with_dataset(self, dataset: InputDataset):
        """
        데이터셋으로 초기화
        
        Args:
            dataset: 입력 데이터셋
        """
        self.trainer.set_dataset(dataset)
        self.is_initialized = True
        rospy.loginfo("훈련 관리자가 데이터셋으로 초기화되었습니다.")
    
    def start_online_training(self):
        """온라인 훈련 시작"""
        if self.is_initialized:
            self.trainer.start_training()
        else:
            rospy.logwarn("데이터셋이 설정되지 않았습니다.")
    
    def stop_online_training(self):
        """온라인 훈련 중지"""
        self.trainer.stop_training()
    
    def get_trainer(self) -> OnlineTrainer:
        """훈련기 반환"""
        return self.trainer
    
    def get_training_stats(self) -> Dict:
        """훈련 통계 반환"""
        return self.trainer.get_training_stats()
    
    def render_from_pose(self, camera_pose: torch.Tensor, image_size: Tuple[int, int] = (640, 480)) -> np.ndarray:
        """
        포즈로부터 이미지 렌더링
        
        Args:
            camera_pose: 카메라 포즈
            image_size: 이미지 크기
            
        Returns:
            렌더링된 이미지
        """
        return self.trainer.render_image(camera_pose, image_size)
    
    def cleanup(self):
        """정리 작업"""
        self.trainer.cleanup()
