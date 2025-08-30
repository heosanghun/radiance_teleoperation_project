using UnityEngine;
using System;
using System.Collections;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Newtonsoft.Json;

namespace RadianceTeleoperation
{
    /// <summary>
    /// ROS-Unity 통신 연결기
    /// Phase 4: 시각화 시스템 구현
    /// 
    /// 이 스크립트는 Unity와 ROS 간의 TCP 통신을 관리합니다.
    /// </summary>
    public class ROSConnector : MonoBehaviour
    {
        [Header("Connection Settings")]
        public string rosIP = "192.168.1.100";
        public int rosPort = 10000;
        public bool autoConnect = true;
        public float reconnectInterval = 5.0f;
        
        [Header("Topics")]
        public string poseTopic = "/nerf/view_pose";
        public string renderRequestTopic = "/nerf/render_request";
        public string renderedImageTopic = "/nerf/rendered_image";
        public string robotControlTopic = "/robot/control";
        
        [Header("Performance")]
        public int maxMessageSize = 1024 * 1024; // 1MB
        public float messageTimeout = 1.0f;
        
        // TCP 연결
        private TcpClient tcpClient;
        private NetworkStream networkStream;
        private Thread receiveThread;
        private bool isConnected = false;
        private bool shouldReconnect = true;
        
        // 메시지 큐
        private Queue<string> messageQueue = new Queue<string>();
        private readonly object queueLock = new object();
        
        // 이벤트
        public event Action<Vector3, Quaternion> OnPoseReceived;
        public event Action<Texture2D> OnImageReceived;
        public event Action<string> OnMessageReceived;
        public event Action OnConnected;
        public event Action OnDisconnected;
        
        // 상태
        private bool isInitialized = false;
        private float lastReconnectTime = 0f;
        
        void Start()
        {
            if (autoConnect)
            {
                Initialize();
            }
        }
        
        void Update()
        {
            // 메시지 큐 처리
            ProcessMessageQueue();
            
            // 재연결 시도
            if (shouldReconnect && !isConnected && Time.time - lastReconnectTime > reconnectInterval)
            {
                AttemptReconnect();
            }
        }
        
        /// <summary>
        /// ROS 연결 초기화
        /// </summary>
        public void Initialize()
        {
            if (isInitialized)
                return;
            
            Debug.Log("ROS 연결기 초기화 중...");
            
            // TCP 클라이언트 초기화
            tcpClient = new TcpClient();
            tcpClient.ReceiveBufferSize = maxMessageSize;
            tcpClient.SendBufferSize = maxMessageSize;
            
            // 연결 시도
            ConnectToROS();
            
            isInitialized = true;
        }
        
        /// <summary>
        /// ROS에 연결
        /// </summary>
        void ConnectToROS()
        {
            try
            {
                Debug.Log($"ROS에 연결 시도 중: {rosIP}:{rosPort}");
                
                tcpClient.Connect(rosIP, rosPort);
                networkStream = tcpClient.GetStream();
                
                isConnected = true;
                shouldReconnect = true;
                
                // 수신 스레드 시작
                StartReceiveThread();
                
                // 연결 이벤트 발생
                OnConnected?.Invoke();
                
                Debug.Log("ROS 연결 성공");
            }
            catch (Exception e)
            {
                Debug.LogError($"ROS 연결 실패: {e.Message}");
                isConnected = false;
                shouldReconnect = true;
            }
        }
        
        /// <summary>
        /// 재연결 시도
        /// </summary>
        void AttemptReconnect()
        {
            if (isConnected)
                return;
            
            lastReconnectTime = Time.time;
            Debug.Log("ROS 재연결 시도 중...");
            
            try
            {
                if (tcpClient != null)
                {
                    tcpClient.Close();
                }
                
                ConnectToROS();
            }
            catch (Exception e)
            {
                Debug.LogWarning($"재연결 실패: {e.Message}");
            }
        }
        
        /// <summary>
        /// 수신 스레드 시작
        /// </summary>
        void StartReceiveThread()
        {
            if (receiveThread != null && receiveThread.IsAlive)
            {
                receiveThread.Abort();
            }
            
            receiveThread = new Thread(ReceiveLoop);
            receiveThread.IsBackground = true;
            receiveThread.Start();
        }
        
