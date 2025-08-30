# 🤝 기여 가이드

Radiance Fields for Robotic Teleoperation 프로젝트에 기여해주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법을 안내합니다.

## 📋 목차

- [기여 방법](#기여-방법)
- [개발 환경 설정](#개발-환경-설정)
- [코딩 스타일](#코딩-스타일)
- [테스트 작성](#테스트-작성)
- [PR 제출](#pr-제출)
- [이슈 리포트](#이슈-리포트)

## 🚀 기여 방법

### 1. 포크 및 클론
```bash
# 저장소 포크 후 클론
git clone https://github.com/yourusername/radiance-fields-robotic-teleoperation.git
cd radiance-fields-robotic-teleoperation
```

### 2. 개발 브랜치 생성
```bash
# 메인 브랜치에서 최신 상태로 업데이트
git checkout main
git pull origin main

# 새로운 기능 브랜치 생성
git checkout -b feature/your-feature-name
# 또는 버그 수정 브랜치
git checkout -b fix/your-bug-description
```

### 3. 변경사항 커밋
```bash
# 변경사항 스테이징
git add .

# 의미있는 커밋 메시지 작성
git commit -m "feat: add new camera calibration feature"
git commit -m "fix: resolve memory leak in NeRF training"
git commit -m "docs: update installation guide"
```

### 4. PR 생성
```bash
# 브랜치 푸시
git push origin feature/your-feature-name

# GitHub에서 Pull Request 생성
```

## 🛠️ 개발 환경 설정

### 필수 요구사항
- Ubuntu 20.04 LTS
- Python 3.8+
- ROS Noetic
- CUDA 11.8+
- Unity 2022.3.12f1

### 환경 설정
```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/radiance-fields-robotic-teleoperation.git
cd radiance-fields-robotic-teleoperation/radiance_teleoperation_project

# 2. 자동 설치 스크립트 실행
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh

# 3. Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 4. 의존성 설치
pip install -r requirements.txt

# 5. ROS 워크스페이스 빌드
cd ~/catkin_ws
catkin build
```

### 개발 도구 설정
```bash
# Pre-commit 훅 설치
pip install pre-commit
pre-commit install

# 코드 포맷터 설정
pip install black flake8 mypy
```

## 📝 코딩 스타일

### Python
- **PEP 8** 준수
- **Black** 포맷터 사용
- **Flake8** 린터 사용
- **Type hints** 사용 권장

```python
# 좋은 예시
from typing import List, Optional, Tuple
import numpy as np

def process_camera_data(
    images: List[np.ndarray], 
    camera_poses: Optional[List[np.ndarray]] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    카메라 데이터를 처리합니다.
    
    Args:
        images: 처리할 이미지 리스트
        camera_poses: 카메라 포즈 리스트 (선택사항)
        
    Returns:
        처리된 이미지와 포즈의 튜플
    """
    # 구현...
    pass
```

### C++
- **Google C++ Style Guide** 준수
- **Clang-format** 사용
- **Clang-tidy** 린터 사용

```cpp
// 좋은 예시
#include <memory>
#include <vector>

namespace radiance_teleop {

class CameraManager {
 public:
  explicit CameraManager(const std::string& config_path);
  
  bool Initialize();
  std::vector<cv::Mat> GetImages() const;
  
 private:
  std::string config_path_;
  std::unique_ptr<CameraNode> camera_node_;
};

}  // namespace radiance_teleop
```

### C# (Unity)
- **Microsoft C# Coding Conventions** 준수
- **Unity C# Style Guide** 참고
- **XML 문서 주석** 사용

```csharp
// 좋은 예시
using UnityEngine;
using System.Collections.Generic;

namespace RadianceTeleoperation
{
    /// <summary>
    /// VR 환경을 관리하는 클래스입니다.
    /// </summary>
    public class VRManager : MonoBehaviour
    {
        [SerializeField] private Transform headsetTransform;
        [SerializeField] private Transform leftControllerTransform;
        [SerializeField] private Transform rightControllerTransform;
        
        private ROSConnector rosConnector;
        
        /// <summary>
        /// VR 시스템을 초기화합니다.
        /// </summary>
        /// <returns>초기화 성공 여부</returns>
        public bool InitializeVR()
        {
            // 구현...
            return true;
        }
    }
}
```

## 🧪 테스트 작성

### 단위 테스트
각 모듈별로 단위 테스트를 작성해주세요.

```python
# test/test_camera_node.py
import pytest
import numpy as np
from src.radiance_camera.src.multi_camera_node import MultiCameraNode

class TestMultiCameraNode:
    def test_camera_initialization(self):
        """카메라 초기화 테스트"""
        node = MultiCameraNode()
        assert node.is_initialized == False
        
        result = node.initialize()
        assert result == True
        assert node.is_initialized == True
    
    def test_image_processing(self):
        """이미지 처리 테스트"""
        # 테스트 구현...
        pass
```

### 통합 테스트
전체 시스템의 통합 테스트를 작성해주세요.

```python
# test/test_integration.py
import pytest
import rospy
from std_msgs.msg import String

class TestSystemIntegration:
    def test_camera_to_nerf_pipeline(self):
        """카메라에서 NeRF까지의 파이프라인 테스트"""
        # 테스트 구현...
        pass
```

### 성능 테스트
성능 벤치마크 테스트를 작성해주세요.

```python
# test/test_performance.py
import time
import pytest

class TestPerformance:
    def test_nerf_training_speed(self):
        """NeRF 훈련 속도 테스트"""
        start_time = time.time()
        # 훈련 실행...
        end_time = time.time()
        
        training_time = end_time - start_time
        assert training_time < 0.1  # 100ms 이내
```

## 📤 PR 제출

### PR 템플릿
```markdown
## 📝 변경사항 요약
- 변경사항에 대한 간단한 설명

## 🔧 변경된 내용
- [ ] 새로운 기능 추가
- [ ] 버그 수정
- [ ] 문서 업데이트
- [ ] 성능 개선
- [ ] 리팩토링

## 🧪 테스트
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 성능 테스트 통과
- [ ] 수동 테스트 완료

## 📸 스크린샷 (UI 변경시)
- 변경 전/후 스크린샷 첨부

## 📋 체크리스트
- [ ] 코드 스타일 가이드 준수
- [ ] 자체 리뷰 완료
- [ ] 문서 업데이트
- [ ] 변경사항이 기존 기능에 영향 없음
```

### 커밋 메시지 규칙
```
<type>(<scope>): <subject>

<body>

<footer>
```

**타입:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 스타일 변경
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 프로세스 또는 보조 도구 변경

**예시:**
```
feat(camera): add multi-camera synchronization

- Implement timestamp-based synchronization
- Add buffer management for multiple cameras
- Support up to 4 cameras simultaneously

Closes #123
```

## 🐛 이슈 리포트

### 버그 리포트 템플릿
```markdown
## 🐛 버그 설명
버그에 대한 명확하고 간결한 설명

## 🔄 재현 단계
1. '...'로 이동
2. '...' 클릭
3. '...'까지 스크롤
4. 오류 발생

## 📱 예상 동작
예상했던 정상적인 동작

## 📸 스크린샷
가능한 경우 스크린샷 첨부

## 💻 환경 정보
- OS: Ubuntu 20.04
- Python: 3.8.10
- ROS: Noetic
- CUDA: 11.8
- GPU: RTX 4080

## 📋 추가 정보
문제 해결에 도움이 될 수 있는 추가 정보
```

### 기능 요청 템플릿
```markdown
## 💡 기능 요청
원하는 기능에 대한 명확한 설명

## 🎯 문제점
이 기능이 해결할 문제점

## 💭 제안하는 해결책
구체적인 해결 방안

## 🔄 대안
고려한 다른 해결책들

## 📋 추가 정보
기능 구현에 도움이 될 수 있는 추가 정보
```

## 📞 연락처

- **이슈 리포트**: [GitHub Issues](https://github.com/yourusername/radiance-fields-robotic-teleoperation/issues)
- **문의사항**: your.email@example.com
- **토론**: [GitHub Discussions](https://github.com/yourusername/radiance-fields-robotic-teleoperation/discussions)

## 🙏 감사의 말

프로젝트에 기여해주시는 모든 분들께 감사드립니다! 여러분의 기여가 이 프로젝트를 더욱 발전시킵니다.

---

**기여자 명단에 추가되시려면 PR 설명에 "Add me to contributors"라고 언급해주세요!**
