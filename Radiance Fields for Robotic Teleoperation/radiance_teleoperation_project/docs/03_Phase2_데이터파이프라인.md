# Phase 2: 데이터 수집 및 처리 파이프라인 구현 (3-4주)

## 🎯 목표
실시간 멀티 카메라 데이터 스트림 및 전처리 시스템 구축

## 📋 상세 작업 계획

### 2.1 멀티 카메라 데이터 수집 시스템 (1.5주)

#### 2.1.1 Camera Node 개발
```python
# radiance_camera/src/camera_node.py
#!/usr/bin/env python3

import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import TransformStamped
from cv_bridge import CvBridge
import tf2_ros
import yaml
import threading
import queue
from collections import deque

class MultiCameraNode:
    def __init__(self):
        rospy.init_node('multi_camera_node')
        
        # 설정 파일 로드
        self.config = self.load_config()
        
        # 브릿지 및 버퍼 초기화
        self.bridge = CvBridge()
        self.image_buffers = {}
        self.depth_buffers = {}
        self.info_buffers = {}
        
        # 카메라별 스레드 및 큐
        self.camera_threads = {}
        self.image_queues = {}
        
        # TF 브로드캐스터
        self.tf_broadcaster = tf2_ros.TransformBroadcaster()
        
        # 퍼블리셔 초기화
        self.init_publishers()
        
        # 카메라 초기화
        self.init_cameras()
        
    def load_config(self):
        """설정 파일 로드"""
        config_path = rospy.get_param('~config_path', 'config/camera_config.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def init_publishers(self):
        """퍼블리셔 초기화"""
        self.publishers = {}
        for camera in self.config['cameras']:
            name = camera['name']
            self.publishers[name] = {
                'image': rospy.Publisher(f'/{name}/image_raw', Image, queue_size=10),
                'depth': rospy.Publisher(f'/{name}/depth_raw', Image, queue_size=10),
                'info': rospy.Publisher(f'/{name}/camera_info', CameraInfo, queue_size=10)
            }
    
    def init_cameras(self):
        """카메라 초기화 및 스레드 시작"""
        for camera in self.config['cameras']:
            name = camera['name']
            
            # RealSense 카메라 초기화
            if 'realsense' in camera.get('type', '').lower():
                self.init_realsense_camera(camera)
            else:
                self.init_standard_camera(camera)
            
            # 버퍼 초기화
            self.image_buffers[name] = deque(maxlen=100)
            self.depth_buffers[name] = deque(maxlen=100)
            self.info_buffers[name] = deque(maxlen=100)
            
            # 스레드 시작
            self.start_camera_thread(camera)
    
    def init_realsense_camera(self, camera_config):
        """RealSense 카메라 초기화"""
        import pyrealsense2 as rs
        
        pipeline = rs.pipeline()
        config = rs.config()
        
        # 스트림 설정
        config.enable_stream(rs.stream.color, 
                           camera_config['intrinsics']['width'],
                           camera_config['intrinsics']['height'], 
                           rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth,
                           camera_config['intrinsics']['width'],
                           camera_config['intrinsics']['height'], 
                           rs.format.z16, 30)
        
        # 파이프라인 시작
        profile = pipeline.start(config)
        
        # 카메라 정보 저장
        camera_config['pipeline'] = pipeline
        camera_config['profile'] = profile
    
    def start_camera_thread(self, camera_config):
        """카메라 스레드 시작"""
        name = camera_config['name']
        
        def camera_loop():
            rate = rospy.Rate(30)  # 30 FPS
            
            while not rospy.is_shutdown():
                try:
                    if 'pipeline' in camera_config:
                        # RealSense 카메라
                        frames = camera_config['pipeline'].wait_for_frames()
                        color_frame = frames.get_color_frame()
                        depth_frame = frames.get_depth_frame()
                        
                        if color_frame and depth_frame:
                            # 이미지 변환
                            color_image = np.asanyarray(color_frame.get_data())
                            depth_image = np.asanyarray(depth_frame.get_data())
                            
                            # 메시지 생성 및 발행
                            self.publish_camera_data(name, color_image, depth_image, camera_config)
                    
                    rate.sleep()
                    
                except Exception as e:
                    rospy.logerr(f"Camera {name} error: {e}")
                    rate.sleep()
        
        # 스레드 시작
        thread = threading.Thread(target=camera_loop)
        thread.daemon = True
        thread.start()
        self.camera_threads[name] = thread
    
    def publish_camera_data(self, camera_name, color_image, depth_image, camera_config):
        """카메라 데이터 발행"""
        timestamp = rospy.Time.now()
        
        # 이미지 메시지 생성
        color_msg = self.bridge.cv2_to_imgmsg(color_image, "bgr8")
        color_msg.header.stamp = timestamp
        color_msg.header.frame_id = camera_config['camera_frame']
        
        depth_msg = self.bridge.cv2_to_imgmsg(depth_image, "16UC1")
        depth_msg.header.stamp = timestamp
        depth_msg.header.frame_id = camera_config['camera_frame']
        
        # 카메라 정보 메시지 생성
        info_msg = CameraInfo()
        info_msg.header.stamp = timestamp
        info_msg.header.frame_id = camera_config['camera_frame']
        info_msg.height = camera_config['intrinsics']['height']
        info_msg.width = camera_config['intrinsics']['width']
        info_msg.K = [
            camera_config['intrinsics']['fx'], 0, camera_config['intrinsics']['cx'],
            0, camera_config['intrinsics']['fy'], camera_config['intrinsics']['cy'],
            0, 0, 1
        ]
        info_msg.D = [
            camera_config['distortion']['k1'],
            camera_config['distortion']['k2'],
            camera_config['distortion']['p1'],
            camera_config['distortion']['p2'],
            camera_config['distortion']['k3']
        ]
        
        # 발행
        self.publishers[camera_name]['image'].publish(color_msg)
        self.publishers[camera_name]['depth'].publish(depth_msg)
        self.publishers[camera_name]['info'].publish(info_msg)
        
        # 버퍼에 저장
        self.image_buffers[camera_name].append(color_image)
        self.depth_buffers[camera_name].append(depth_image)
        self.info_buffers[camera_name].append(info_msg)
        
        # TF 발행
        self.publish_camera_tf(camera_name, camera_config, timestamp)
    
    def publish_camera_tf(self, camera_name, camera_config, timestamp):
        """카메라 TF 발행"""
        transform = TransformStamped()
        transform.header.stamp = timestamp
        transform.header.frame_id = camera_config.get('base_frame', 'world')
        transform.child_frame_id = camera_config['camera_frame']
        
        # 카메라 포즈 설정 (설정에서 로드)
        pose = camera_config.get('pose', {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': 0})
        
        transform.transform.translation.x = pose['x']
        transform.transform.translation.y = pose['y']
        transform.transform.translation.z = pose['z']
        
        # 오일러 각도를 쿼터니언으로 변환
        from tf.transformations import quaternion_from_euler
        q = quaternion_from_euler(pose['roll'], pose['pitch'], pose['yaw'])
        transform.transform.rotation.x = q[0]
        transform.transform.rotation.y = q[1]
        transform.transform.rotation.z = q[2]
        transform.transform.rotation.w = q[3]
        
        self.tf_broadcaster.sendTransform(transform)

if __name__ == '__main__':
    try:
        node = MultiCameraNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
```

