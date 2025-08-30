# Radiance Fields for Robotic Teleoperation

ETH Zurich의 "Radiance Fields for Robotic Teleoperation" 논문을 바탕으로 한 실시간 로봇 원격 조작 시스템입니다.

## 🎯 프로젝트 개요

이 프로젝트는 Neural Radiance Fields(NeRF)와 3D Gaussian Splatting(3DGS)을 활용하여 고품질의 실시간 로봇 원격 조작 시스템을 구현합니다.

### 핵심 기능
- **온라인 Radiance Field 훈련**: 다중 카메라 실시간 데이터로 학습
- **다양한 방법 지원**: NeRF, 3DGS 등 여러 radiance field 방법 통합
- **VR 시각화 시스템**: Meta Quest 3 기반 몰입형 인터페이스
- **완전한 ROS 통합**: 기존 텔레오퍼레이션 시스템과 원활한 통합

### 목표 성능 지표
- **품질**: NeRF PSNR > 20, 3DGS PSNR > 25
- **속도**: 3DGS 렌더링 > 100 FPS, 훈련 속도 ~35ms/iteration
- **사용성**: VR 인터페이스 선호도 > 70%
- **안정성**: 1시간 연속 운영 가능

## 🛠️ 시스템 요구사항

### 하드웨어
- **개발 워크스테이션**: NVIDIA RTX 4080/4090 (12GB+ VRAM)
- **로봇 플랫폼**: Franka Panda 또는 Anymal (선택)
- **센서**: Intel RealSense 435i/L515
- **VR 헤드셋**: Meta Quest 3
- **네트워크**: 기가비트 이더넷

### 소프트웨어
- **OS**: Ubuntu 20.04 LTS
- **ROS**: Noetic
- **Python**: 3.8+
- **CUDA**: 11.8+
- **Unity**: 2022.3.12f1
- **NerfStudio**: 최신 버전

## 📁 프로젝트 구조

```
radiance_teleoperation_project/
├── src/                    # 소스 코드
│   ├── radiance_camera/    # 카메라 관련 패키지
│   ├── radiance_nerf/      # NeRF 관련 패키지
│   ├── radiance_viz/       # 시각화 관련 패키지
│   └── radiance_robot/     # 로봇 통합 패키지
├── config/                 # 설정 파일
├── launch/                 # ROS Launch 파일
├── scripts/                # 유틸리티 스크립트
├── test/                   # 테스트 코드
├── docs/                   # 문서
├── unity_vr/               # Unity VR 프로젝트
└── docker/                 # Docker 설정
```

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Phase 1: 환경 설정 및 기초 구조 구축
./scripts/setup_environment.sh
```

### 2. 데이터 수집
```bash
# Phase 2: 데이터 수집 및 처리 파이프라인
roslaunch radiance_camera multi_camera.launch
```

### 3. NeRF 훈련
```bash
# Phase 3: Radiance Field 통합
roslaunch radiance_nerf online_training.launch
```

### 4. VR 시각화
```bash
# Phase 4: 시각화 시스템
# Unity VR 앱 실행
```

## 📚 문서

- [설치 가이드](docs/INSTALLATION.md)
- [사용자 매뉴얼](docs/USER_MANUAL.md)
- [API 문서](docs/API_REFERENCE.md)
- [문제 해결 가이드](docs/TROUBLESHOOTING.md)

## 🤝 기여하기

이 프로젝트에 기여하고 싶으시다면 [기여 가이드](docs/CONTRIBUTING.md)를 참고해주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🙏 인용

이 프로젝트를 사용하시는 경우 다음 논문을 인용해주세요:

```bibtex
@article{wildersmith2024rfteleoperation,
  title={Radiance Fields for Robotic Teleoperation},
  author={Maximum Wilder-Smith and Vaishakh Patil and Marco Hutter},
  journal={arXiv preprint arXiv:2401.xxxxx},
  year={2024}
}
```