        /// <summary>
        /// 수신 루프
        /// </summary>
        void ReceiveLoop()
        {
            byte[] buffer = new byte[maxMessageSize];
            
            while (isConnected && tcpClient != null && tcpClient.Connected)
            {
                try
                {
                    int bytesRead = networkStream.Read(buffer, 0, buffer.Length);
                    
                    if (bytesRead > 0)
                    {
                        string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                        
                        // 메시지 큐에 추가
                        lock (queueLock)
                        {
                            messageQueue.Enqueue(message);
                        }
                    }
                }
                catch (Exception e)
                {
                    Debug.LogError($"수신 오류: {e.Message}");
                    break;
                }
            }
            
            // 연결 끊김 처리
            isConnected = false;
            OnDisconnected?.Invoke();
        }
        
        /// <summary>
        /// 메시지 큐 처리
        /// </summary>
        void ProcessMessageQueue()
        {
            lock (queueLock)
            {
                while (messageQueue.Count > 0)
                {
                    string message = messageQueue.Dequeue();
                    ProcessMessage(message);
                }
            }
        }
        
        /// <summary>
        /// 메시지 처리
        /// </summary>
        void ProcessMessage(string message)
        {
            try
            {
                // JSON 메시지 파싱
                ROSMessage rosMessage = JsonConvert.DeserializeObject<ROSMessage>(message);
                
                switch (rosMessage.topic)
                {
                    case "/nerf/rendered_image":
                        ProcessImageMessage(rosMessage);
                        break;
                        
                    case "/robot/status":
                        ProcessRobotStatusMessage(rosMessage);
                        break;
                        
                    default:
                        OnMessageReceived?.Invoke(message);
                        break;
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"메시지 처리 오류: {e.Message}");
            }
        }
        
        /// <summary>
        /// 이미지 메시지 처리
        /// </summary>
        void ProcessImageMessage(ROSMessage message)
        {
            try
            {
                // Base64 인코딩된 이미지 데이터를 텍스처로 변환
                byte[] imageData = Convert.FromBase64String(message.data);
                
                // Unity 메인 스레드에서 텍스처 생성
                StartCoroutine(CreateTextureFromBytes(imageData));
            }
            catch (Exception e)
            {
                Debug.LogError($"이미지 메시지 처리 오류: {e.Message}");
            }
        }
        
        /// <summary>
        /// 바이트 배열로부터 텍스처 생성
        /// </summary>
        IEnumerator CreateTextureFromBytes(byte[] imageData)
        {
            Texture2D texture = new Texture2D(2, 2);
            
            if (texture.LoadImage(imageData))
            {
                OnImageReceived?.Invoke(texture);
            }
            else
            {
                Debug.LogError("이미지 로드 실패");
            }
            
            yield return null;
        }
        
        /// <summary>
        /// 로봇 상태 메시지 처리
        /// </summary>
        void ProcessRobotStatusMessage(ROSMessage message)
        {
            try
            {
                RobotStatus status = JsonConvert.DeserializeObject<RobotStatus>(message.data);
                Debug.Log($"로봇 상태: {status.status}");
            }
            catch (Exception e)
            {
                Debug.LogError($"로봇 상태 메시지 처리 오류: {e.Message}");
            }
        }
        
        /// <summary>
        /// 포즈 데이터 전송
        /// </summary>
        public void SendPose(Vector3 position, Quaternion rotation)
        {
            if (!isConnected)
                return;
            
            try
            {
                PoseMessage poseMessage = new PoseMessage
                {
                    topic = poseTopic,
                    position = new float[] { position.x, position.y, position.z },
                    rotation = new float[] { rotation.x, rotation.y, rotation.z, rotation.w }
                };
                
                string jsonMessage = JsonConvert.SerializeObject(poseMessage);
                SendMessage(jsonMessage);
            }
            catch (Exception e)
            {
                Debug.LogError($"포즈 전송 오류: {e.Message}");
            }
        }
        