#### 2.1.2 Data Buffer 시스템
```python
# radiance_camera/src/data_buffer.py
#!/usr/bin/env python3

import rospy
import numpy as np
from collections import deque
import threading
import time
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge

class DataBuffer:
    def __init__(self, buffer_size=100, sync_threshold=0.1):
        self.buffer_size = buffer_size
        self.sync_threshold = sync_threshold  # 초 단위
        
        # 카메라별 버퍼
        self.image_buffers = {}
        self.depth_buffers = {}
        self.info_buffers = {}
        self.timestamp_buffers = {}
        
        # 동기화된 데이터 버퍼
        self.sync_buffer = deque(maxlen=buffer_size)
        
        # 스레드 안전을 위한 락
        self.lock = threading.Lock()
        
        # 블러 감지 설정
        self.blur_threshold = 100  # Laplacian 분산 임계값
        
    def add_camera(self, camera_name):
        """새로운 카메라 추가"""
        with self.lock:
            self.image_buffers[camera_name] = deque(maxlen=self.buffer_size)
            self.depth_buffers[camera_name] = deque(maxlen=self.buffer_size)
            self.info_buffers[camera_name] = deque(maxlen=self.buffer_size)
            self.timestamp_buffers[camera_name] = deque(maxlen=self.buffer_size)
    
    def add_data(self, camera_name, image, depth, info, timestamp):
        """카메라 데이터 추가"""
        with self.lock:
            # 블러 검사
            if self.is_image_blurry(image):
                rospy.logwarn(f"Blurry image detected from {camera_name}")
                return False
            
            # 데이터 추가
            self.image_buffers[camera_name].append(image)
            self.depth_buffers[camera_name].append(depth)
            self.info_buffers[camera_name].append(info)
            self.timestamp_buffers[camera_name].append(timestamp)
            
            # 동기화 시도
            self.try_sync_data()
            return True
    
    def is_image_blurry(self, image):
        """이미지 블러 검사"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var < self.blur_threshold
    
    def try_sync_data(self):
        """모든 카메라의 데이터 동기화 시도"""
        if len(self.image_buffers) == 0:
            return
        
        # 모든 카메라에 데이터가 있는지 확인
        for camera_name in self.image_buffers:
            if len(self.timestamp_buffers[camera_name]) == 0:
                return
        
        # 가장 최근 타임스탬프 찾기
        latest_timestamps = {}
        for camera_name in self.timestamp_buffers:
            latest_timestamps[camera_name] = self.timestamp_buffers[camera_name][-1]
        
        # 동기화 가능한지 확인
        if self.can_sync_timestamps(latest_timestamps):
            # 동기화된 데이터 생성
            sync_data = self.create_sync_data(latest_timestamps)
            if sync_data:
                self.sync_buffer.append(sync_data)
    
    def can_sync_timestamps(self, timestamps):
        """타임스탬프 동기화 가능 여부 확인"""
        if len(timestamps) < 2:
            return True
        
        # 모든 타임스탬프가 임계값 내에 있는지 확인
        base_time = min(timestamps.values())
        for timestamp in timestamps.values():
            if abs(timestamp - base_time) > self.sync_threshold:
                return False
        return True
    
    def create_sync_data(self, timestamps):
        """동기화된 데이터 생성"""
        sync_data = {
            'timestamp': min(timestamps.values()),
            'cameras': {}
        }
        
        for camera_name in timestamps:
            # 해당 타임스탬프에 가장 가까운 데이터 찾기
            idx = self.find_closest_timestamp(camera_name, timestamps[camera_name])
            if idx >= 0:
                sync_data['cameras'][camera_name] = {
                    'image': self.image_buffers[camera_name][idx],
                    'depth': self.depth_buffers[camera_name][idx],
                    'info': self.info_buffers[camera_name][idx],
                    'timestamp': self.timestamp_buffers[camera_name][idx]
                }
        
        return sync_data if len(sync_data['cameras']) == len(self.image_buffers) else None
    
    def find_closest_timestamp(self, camera_name, target_timestamp):
        """가장 가까운 타임스탬프 인덱스 찾기"""
        timestamps = list(self.timestamp_buffers[camera_name])
        if not timestamps:
            return -1
        
        closest_idx = 0
        min_diff = abs(timestamps[0] - target_timestamp)
        
        for i, timestamp in enumerate(timestamps):
            diff = abs(timestamp - target_timestamp)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
        
        return closest_idx if min_diff <= self.sync_threshold else -1
    
    def get_latest_sync_data(self):
        """최신 동기화된 데이터 반환"""
        with self.lock:
            if len(self.sync_buffer) > 0:
                return self.sync_buffer[-1]
            return None
    
    def get_all_sync_data(self):
        """모든 동기화된 데이터 반환"""
        with self.lock:
            return list(self.sync_buffer)
    
    def clear_buffers(self):
        """모든 버퍼 클리어"""
        with self.lock:
            for camera_name in self.image_buffers:
                self.image_buffers[camera_name].clear()
                self.depth_buffers[camera_name].clear()
                self.info_buffers[camera_name].clear()
                self.timestamp_buffers[camera_name].clear()
            self.sync_buffer.clear()
```

