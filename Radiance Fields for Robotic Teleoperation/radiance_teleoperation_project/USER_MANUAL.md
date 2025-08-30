# Radiance Fields for Robotic Teleoperation - 사용자 매뉴얼

## 🎯 개요

이 매뉴얼은 Radiance Fields for Robotic Teleoperation 시스템의 사용법을 설명합니다.

## 🚀 시스템 시작

### 1. 환경 준비

```bash
# ROS 환경 활성화
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash

# NerfStudio 환경 활성화
conda activate nerfstudio
```

### 2. 시스템 시작

#### 2.1 ROS 마스터 시작
```bash
# 터미널 1
roscore
```

#### 2.2 멀티 카메라 노드 시작
```bash
# 터미널 2
roslaunch radiance_camera multi_camera.launch
```

#### 2.3 NeRF 훈련 노드 시작
```bash
# 터미널 3
roslaunch radiance_nerf online_training.launch
```

#### 2.4 VR 시각화 시작
```bash
# 터미널 4
roslaunch radiance_viz vr_visualization.launch
```

### 3. Unity VR 앱 실행

1. Meta Quest 3 연결
2. Unity VR 앱 빌드 및 설치
3. 앱 실행

## 📊 시스템 모니터링

### 1. ROS 토픽 모니터링

```bash
# 모든 토픽 확인
rostopic list

# 특정 토픽 모니터링
rostopic echo /camera_stats
rostopic echo /nerf/training_stats
rostopic echo /nerf/rendered_image
```

### 2. 시스템 상태 확인

```bash
# 노드 상태 확인
rosnode list
rosnode info /multi_camera_node

# 서비스 확인
rosservice list
```

### 3. RViz 시각화

```bash
# RViz 실행
rviz

# 설정 파일 로드
# File -> Open Config -> radiance_viz/config/radiance_viz.rviz
```

## 🎮 VR 인터페이스 사용법

### 1. 기본 조작

#### 헤드셋 조작
- **이동**: 헤드셋을 움직여 시점 변경
- **회전**: 헤드셋을 회전하여 방향 변경
- **줌**: 컨트롤러 트리거로 줌 인/아웃

#### 컨트롤러 조작
- **포인팅**: 검지로 포인팅하여 객체 선택
- **잡기**: 모든 손가락을 접어 객체 잡기
- **메뉴**: 왼손 손바닥을 위로 향해 메뉴 열기

### 2. 팜 메뉴 사용법

#### 메뉴 항목
- **카메라 전환**: 다른 카메라 뷰로 전환
- **렌더링 품질**: NeRF 렌더링 품질 조정
- **로봇 제어**: 로봇 제어 모드 활성화
- **설정**: 시스템 설정 변경

#### 메뉴 조작
1. 왼손 손바닥을 위로 향기기
2. 메뉴가 나타나면 원하는 항목 터치
3. 메뉴 닫기: 손바닥을 아래로 향기기

### 3. 로봇 제어

#### 이동 제어
- **전진/후진**: 컨트롤러 스틱 위/아래
- **좌우 이동**: 컨트롤러 스틱 좌/우
- **회전**: 컨트롤러 스틱 좌우 회전

#### 매니퓰레이션
- **팔 제어**: 컨트롤러로 로봇 팔 조작
- **그리퍼 제어**: 트리거로 그리퍼 열기/닫기
- **포즈 저장**: 특정 포즈 저장 및 복원

## 🔧 설정 및 조정

### 1. 카메라 설정

```yaml
# config/camera_config.yaml 편집
cameras:
  - name: "front_camera"
    type: "realsense"
    intrinsics:
      width: 640
      height: 480
      fx: 615.0
      fy: 615.0
      cx: 320.0
      cy: 240.0
```

### 2. NeRF 훈련 설정

```yaml
# config/nerf_config.yaml 편집
training:
  learning_rate: 1e-3
  batch_size: 4096
  max_iterations: 1000
  save_interval: 100
```

### 3. VR 설정

