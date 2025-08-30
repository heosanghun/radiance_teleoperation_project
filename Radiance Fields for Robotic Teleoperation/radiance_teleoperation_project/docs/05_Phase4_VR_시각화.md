# Phase 4: 시각화 시스템 구현 (3-4주)

## 🎯 목표
RViz 플러그인 및 VR 시스템 개발

## 📋 주요 작업

### 4.1 RViz 플러그인 개발 (1.5주)

#### 4.1.1 NerfViewController 플러그인
```cpp
// radiance_viz/src/nerf_view_controller.cpp
class NerfViewController : public rviz::ViewController
{
public:
    NerfViewController();
    virtual void onInitialize();
    virtual void handleMouseEvent(rviz::ViewportMouseEvent& event);
    virtual void lookAt(const Ogre::Vector3& point);
    virtual void reset();
    
private:
    ros::ServiceClient render_client_;
    void sendRenderRequest(const geometry_msgs::PoseStamped& pose);
};
```

#### 4.1.2 점진적 해상도 렌더링
- 저해상도 프리뷰 (10% → 50% → 100%)
- 적응적 품질 조정
- 실시간 성능 모니터링

### 4.2 Unity VR 프로젝트 (2주)

#### 4.2.1 기본 VR 설정
```csharp
// Unity Scripts/VRManager.cs
public class VRManager : MonoBehaviour
{
    public GameObject headset;
    public GameObject leftHand;
    public GameObject rightHand;
    
    void Start()
    {
        InitializeVR();
        ConnectToROS();
    }
    
    void InitializeVR()
    {
        // OpenXR 설정
        // Hand tracking 활성화
    }
}
```

#### 4.2.2 핵심 VR 컴포넌트
1. **Hand Tracking System**
   - 제스처 인식
   - 가상 객체 조작
   - UI 상호작용

2. **Haptic Feedback**
   - 촉각 피드백 제공
   - 충돌 감지
   - 힘 피드백

3. **Palm Menu**
   - 직관적 메뉴 시스템
   - 설정 조정
   - 상태 모니터링

### 4.3 ROS-Unity 통신 (1주)

#### 4.3.1 TCP 연결 설정
```csharp
// Unity Scripts/ROSConnector.cs
public class ROSConnector : MonoBehaviour
{
    private TcpConnector tcpConnector;
    
    void Start()
    {
        tcpConnector = new TcpConnector();
        tcpConnector.Connect("192.168.1.100", 10000);
    }
    
    public void SendPoseData(Vector3 position, Quaternion rotation)
    {
        // ROS로 포즈 데이터 전송
    }
}
```

#### 4.3.2 실시간 데이터 스트리밍
- NeRF 렌더링 결과 수신
- 로봇 상태 시각화
- 센서 데이터 통합

### 4.4 NeRF 뷰어 통합 (0.5주)

#### 4.4.1 VR 내 NeRF 렌더링
```csharp
// Unity Scripts/NerfViewer.cs
public class NerfViewer : MonoBehaviour
{
    public RenderTexture nerfTexture;
    public GameObject viewSphere;
    
    void Update()
    {
        RequestNerfRender();
        UpdateView();
    }
    
    void RequestNerfRender()
    {
        // ROS에 렌더링 요청
    }
}
```

## ✅ 검증 기준

### RViz 플러그인 검증
- [ ] RViz에서 NerfViewController 정상 작동
- [ ] 점진적 해상도 렌더링 구현
- [ ] 마우스/키보드 상호작용 지원
- [ ] 실시간 성능 모니터링

### VR 시스템 검증
- [ ] Meta Quest 3에서 정상 실행
- [ ] 핸드 트래킹 정확도 > 95%
- [ ] VR 렌더링 프레임레이트 > 72 FPS
- [ ] ROS 통신 지연 < 50ms

### 통합 시스템 검증
- [ ] NeRF 뷰어 VR 통합 완료
- [ ] 실시간 포즈 데이터 교환
- [ ] 멀티유저 지원 (최소 2명)
- [ ] 1시간 연속 운영 안정성

## 🚨 문제 해결 가이드

### VR 개발 문제
1. **핸드 트래킹 불안정**
   - 조명 조건 최적화
   - 캘리브레이션 개선

2. **VR 멀미 최소화**
   - 프레임레이트 유지
   - 텔레포트 이동 구현

3. **Unity-ROS 통신 지연**
   - 메시지 압축
   - 배치 전송 최적화
