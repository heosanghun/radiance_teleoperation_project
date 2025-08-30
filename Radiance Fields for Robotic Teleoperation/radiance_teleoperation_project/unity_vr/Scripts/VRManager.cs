using UnityEngine;
using UnityEngine.XR;
using UnityEngine.XR.Interaction.Toolkit;
using System.Collections.Generic;

namespace RadianceTeleoperation
{
    /// <summary>
    /// VR 시스템 관리자
    /// Phase 4: 시각화 시스템 구현
    /// 
    /// 이 스크립트는 Meta Quest 3에서 VR 환경을 초기화하고 관리합니다.
    /// </summary>
    public class VRManager : MonoBehaviour
    {
        [Header("VR Components")]
        public GameObject headset;
        public GameObject leftHand;
        public GameObject rightHand;
        public GameObject palmMenu;
        
        [Header("ROS Integration")]
        public ROSConnector rosConnector;
        public NerfViewer nerfViewer;
        
        [Header("Hand Tracking")]
        public bool enableHandTracking = true;
        public bool enableHapticFeedback = true;
        
        [Header("Performance")]
        public int targetFrameRate = 72;
        public bool enableFoveatedRendering = true;
        
        // VR 상태
        private bool isVRInitialized = false;
        private bool isHandTrackingActive = false;
        
        // 핸드 트래킹 컴포넌트
        private XRHandSubsystem handSubsystem;
        private List<XRHandSubsystem> handSubsystems = new List<XRHandSubsystem>();
        
        // 하이브리드 렌더링
        private bool isHybridRenderingEnabled = false;
        
        void Start()
        {
            InitializeVR();
            ConnectToROS();
            SetupHandTracking();
            SetupPalmMenu();
        }
        
        void Update()
        {
            UpdateHandTracking();
            UpdatePalmMenu();
            UpdatePerformance();
        }
        
        /// <summary>
        /// VR 시스템 초기화
        /// </summary>
        void InitializeVR()
        {
            Debug.Log("VR 시스템 초기화 중...");
            
            // OpenXR 설정
            if (!InitializeOpenXR())
            {
                Debug.LogError("OpenXR 초기화 실패");
                return;
            }
            
            // 프레임레이트 설정
            Application.targetFrameRate = targetFrameRate;
            QualitySettings.vSyncCount = 0;
            
            // 하이브리드 렌더링 설정
            if (enableFoveatedRendering)
            {
                SetupFoveatedRendering();
            }
            
            isVRInitialized = true;
            Debug.Log("VR 시스템 초기화 완료");
        }
        
        /// <summary>
        /// OpenXR 초기화
        /// </summary>
        bool InitializeOpenXR()
        {
            // OpenXR 활성화 확인
            if (!XRSettings.isDeviceActive)
            {
                Debug.LogWarning("VR 디바이스가 활성화되지 않았습니다.");
                return false;
            }
            
            // OpenXR 설정
            XRSettings.eyeTextureResolutionScale = 1.0f;
            XRSettings.renderViewportScale = 1.0f;
            
            Debug.Log($"VR 디바이스: {XRSettings.loadedDeviceName}");
            Debug.Log($"렌더링 스케일: {XRSettings.renderViewportScale}");
            
            return true;
        }
        
        /// <summary>
        /// 하이브리드 렌더링 설정
        /// </summary>
        void SetupFoveatedRendering()
        {
            // Quest 3의 하이브리드 렌더링 설정
            if (XRSettings.loadedDeviceName.Contains("Oculus"))
            {
                // Oculus 특화 설정
                OVRPlugin.SetFoveatedRenderingLevel(OVRPlugin.FoveatedRenderingLevel.High);
                OVRPlugin.SetFoveatedRenderingDynamic(OVRPlugin.FoveatedRenderingDynamic.Enabled);
                
                isHybridRenderingEnabled = true;
                Debug.Log("하이브리드 렌더링이 활성화되었습니다.");
            }
        }
        
        /// <summary>
        /// ROS 연결 설정
        /// </summary>
        void ConnectToROS()
        {
            if (rosConnector == null)
            {
                rosConnector = FindObjectOfType<ROSConnector>();
            }
            
            if (rosConnector != null)
            {
                rosConnector.Initialize();
                Debug.Log("ROS 연결이 설정되었습니다.");
            }
            else
            {
                Debug.LogWarning("ROSConnector를 찾을 수 없습니다.");
            }
        }
        