### 2.2 데이터 전처리 파이프라인 (1주)

#### 2.2.1 Image Preprocessing
```python
# radiance_camera/src/image_preprocessor.py
#!/usr/bin/env python3

import cv2
import numpy as np
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge

class ImagePreprocessor:
    def __init__(self, config):
        self.config = config
        self.bridge = CvBridge()
        
        # 왜곡 보정을 위한 맵 생성
        self.undistort_maps = {}
        self.init_undistort_maps()
    
    def init_undistort_maps(self):
        """왜곡 보정 맵 초기화"""
        for camera_name, camera_config in self.config['cameras'].items():
            # 카메라 매트릭스
            K = np.array([
                [camera_config['intrinsics']['fx'], 0, camera_config['intrinsics']['cx']],
                [0, camera_config['intrinsics']['fy'], camera_config['intrinsics']['cy']],
                [0, 0, 1]
            ])
            
            # 왜곡 계수
            D = np.array([
                camera_config['distortion']['k1'],
                camera_config['distortion']['k2'],
                camera_config['distortion']['p1'],
                camera_config['distortion']['p2'],
                camera_config['distortion']['k3']
            ])
            
            # 왜곡 보정 맵 생성
            h, w = camera_config['intrinsics']['height'], camera_config['intrinsics']['width']
            map1, map2 = cv2.initUndistortRectifyMap(K, D, None, K, (w, h), cv2.CV_32FC1)
            
            self.undistort_maps[camera_name] = (map1, map2)
    
    def preprocess_image(self, image, camera_name):
        """이미지 전처리"""
        # 왜곡 보정
        if camera_name in self.undistort_maps:
            map1, map2 = self.undistort_maps[camera_name]
            image = cv2.remap(image, map1, map2, cv2.INTER_LINEAR)
        
        # 색상 정규화
        image = self.normalize_colors(image)
        
        # 해상도 조정 (필요시)
        target_size = self.config.get('target_size', None)
        if target_size:
            image = cv2.resize(image, target_size)
        
        return image
    
    def normalize_colors(self, image):
        """색상 정규화"""
        # BGR to RGB 변환
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 정규화 (0-1 범위)
        image_normalized = image_rgb.astype(np.float32) / 255.0
        
        return image_normalized
    
    def preprocess_depth(self, depth_image, camera_name):
        """깊이 이미지 전처리"""
        # 깊이 이미지를 미터 단위로 변환
        depth_meters = depth_image.astype(np.float32) / 1000.0
        
        # 무효한 깊이값 필터링
        depth_meters[depth_meters == 0] = np.nan
        
        return depth_meters
```

