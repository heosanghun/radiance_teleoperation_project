#!/usr/bin/env python3

"""
Radiance Fields for Robotic Teleoperation - ROS 2 데이터셋
Phase 3: Radiance Field 통합

이 모듈은 ROS 2에서 실시간으로 수집된 카메라 데이터를 NerfStudio의 InputDataset 형식으로 변환합니다.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple
import rclpy
from rclpy.node import Node
from dataclasses import dataclass
import time
from std_msgs.msg import String

# NerfStudio imports
try:
    from nerfstudio.data.dataparsers.base_dataparser import DataparserOutputs
    from nerfstudio.data.datasets.base_dataset import InputDataset
    from nerfstudio.cameras.cameras import Cameras, CameraType
    from nerfstudio.cameras.rays import RayBundle
    NERFSTUDIO_AVAILABLE = True
except ImportError:
    NERFSTUDIO_AVAILABLE = False
    print("NerfStudio가 설치되지 않았습니다.")

@dataclass
class ROSDatasetConfig:
    """ROS 2 데이터셋 설정"""
    image_height: int = 480
    image_width: int = 640
    num_images: int = 100
    camera_to_worlds: Optional[torch.Tensor] = None
    fx: Optional[float] = None
    fy: Optional[float] = None
    cx: Optional[float] = None
    cy: Optional[float] = None
    distortion_params: Optional[torch.Tensor] = None
    camera_type: CameraType = CameraType.PERSPECTIVE

class ROSDataset(InputDataset):
    """
    ROS 2 실시간 데이터를 NerfStudio 형식으로 변환하는 데이터셋
    """
    
    def __init__(self, config: ROSDatasetConfig, sync_data_buffer=None):
        """
        ROS 2 데이터셋 초기화
        
        Args:
            config: 데이터셋 설정
            sync_data_buffer: 동기화된 데이터 버퍼
        """
        if not NERFSTUDIO_AVAILABLE:
            raise ImportError("NerfStudio가 필요합니다.")
        
        self.config = config
        self.sync_data_buffer = sync_data_buffer
        
        # 데이터 저장소
        self.images = []
        self.cameras = None
        self.metadata = {}
        
        # 카메라 설정
        self._setup_cameras()
        
        # 데이터셋 초기화
        super().__init__(dataparser_outputs=self._create_dataparser_outputs())
        
        print("ROS 2 데이터셋이 초기화되었습니다.")
    
    def _setup_cameras(self):
        """카메라 설정"""
        # 기본 카메라 매트릭스
        if self.config.fx is None:
            self.config.fx = 615.0
        if self.config.fy is None:
            self.config.fy = 615.0
        if self.config.cx is None:
            self.config.cx = self.config.image_width / 2
        if self.config.cy is None:
            self.config.cy = self.config.image_height / 2
        
        # 카메라 매트릭스
        camera_to_worlds = self.config.camera_to_worlds
        if camera_to_worlds is None:
            # 기본 카메라 포즈 (정면 카메라)
            camera_to_worlds = torch.eye(4, dtype=torch.float32).unsqueeze(0)
        
        # 카메라 객체 생성
        self.cameras = Cameras(
            camera_to_worlds=camera_to_worlds,
            fx=self.config.fx,
            fy=self.config.fy,
            cx=self.config.cx,
            cy=self.config.cy,
            distortion_params=self.config.distortion_params,
            camera_type=self.config.camera_type,
            image_height=self.config.image_height,
            image_width=self.config.image_width,
        )
    
    def _create_dataparser_outputs(self) -> DataparserOutputs:
        """DataparserOutputs 생성"""
        return DataparserOutputs(
            image_filenames=[],
            cameras=self.cameras,
            alpha_color=None,
            scene_box=None,
            mask_filenames=None,
            metadata={},
            dataparser_scale=1.0,
            dataparser_transform=torch.eye(4, dtype=torch.float32),
        )
    
    def add_sync_data(self, sync_data: Dict):
        """
        동기화된 데이터 추가
        
        Args:
            sync_data: 동기화된 카메라 데이터
        """
        try:
            # 이미지 데이터 추출
            images = []
            camera_to_worlds = []
            
            for camera_name, camera_data in sync_data['cameras'].items():
                # 이미지 추가
                if 'image' in camera_data:
                    image = camera_data['image']
                    if isinstance(image, np.ndarray):
                        image = torch.from_numpy(image).float()
                    images.append(image)
                
                # 카메라 포즈 추가
                if 'camera_matrix' in camera_data and camera_data['camera_matrix'] is not None:
                    # 카메라 매트릭스에서 포즈 추출 (간단한 변환)
                    pose = torch.eye(4, dtype=torch.float32)
                    camera_to_worlds.append(pose)
                else:
                    # 기본 포즈 사용
                    camera_to_worlds.append(torch.eye(4, dtype=torch.float32))
            
            if images:
                # 이미지 스택
                image_stack = torch.stack(images, dim=0)
                self.images.append(image_stack)
                
                # 카메라 포즈 업데이트
                pose_stack = torch.stack(camera_to_worlds, dim=0)
                self.cameras.camera_to_worlds = torch.cat([
                    self.cameras.camera_to_worlds, pose_stack
                ], dim=0)
                
                # 메타데이터 업데이트
                self.metadata[f"timestamp_{len(self.images)}"] = sync_data.get('timestamp', time.time())
                
                print(f"동기화된 데이터가 추가되었습니다. 총 {len(self.images)}개 프레임")
            
        except Exception as e:
            print(f"동기화된 데이터 추가 실패: {e}")
    
    def get_numpy_image(self, image_idx: int) -> np.ndarray:
        """
        numpy 이미지 반환
        
        Args:
            image_idx: 이미지 인덱스
            
        Returns:
            numpy 이미지 배열
        """
        if 0 <= image_idx < len(self.images):
            # 마지막 이미지 스택에서 해당 인덱스 반환
            image_stack = self.images[-1]
            if image_idx < image_stack.shape[0]:
                return image_stack[image_idx].numpy()
        
        # 기본값 반환
        return np.zeros((self.config.image_height, self.config.image_width, 3), dtype=np.float32)
    
    def get_image(self, image_idx: int) -> torch.Tensor:
        """
        torch 이미지 반환
        
        Args:
            image_idx: 이미지 인덱스
            
        Returns:
            torch 이미지 텐서
        """
        if 0 <= image_idx < len(self.images):
            image_stack = self.images[-1]
            if image_idx < image_stack.shape[0]:
                return image_stack[image_idx]
        
        # 기본값 반환
        return torch.zeros((self.config.image_height, self.config.image_width, 3), dtype=torch.float32)
    
    def get_camera(self, image_idx: int) -> Cameras:
        """
        카메라 반환
        
        Args:
            image_idx: 이미지 인덱스
            
        Returns:
            카메라 객체
        """
        if image_idx < self.cameras.camera_to_worlds.shape[0]:
            return Cameras(
                camera_to_worlds=self.cameras.camera_to_worlds[image_idx:image_idx+1],
                fx=self.cameras.fx,
                fy=self.cameras.fy,
                cx=self.cameras.cx,
                cy=self.cameras.cy,
                distortion_params=self.cameras.distortion_params,
                camera_type=self.cameras.camera_type,
                image_height=self.cameras.image_height,
                image_width=self.cameras.image_width,
            )
        
        return self.cameras
    
    def get_ray_bundle(self, image_idx: int) -> RayBundle:
        """
        레이 번들 반환
        
        Args:
            image_idx: 이미지 인덱스
            
        Returns:
            레이 번들
        """
        camera = self.get_camera(image_idx)
        return camera.generate_rays(camera_indices=0)
    
    def __len__(self) -> int:
        """데이터셋 길이"""
        return len(self.images) if self.images else 0
    
    def get_metadata(self, image_idx: int) -> Dict:
        """메타데이터 반환"""
        return self.metadata.get(f"timestamp_{image_idx}", {})
    
    def clear_old_data(self, max_frames: int = 100):
        """
        오래된 데이터 정리
        
        Args:
            max_frames: 유지할 최대 프레임 수
        """
        if len(self.images) > max_frames:
            # 오래된 이미지 제거
            self.images = self.images[-max_frames:]
            
            # 카메라 포즈도 함께 제거
            if self.cameras.camera_to_worlds.shape[0] > max_frames:
                self.cameras.camera_to_worlds = self.cameras.camera_to_worlds[-max_frames:]
            
            # 메타데이터 정리
            keys_to_remove = []
            for key in self.metadata.keys():
                if key.startswith("timestamp_"):
                    frame_num = int(key.split("_")[1])
                    if frame_num < len(self.images) - max_frames:
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.metadata[key]
            
            print(f"오래된 데이터가 정리되었습니다. 현재 {len(self.images)}개 프레임 유지")

class ROSDataManager(Node):
    """
    ROS 2 데이터 관리자
    """
    
    def __init__(self, config: ROSDatasetConfig):
        """
        데이터 관리자 초기화
        
        Args:
            config: 데이터셋 설정
        """
        super().__init__('ros_data_manager')
        self.config = config
        self.dataset = ROSDataset(config)
        self.is_running = False
        
        # 데이터 상태 발행자
        self.status_publisher = self.create_publisher(
            String, 'data_manager_status', 10
        )
        self.status_timer = self.create_timer(5.0, self._publish_status)
        
        print("ROS 2 데이터 관리자가 초기화되었습니다.")
    
    def start(self):
        """데이터 수집 시작"""
        self.is_running = True
        print("ROS 2 데이터 수집이 시작되었습니다.")
    
    def stop(self):
        """데이터 수집 중지"""
        self.is_running = False
        print("ROS 2 데이터 수집이 중지되었습니다.")
    
    def add_sync_data(self, sync_data: Dict):
        """
        동기화된 데이터 추가
        
        Args:
            sync_data: 동기화된 카메라 데이터
        """
        if self.is_running:
            self.dataset.add_sync_data(sync_data)
    
    def get_dataset(self) -> ROSDataset:
        """데이터셋 반환"""
        return self.dataset
    
    def get_latest_data(self) -> Optional[Dict]:
        """최신 데이터 반환"""
        if len(self.dataset.images) > 0:
            return {
                'images': self.dataset.images[-1],
                'cameras': self.dataset.cameras,
                'metadata': self.dataset.metadata
            }
        return None
    
    def cleanup(self, max_frames: int = 100):
        """
        데이터 정리
        
        Args:
            max_frames: 유지할 최대 프레임 수
        """
        self.dataset.clear_old_data(max_frames)
    
    def _publish_status(self):
        """데이터 관리자 상태 발행"""
        try:
            status_msg = f"Running: {self.is_running}, Frames: {len(self.dataset.images)}"
            msg = String()
            msg.data = status_msg
            self.status_publisher.publish(msg)
        except Exception as e:
            self.get_logger().error(f"상태 발행 실패: {e}")