        /// <summary>
        /// 핸드 트래킹 설정
        /// </summary>
        void SetupHandTracking()
        {
            if (!enableHandTracking)
                return;
            
            // 핸드 서브시스템 초기화
            SubsystemManager.GetInstances(handSubsystems);
            
            if (handSubsystems.Count > 0)
            {
                handSubsystem = handSubsystems[0];
                handSubsystem.Start();
                isHandTrackingActive = true;
                
                Debug.Log("핸드 트래킹이 활성화되었습니다.");
            }
            else
            {
                Debug.LogWarning("핸드 트래킹 서브시스템을 찾을 수 없습니다.");
            }
        }
        
        /// <summary>
        /// 팜 메뉴 설정
        /// </summary>
        void SetupPalmMenu()
        {
            if (palmMenu != null)
            {
                palmMenu.SetActive(false);
                Debug.Log("팜 메뉴가 설정되었습니다.");
            }
        }
        
        /// <summary>
        /// 핸드 트래킹 업데이트
        /// </summary>
        void UpdateHandTracking()
        {
            if (!isHandTrackingActive || handSubsystem == null)
                return;
            
            // 왼손 트래킹
            if (handSubsystem.TryGetJoint(XRHandJointID.Palm, XRHandSubsystem.Hand.Left, out XRHandJoint leftPalm))
            {
                UpdateHandTransform(leftHand, leftPalm);
            }
            
            // 오른손 트래킹
            if (handSubsystem.TryGetJoint(XRHandJointID.Palm, XRHandSubsystem.Hand.Right, out XRHandJoint rightPalm))
            {
                UpdateHandTransform(rightHand, rightPalm);
            }
            
            // 제스처 인식
            DetectGestures();
        }
        
        /// <summary>
        /// 핸드 트랜스폼 업데이트
        /// </summary>
        void UpdateHandTransform(GameObject handObject, XRHandJoint palmJoint)
        {
            if (handObject != null && palmJoint.tracked)
            {
                handObject.transform.position = palmJoint.pose.position;
                handObject.transform.rotation = palmJoint.pose.rotation;
            }
        }
        
        /// <summary>
        /// 제스처 인식
        /// </summary>
        void DetectGestures()
        {
            // 손가락 제스처 인식
            if (IsPointingGesture(XRHandSubsystem.Hand.Right))
            {
                HandlePointingGesture();
            }
            
            if (IsGrabGesture(XRHandSubsystem.Hand.Right))
            {
                HandleGrabGesture();
            }
            
            if (IsMenuGesture(XRHandSubsystem.Hand.Left))
            {
                TogglePalmMenu();
            }
        }
        
        /// <summary>
        /// 포인팅 제스처 확인
        /// </summary>
        bool IsPointingGesture(XRHandSubsystem.Hand hand)
        {
            if (handSubsystem == null)
                return false;
            
            // 검지가 펴져있고 다른 손가락이 접혀있는지 확인
            if (handSubsystem.TryGetJoint(XRHandJointID.IndexTip, hand, out XRHandJoint indexTip) &&
                handSubsystem.TryGetJoint(XRHandJointID.IndexProximal, hand, out XRHandJoint indexProximal))
            {
                float fingerExtension = Vector3.Distance(indexTip.pose.position, indexProximal.pose.position);
                return fingerExtension > 0.05f; // 임계값
            }
            
            return false;
        }
        
        /// <summary>
        /// 잡기 제스처 확인
        /// </summary>
        bool IsGrabGesture(XRHandSubsystem.Hand hand)
        {
            if (handSubsystem == null)
                return false;
            
            // 모든 손가락이 접혀있는지 확인
            // 실제 구현에서는 더 정교한 로직 필요
            return false;
        }
        
        /// <summary>
        /// 메뉴 제스처 확인
        /// </summary>
        bool IsMenuGesture(XRHandSubsystem.Hand hand)
        {
            if (handSubsystem == null)
                return false;
            
            // 손바닥이 위를 향하고 있는지 확인
            if (handSubsystem.TryGetJoint(XRHandJointID.Palm, hand, out XRHandJoint palm))
            {
                Vector3 palmUp = palm.pose.up;
                return Vector3.Dot(palmUp, Vector3.up) > 0.7f;
            }
            
            return false;
        }
        