```yaml
# config/vr_config.yaml 편집
vr:
  target_frame_rate: 72
  enable_foveated_rendering: true
  hand_tracking: true
  haptic_feedback: true
```

## 📈 성능 최적화

### 1. GPU 메모리 최적화

```bash
# GPU 메모리 모니터링
watch -n 1 nvidia-smi

# 배치 크기 조정
# config/nerf_config.yaml에서 batch_size 줄이기
```

### 2. 네트워크 최적화

```bash
# 네트워크 대역폭 확인
iftop

# ROS 네트워크 설정
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=your_ip_address
```

### 3. 렌더링 품질 조정

- **고품질**: PSNR > 25, FPS < 30
- **중간 품질**: PSNR > 20, FPS 30-60
- **저품질**: PSNR > 15, FPS > 60

## 🐛 문제 해결

### 1. 일반적인 문제

#### 카메라 연결 실패
```bash
# RealSense 카메라 확인
realsense-viewer

# USB 권한 설정
sudo usermod -a -G video $USER
```

#### NeRF 훈련 실패
```bash
# GPU 메모리 확인
nvidia-smi

# 배치 크기 줄이기
# config/nerf_config.yaml 수정
```

#### VR 연결 실패
```bash
# TCP 연결 확인
netstat -an | grep 10000

# 방화벽 설정
sudo ufw allow 10000
```

### 2. 로그 확인

```bash
# ROS 로그 확인
rqt_console

# 시스템 로그 확인
journalctl -f

# GPU 로그 확인
nvidia-smi -l 1
```

### 3. 성능 문제

#### 낮은 FPS
1. 렌더링 품질 낮추기
2. GPU 메모리 확인
3. 네트워크 대역폭 확인

#### 높은 지연시간
1. 네트워크 연결 확인
2. ROS 토픽 주기 조정
3. 이미지 압축 설정

## 📊 데이터 수집 및 분석

### 1. 데이터 수집

```bash
# 데이터 수집 시작
rosbag record -a -o /tmp/radiance_data

# 특정 토픽만 수집
rosbag record /camera_stats /nerf/training_stats -o /tmp/stats_data
```

### 2. 데이터 분석

```bash
# ROSbag 재생
rosbag play /tmp/radiance_data.bag

# 데이터 시각화
rqt_plot /camera_stats
rqt_plot /nerf/training_stats
```

### 3. 성능 메트릭

#### 품질 메트릭
- **PSNR**: Peak Signal-to-Noise Ratio
- **SSIM**: Structural Similarity Index
- **LPIPS**: Learned Perceptual Image Patch Similarity

#### 성능 메트릭
- **FPS**: Frames Per Second
- **지연시간**: End-to-End Latency
- **메모리 사용량**: GPU/CPU Memory Usage

## 🔄 시스템 업데이트

### 1. 소프트웨어 업데이트

```bash
# ROS 패키지 업데이트
cd ~/catkin_ws
git pull origin main
catkin_make

# NerfStudio 업데이트
conda activate nerfstudio
pip install --upgrade nerfstudio
```

### 2. 설정 백업

```bash
# 설정 파일 백업
cp -r config/ ~/backup/config_$(date +%Y%m%d)

# 모델 체크포인트 백업
cp -r /tmp/nerf_checkpoint_* ~/backup/models/
```

## 📞 지원 및 문의

### 1. 문서
- [API 문서](docs/API_REFERENCE.md)
- [문제 해결 가이드](docs/TROUBLESHOOTING.md)
- [개발자 가이드](docs/DEVELOPER_GUIDE.md)

### 2. 커뮤니티
- [GitHub Issues](https://github.com/your-repo/radiance-teleoperation/issues)
- [Discord 채널](https://discord.gg/your-channel)
- [Wiki](https://github.com/your-repo/radiance-teleoperation/wiki)

### 3. 연락처
- **이메일**: support@your-org.com
- **GitHub**: [@your-username](https://github.com/your-username)

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