#### 2.2.2 Transform 관리
```python
# radiance_camera/src/transform_manager.py
#!/usr/bin/env python3

import rospy
import numpy as np
import tf2_ros
import tf2_geometry_msgs
from geometry_msgs.msg import TransformStamped, PoseStamped
from sensor_msgs.msg import CameraInfo
import threading

class TransformManager:
    def __init__(self):
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster()
        
        # 카메라 포즈 캐시
        self.camera_poses = {}
        self.pose_lock = threading.Lock()
        
        # TF 트리 구성
        self.setup_tf_tree()
    
    def setup_tf_tree(self):
        """TF 트리 구성"""
        # 기본 TF 프레임 설정
        base_frames = ['world', 'map', 'base_link']
        for frame in base_frames:
            self.broadcast_static_transform(frame, 'world', [0, 0, 0], [0, 0, 0, 1])
    
    def broadcast_static_transform(self, child_frame, parent_frame, translation, rotation):
        """정적 TF 발행"""
        transform = TransformStamped()
        transform.header.stamp = rospy.Time.now()
        transform.header.frame_id = parent_frame
        transform.child_frame_id = child_frame
        transform.transform.translation.x = translation[0]
        transform.transform.translation.y = translation[1]
        transform.transform.translation.z = translation[2]
        transform.transform.rotation.x = rotation[0]
        transform.transform.rotation.y = rotation[1]
        transform.transform.rotation.z = rotation[2]
        transform.transform.rotation.w = rotation[3]
        
        self.tf_broadcaster.sendTransform(transform)
    
    def get_camera_pose(self, camera_frame, base_frame='world', timeout=1.0):
        """카메라 포즈 조회"""
        try:
            # TF 버퍼에서 변환 조회
            transform = self.tf_buffer.lookup_transform(
                base_frame, camera_frame, rospy.Time(0), rospy.Duration(timeout)
            )
            
            # 변환을 포즈로 변환
            pose = PoseStamped()
            pose.header = transform.header
            pose.pose.position = transform.transform.translation
            pose.pose.orientation = transform.transform.rotation
            
            return pose
            
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
            rospy.logwarn(f"TF lookup failed: {e}")
            return None
    
    def update_camera_pose(self, camera_name, pose):
        """카메라 포즈 업데이트"""
        with self.pose_lock:
            self.camera_poses[camera_name] = pose
    
    def get_all_camera_poses(self, base_frame='world'):
        """모든 카메라 포즈 조회"""
        poses = {}
        with self.pose_lock:
            for camera_name in self.camera_poses:
                pose = self.get_camera_pose(self.camera_poses[camera_name].header.frame_id, base_frame)
                if pose:
                    poses[camera_name] = pose
        return poses
```