        /// <summary>
        /// 포인팅 제스처 처리
        /// </summary>
        void HandlePointingGesture()
        {
            // NeRF 뷰어에 포인팅 정보 전달
            if (nerfViewer != null)
            {
                nerfViewer.HandlePointing(rightHand.transform.position, rightHand.transform.forward);
            }
        }
        
        /// <summary>
        /// 잡기 제스처 처리
        /// </summary>
        void HandleGrabGesture()
        {
            // 객체 조작 또는 VR 내 상호작용
            Debug.Log("잡기 제스처 감지됨");
        }
        
        /// <summary>
        /// 팜 메뉴 토글
        /// </summary>
        void TogglePalmMenu()
        {
            if (palmMenu != null)
            {
                palmMenu.SetActive(!palmMenu.activeSelf);
                
                if (palmMenu.activeSelf)
                {
                    // 메뉴 위치를 왼손 위치로 설정
                    palmMenu.transform.position = leftHand.transform.position + leftHand.transform.forward * 0.3f;
                    palmMenu.transform.rotation = leftHand.transform.rotation;
                }
            }
        }
        
        /// <summary>
        /// 팜 메뉴 업데이트
        /// </summary>
        void UpdatePalmMenu()
        {
            if (palmMenu != null && palmMenu.activeSelf)
            {
                // 메뉴가 활성화되어 있으면 위치 업데이트
                palmMenu.transform.position = leftHand.transform.position + leftHand.transform.forward * 0.3f;
            }
        }
        
        /// <summary>
        /// 성능 최적화 업데이트
        /// </summary>
        void UpdatePerformance()
        {
            // 프레임레이트 모니터링
            float currentFPS = 1.0f / Time.deltaTime;
            
            if (currentFPS < targetFrameRate * 0.8f)
            {
                // 성능 저하 시 품질 조정
                AdjustQualityForPerformance();
            }
        }
        
        /// <summary>
        /// 성능을 위한 품질 조정
        /// </summary>
        void AdjustQualityForPerformance()
        {
            // 렌더링 품질 동적 조정
            if (isHybridRenderingEnabled)
            {
                // 하이브리드 렌더링 품질 조정
                OVRPlugin.SetFoveatedRenderingLevel(OVRPlugin.FoveatedRenderingLevel.Medium);
            }
            
            Debug.Log("성능 최적화를 위해 품질이 조정되었습니다.");
        }
        
        /// <summary>
        /// 하이브리드 렌더링 활성화
        /// </summary>
        public void EnableHybridRendering()
        {
            if (XRSettings.loadedDeviceName.Contains("Oculus"))
            {
                SetupFoveatedRendering();
            }
        }
        
        /// <summary>
        /// 하이브리드 렌더링 비활성화
        /// </summary>
        public void DisableHybridRendering()
        {
            if (isHybridRenderingEnabled)
            {
                OVRPlugin.SetFoveatedRenderingLevel(OVRPlugin.FoveatedRenderingLevel.Off);
                isHybridRenderingEnabled = false;
                Debug.Log("하이브리드 렌더링이 비활성화되었습니다.");
            }
        }
        
        /// <summary>
        /// VR 상태 정보 반환
        /// </summary>
        public VRStatus GetVRStatus()
        {
            return new VRStatus
            {
                isInitialized = isVRInitialized,
                isHandTrackingActive = isHandTrackingActive,
                isHybridRenderingEnabled = isHybridRenderingEnabled,
                currentFrameRate = 1.0f / Time.deltaTime,
                targetFrameRate = targetFrameRate
            };
        }
        
        void OnDestroy()
        {
            // 정리 작업
            if (handSubsystem != null)
            {
                handSubsystem.Stop();
            }
            
            if (isHybridRenderingEnabled)
            {
                DisableHybridRendering();
            }
        }
    }
    
    /// <summary>
    /// VR 상태 정보
    /// </summary>
    [System.Serializable]
    public struct VRStatus
    {
        public bool isInitialized;
        public bool isHandTrackingActive;
        public bool isHybridRenderingEnabled;
        public float currentFrameRate;
        public int targetFrameRate;
    }
}
