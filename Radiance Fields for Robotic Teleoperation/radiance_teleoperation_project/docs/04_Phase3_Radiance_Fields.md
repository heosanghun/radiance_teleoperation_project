# Phase 3: Radiance Field 통합 (4-5주)

## 🎯 목표
NerfStudio-ROS 브릿지 및 Radiance Field 모델 구현

## 📋 주요 작업

### 3.1 NerfStudio-ROS 브릿지 (2주)

#### 3.1.1 커스텀 Dataset 클래스
```python
# radiance_nerf/src/ros_dataset.py
class ROSDataset(InputDataset):
    def __init__(self, config: ROSDatasetConfig):
        self.config = config
        self.ros_buffer = DataBuffer()
        self.image_filenames = []
        self.cameras = Cameras()
        
    def get_numpy_image(self, image_idx: int) -> np.ndarray:
        # ROS 이미지 데이터를 numpy 배열로 변환
        pass
```

#### 3.1.2 ROS DataLoader
```python
# radiance_nerf/src/ros_dataloader.py  
class ROSDataLoader:
    def __init__(self, dataset, config):
        self.dataset = dataset
        self.batch_size = config.batch_size
        self.num_workers = config.num_workers
        
    def __iter__(self):
        # 실시간 ROS 데이터 배치 생성
        pass
```

#### 3.1.3 ActionServer 구현
```python
# radiance_nerf/src/render_server.py
class RenderActionServer:
    def __init__(self):
        self.server = actionlib.SimpleActionServer(
            'render_radiance_field', 
            RenderAction, 
            self.execute_render
        )
        
    def execute_render(self, goal):
        # 렌더링 요청 처리
        pass
```

### 3.2 NeRF/3DGS 모델 최적화 (2주)

#### 3.2.1 실시간 NeRF 구현
- 경량화된 네트워크 아키텍처
- 적응적 샘플링 전략
- 점진적 해상도 훈련

#### 3.2.2 3D Gaussian Splatting 최적화
- GPU 메모리 효율적 스플랫 관리
- 실시간 가우시안 최적화
- 고속 렌더링 파이프라인 (151 FPS 목표)

### 3.3 온라인 학습 시스템 (1주)

#### 3.3.1 실시간 훈련 파이프라인
```python
# radiance_nerf/src/online_trainer.py
class OnlineTrainer:
    def __init__(self, model, config):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters())
        self.loss_fn = MSELoss()
        
    def train_step(self, batch):
        # 온라인 훈련 스텝
        pass
```

## ✅ 검증 기준
- [ ] ROS-NerfStudio 데이터 교환 정상 작동
- [ ] 실시간 훈련 속도 ~35ms/iteration
- [ ] 3DGS 렌더링 속도 > 100 FPS
- [ ] NeRF PSNR > 20, 3DGS PSNR > 25