### 2.3 Configuration 시스템 (3일)

#### 2.3.1 설정 파일 구조
```yaml
# config/camera_config.yaml
# 카메라 설정
cameras:
  - name: "front_camera"
    type: "realsense"
    image_topic: "/front_camera/color/image_raw"
    depth_topic: "/front_camera/depth/image_rect_raw"
    info_topic: "/front_camera/color/camera_info"
    camera_frame: "front_camera_color_optical_frame"
    base_frame: "world"
    
    # 카메라 내부 파라미터
    intrinsics:
      width: 640
      height: 480
      fx: 615.0
      fy: 615.0
      cx: 320.0
      cy: 240.0
    
    # 왜곡 계수
    distortion:
      k1: 0.0
      k2: 0.0
      k3: 0.0
      p1: 0.0
      p2: 0.0
    
    # 카메라 포즈 (기본값)
    pose:
      x: 0.0
      y: 0.0
      z: 1.0
      roll: 0.0
      pitch: 0.0
      yaw: 0.0
    
    # 캡처 설정
    capture:
      fps: 30
      blur_threshold: 100
      auto_exposure: true
      exposure_time: 10000

  - name: "rear_camera"
    type: "realsense"
    image_topic: "/rear_camera/color/image_raw"
    depth_topic: "/rear_camera/depth/image_rect_raw"
    info_topic: "/rear_camera/color/camera_info"
    camera_frame: "rear_camera_color_optical_frame"
    base_frame: "world"
    
    intrinsics:
      width: 640
      height: 480
      fx: 615.0
      fy: 615.0
      cx: 320.0
      cy: 240.0
    
    distortion:
      k1: 0.0
      k2: 0.0
      k3: 0.0
      p1: 0.0
      p2: 0.0
    
    pose:
      x: 0.0
      y: 0.0
      z: 1.0
      roll: 0.0
      pitch: 0.0
      yaw: 3.14159  # 180도
    
    capture:
      fps: 30
      blur_threshold: 100
      auto_exposure: true
      exposure_time: 10000

# 데이터 처리 설정
processing:
  target_size: [640, 480]
  sync_threshold: 0.1  # 초
  buffer_size: 100
  enable_blur_detection: true
  enable_undistortion: true
  enable_normalization: true

# 저장 설정
storage:
  save_path: "/tmp/radiance_data"
  auto_save: false
  save_format: "rosbag"  # rosbag, images, nerfstudio
  compression: true
```