        /// <summary>
        /// 렌더링 요청 전송
        /// </summary>
        public void SendRenderRequest(Vector3 position, Quaternion rotation, int quality = 2)
        {
            if (!isConnected)
                return;
            
            try
            {
                RenderRequestMessage renderRequest = new RenderRequestMessage
                {
                    topic = renderRequestTopic,
                    position = new float[] { position.x, position.y, position.z },
                    rotation = new float[] { rotation.x, rotation.y, rotation.z, rotation.w },
                    quality = quality
                };
                
                string jsonMessage = JsonConvert.SerializeObject(renderRequest);
                SendMessage(jsonMessage);
            }
            catch (Exception e)
            {
                Debug.LogError($"렌더링 요청 전송 오류: {e.Message}");
            }
        }
        
        /// <summary>
        /// 로봇 제어 명령 전송
        /// </summary>
        public void SendRobotControl(RobotCommand command)
        {
            if (!isConnected)
                return;
            
            try
            {
                ROSMessage controlMessage = new ROSMessage
                {
                    topic = robotControlTopic,
                    data = JsonConvert.SerializeObject(command)
                };
                
                string jsonMessage = JsonConvert.SerializeObject(controlMessage);
                SendMessage(jsonMessage);
            }
            catch (Exception e)
            {
                Debug.LogError($"로봇 제어 명령 전송 오류: {e.Message}");
            }
        }
        
        /// <summary>
        /// 메시지 전송
        /// </summary>
        void SendMessage(string message)
        {
            if (!isConnected || networkStream == null)
                return;
            
            try
            {
                byte[] data = Encoding.UTF8.GetBytes(message);
                networkStream.Write(data, 0, data.Length);
                networkStream.Flush();
            }
            catch (Exception e)
            {
                Debug.LogError($"메시지 전송 오류: {e.Message}");
                isConnected = false;
            }
        }
        
        /// <summary>
        /// 연결 상태 확인
        /// </summary>
        public bool IsConnected()
        {
            return isConnected && tcpClient != null && tcpClient.Connected;
        }
        
        /// <summary>
        /// 연결 강제 해제
        /// </summary>
        public void Disconnect()
        {
            shouldReconnect = false;
            isConnected = false;
            
            if (receiveThread != null && receiveThread.IsAlive)
            {
                receiveThread.Abort();
            }
            
            if (networkStream != null)
            {
                networkStream.Close();
            }
            
            if (tcpClient != null)
            {
                tcpClient.Close();
            }
            
            Debug.Log("ROS 연결이 해제되었습니다.");
        }
        
        void OnDestroy()
        {
            Disconnect();
        }
        
        void OnApplicationPause(bool pauseStatus)
        {
            if (pauseStatus)
            {
                // 앱이 일시정지되면 연결 유지
                Debug.Log("앱 일시정지 - 연결 유지");
            }
        }
        
        void OnApplicationFocus(bool hasFocus)
        {
            if (!hasFocus)
            {
                // 포커스를 잃으면 연결 상태 확인
                Debug.Log("앱 포커스 해제 - 연결 상태 확인");
            }
        }
    }
    
    /// <summary>
    /// ROS 메시지 기본 클래스
    /// </summary>
    [Serializable]
    public class ROSMessage
    {
        public string topic;
        public string data;
        public long timestamp;
    }
    
    /// <summary>
    /// 포즈 메시지
    /// </summary>
    [Serializable]
    public class PoseMessage
    {
        public string topic;
        public float[] position;
        public float[] rotation;
    }
    
    /// <summary>
    /// 렌더링 요청 메시지
    /// </summary>
    [Serializable]
    public class RenderRequestMessage
    {
        public string topic;
        public float[] position;
        public float[] rotation;
        public int quality;
    }
    
    /// <summary>
    /// 로봇 상태
    /// </summary>
    [Serializable]
    public class RobotStatus
    {
        public string status;
        public Vector3 position;
        public Quaternion rotation;
        public float battery;
    }
    
    /// <summary>
    /// 로봇 제어 명령
    /// </summary>
    [Serializable]
    public class RobotCommand
    {
        public string command;
        public Vector3 targetPosition;
        public Quaternion targetRotation;
        public float speed;
    }
}