#### 2.3.2 설정 관리자
```python
# radiance_camera/src/config_manager.py
#!/usr/bin/env python3

import rospy
import yaml
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = rospy.get_param('~config_path', 'config/camera_config.yaml')
        
        self.config_path = config_path
        self.config = self.load_config()
        
        # 설정 변경 감지를 위한 파일 수정 시간
        self.last_modified = os.path.getmtime(config_path)
    
    def load_config(self):
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # 기본값 설정
            config = self.set_defaults(config)
            
            rospy.loginfo(f"Configuration loaded from {self.config_path}")
            return config
            
        except Exception as e:
            rospy.logerr(f"Failed to load config: {e}")
            return self.get_default_config()
    
    def set_defaults(self, config):
        """기본값 설정"""
        # 카메라 기본값
        for camera in config.get('cameras', []):
            if 'capture' not in camera:
                camera['capture'] = {}
            
            camera['capture'].setdefault('fps', 30)
            camera['capture'].setdefault('blur_threshold', 100)
            camera['capture'].setdefault('auto_exposure', True)
            camera['capture'].setdefault('exposure_time', 10000)
        
        # 처리 기본값
        if 'processing' not in config:
            config['processing'] = {}
        
        config['processing'].setdefault('target_size', [640, 480])
        config['processing'].setdefault('sync_threshold', 0.1)
        config['processing'].setdefault('buffer_size', 100)
        config['processing'].setdefault('enable_blur_detection', True)
        config['processing'].setdefault('enable_undistortion', True)
        config['processing'].setdefault('enable_normalization', True)
        
        # 저장 기본값
        if 'storage' not in config:
            config['storage'] = {}
        
        config['storage'].setdefault('save_path', '/tmp/radiance_data')
        config['storage'].setdefault('auto_save', False)
        config['storage'].setdefault('save_format', 'rosbag')
        config['storage'].setdefault('compression', True)
        
        return config
    
    def get_default_config(self):
        """기본 설정 반환"""
        return {
            'cameras': [],
            'processing': {
                'target_size': [640, 480],
                'sync_threshold': 0.1,
                'buffer_size': 100,
                'enable_blur_detection': True,
                'enable_undistortion': True,
                'enable_normalization': True
            },
            'storage': {
                'save_path': '/tmp/radiance_data',
                'auto_save': False,
                'save_format': 'rosbag',
                'compression': True
            }
        }
    
    def check_for_updates(self):
        """설정 파일 업데이트 확인"""
        try:
            current_modified = os.path.getmtime(self.config_path)
            if current_modified > self.last_modified:
                self.config = self.load_config()
                self.last_modified = current_modified
                return True
        except Exception as e:
            rospy.logwarn(f"Failed to check config updates: {e}")
        
        return False
    
    def get_camera_config(self, camera_name):
        """특정 카메라 설정 반환"""
        for camera in self.config.get('cameras', []):
            if camera['name'] == camera_name:
                return camera
        return None
    
    def get_processing_config(self):
        """처리 설정 반환"""
        return self.config.get('processing', {})
    
    def get_storage_config(self):
        """저장 설정 반환"""
        return self.config.get('storage', {})
    
    def update_config(self, updates):
        """설정 업데이트"""
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        
        self.config = deep_update(self.config, updates)
        
        # 파일에 저장
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            rospy.loginfo("Configuration updated and saved")
        except Exception as e:
            rospy.logerr(f"Failed to save config: {e}")
```

## ✅ 검증 기준

### 데이터 수집 검증
- [ ] 멀티 카메라 동시 스트리밍 (30 FPS)
- [ ] 이미지-깊이 동기화 (지연 < 100ms)
- [ ] 블러 감지 및 필터링 정상 작동
- [ ] TF 트리 정상 구성 및 발행

### 데이터 처리 검증
- [ ] 왜곡 보정 정상 작동
- [ ] 색상 정규화 (0-1 범위)
- [ ] 해상도 조정 정상 작동
- [ ] 메모리 사용량 최적화

### 설정 시스템 검증
- [ ] YAML 설정 파일 정상 로드
- [ ] 실시간 설정 업데이트
- [ ] 기본값 자동 설정
- [ ] 설정 검증 및 오류 처리

## 🚨 문제 해결 가이드

### 일반적인 문제들
1. **카메라 동기화 실패**
   - 해결: 타임스탬프 임계값 조정, 네트워크 지연 확인
2. **메모리 사용량 과다**
   - 해결: 버퍼 크기 조정, 가비지 컬렉션 최적화
3. **TF 변환 실패**
   - 해결: TF 트리 구성 확인, 타임아웃 설정 조정

### 성능 최적화 팁
- 멀티스레딩 활용으로 병렬 처리
- 메모리 매핑으로 대용량 데이터 처리
- GPU 가속 활용 (가능시)
