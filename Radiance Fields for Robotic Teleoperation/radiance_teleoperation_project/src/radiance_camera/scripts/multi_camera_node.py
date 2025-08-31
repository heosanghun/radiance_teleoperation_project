#!/usr/bin/env python3

"""
Radiance Fields for Robotic Teleoperation - 멀티 카메라 노드
Phase 2: 데이터 수집 및 처리 파이프라인

이 노드는 여러 RealSense 카메라에서 실시간으로 이미지와 깊이 데이터를 수집하고,
동기화된 데이터 스트림을 제공합니다.
"""

import rclpy
from rclpy.node import Node
import cv2
import numpy as np
import yaml
import threading
import time
from collections import deque
from typing import Dict, List, Optional

# ROS 2 메시지
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import TransformStamped
from std_msgs.msg import String

# ROS 2 유틸리티
from cv_bridge import CvBridge
import tf2_ros
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import Quaternion
from tf_transformations import quaternion_from_euler

# RealSense
try:
    import pyrealsense2 as rs
    REALSENSE_AVAILABLE = True
except ImportError:
    REALSENSE_AVAILABLE = False
    print("pyrealsense2가 설치되지 않았습니다. RealSense 카메라를 사용할 수 없습니다.")

class MultiCameraNode(Node):
    """
    멀티 카메라 데이터 수집 및 동기화 노드
    """
    
    def __init__(self):
        """노드 초기화"""
        super().__init__('multi_camera_node')
        
        # 설정 파일 로드
        self.config = self._load_config()
        
        # 브릿지 및 버퍼 초기화
        self.bridge = CvBridge()
        self.image_buffers = {}
        self.depth_buffers = {}
        self.info_buffers = {}
        
        # 카메라별 스레드 및 파이프라인
        self.camera_threads = {}
        self.pipelines = {}
        
        # TF 브로드캐스터
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # 퍼블리셔 초기화
        self.publishers = self._init_publishers()
        
        # 카메라 초기화
        self._init_cameras()
        
        # 동기화된 데이터 버퍼
        self.sync_buffer = deque(maxlen=self.config['processing']['buffer_size'])
        self.sync_lock = threading.Lock()
        
        # 통계 정보
        self.stats = {
            'total_frames': 0,
            'dropped_frames': 0,
            'sync_frames': 0,
            'last_sync_time': time.time()
        }
        
        # 통계 발행자
        self.stats_publisher = self.create_publisher(String, 'camera_stats', 10)
        self.stats_timer = self.create_timer(1.0, self._publish_stats)
        
        self.get_logger().info("멀티 카메라 노드가 초기화되었습니다.")
    
    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        config_path = self.declare_parameter('config_path', 'config/camera_config.yaml').value
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.get_logger().info(f"설정 파일을 로드했습니다: {config_path}")
            return config
        except Exception as e:
            self.get_logger().error(f"설정 파일 로드 실패: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """기본 설정 반환"""
        return {
            'cameras': [],
            'processing': {
                'target_size': [640, 480],
                'sync_threshold': 0.1,
                'buffer_size': 100
            },
            'storage': {
                'save_path': '/tmp/radiance_data'
            }
        }
    
    def _init_publishers(self) -> Dict:
        """퍼블리셔 초기화"""
        publishers = {}
        for camera in self.config['cameras']:
            name = camera['name']
            publishers[name] = {
                'image': self.create_publisher(Image, f'/{name}/image_raw', 10),
                'depth': self.create_publisher(Image, f'/{name}/depth_raw', 10),
                'info': self.create_publisher(CameraInfo, f'/{name}/camera_info', 10)
            }
        return publishers
    
    def _init_cameras(self):
        """카메라 초기화 및 스레드 시작"""
        if not REALSENSE_AVAILABLE:
            self.get_logger().error("RealSense SDK가 사용할 수 없습니다.")
            return
        
        for camera in self.config['cameras']:
            name = camera['name']
            
            # RealSense 카메라 초기화
            if self._init_realsense_camera(camera):
                # 버퍼 초기화
                self.image_buffers[name] = deque(maxlen=100)
                self.depth_buffers[name] = deque(maxlen=100)
                self.info_buffers[name] = deque(maxlen=100)
                
                # 스레드 시작
                self._start_camera_thread(camera)
                
                self.get_logger().info(f"카메라 {name} 초기화 완료")
            else:
                self.get_logger().error(f"카메라 {name} 초기화 실패")
    
    def _init_realsense_camera(self, camera_config: Dict) -> bool:
        """RealSense 카메라 초기화"""
        try:
            pipeline = rs.pipeline()
            config = rs.config()
            
            # 스트림 설정
            config.enable_stream(
                rs.stream.color,
                camera_config['intrinsics']['width'],
                camera_config['intrinsics']['height'],
                rs.format.bgr8,
                camera_config['capture']['fps']
            )
            config.enable_stream(
                rs.stream.depth,
                camera_config['intrinsics']['width'],
                camera_config['intrinsics']['height'],
                rs.format.z16,
                camera_config['capture']['fps']
            )
            
            # 파이프라인 시작
            profile = pipeline.start(config)
            
            # 카메라 정보 저장
            camera_config['pipeline'] = pipeline
            camera_config['profile'] = profile
            
            # 카메라 설정 적용
            self._apply_camera_settings(camera_config)
            
            return True
            
        except Exception as e:
            self.get_logger().error(f"RealSense 카메라 초기화 실패: {e}")
            return False
    
    def _apply_camera_settings(self, camera_config: Dict):
        """카메라 설정 적용"""
        try:
            pipeline = camera_config['pipeline']
            profile = camera_config['profile']
            
            # 센서 가져오기
            sensor = profile.get_device().first_depth_sensor()
            
            # 자동 노출 설정
            if camera_config['capture']['auto_exposure']:
                sensor.set_option(rs.option.enable_auto_exposure, 1)
            else:
                sensor.set_option(rs.option.enable_auto_exposure, 0)
                sensor.set_option(rs.option.exposure, camera_config['capture']['exposure_time'])
            
            self.get_logger().info(f"카메라 설정이 적용되었습니다: {camera_config['name']}")
            
        except Exception as e:
            self.get_logger().warn(f"카메라 설정 적용 실패: {e}")
    
    def _start_camera_thread(self, camera_config: Dict):
        """카메라 스레드 시작"""
        name = camera_config['name']
        
        def camera_loop():
            rate = self.create_rate(camera_config['capture']['fps'])
            
            while rclpy.ok():
                try:
                    if 'pipeline' in camera_config:
                        # RealSense 카메라에서 프레임 가져오기
                        frames = camera_config['pipeline'].wait_for_frames()
                        color_frame = frames.get_color_frame()
                        depth_frame = frames.get_depth_frame()
                        
                        if color_frame and depth_frame:
                            # 이미지 변환
                            color_image = np.asanyarray(color_frame.get_data())
                            depth_image = np.asanyarray(depth_frame.get_data())
                            
                            # 블러 검사
                            if self._is_image_blurry(color_image, camera_config):
                                self.get_logger().warn(f"블러 이미지 감지됨: {name}")
                                continue
                            
                            # 메시지 생성 및 발행
                            self._publish_camera_data(name, color_image, depth_image, camera_config)
                            
                            # 동기화 시도
                            self._try_sync_data()
                    
                    rate.sleep()
                    
                except Exception as e:
                    self.get_logger().error(f"카메라 {name} 오류: {e}")
                    rate.sleep()
        
        # 스레드 시작
        thread = threading.Thread(target=camera_loop)
        thread.daemon = True
        thread.start()
        self.camera_threads[name] = thread
    
    def _is_image_blurry(self, image: np.ndarray, camera_config: Dict) -> bool:
        """이미지 블러 검사"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            threshold = camera_config['capture']['blur_threshold']
            return laplacian_var < threshold
        except Exception as e:
            self.get_logger().warn(f"블러 검사 실패: {e}")
            return False
    
    def _publish_camera_data(self, camera_name: str, color_image: np.ndarray, 
                           depth_image: np.ndarray, camera_config: Dict):
        """카메라 데이터 발행"""
        timestamp = self.get_clock().now().to_msg()
        
        # 이미지 메시지 생성
        color_msg = self.bridge.cv2_to_imgmsg(color_image, "bgr8")
        color_msg.header.stamp = timestamp
        color_msg.header.frame_id = camera_config['camera_frame']
        
        depth_msg = self.bridge.cv2_to_imgmsg(depth_image, "16UC1")
        depth_msg.header.stamp = timestamp
        depth_msg.header.frame_id = camera_config['camera_frame']
        
        # 카메라 정보 메시지 생성
        info_msg = self._create_camera_info(camera_config, timestamp)
        
        # 발행
        self.publishers[camera_name]['image'].publish(color_msg)
        self.publishers[camera_name]['depth'].publish(depth_msg)
        self.publishers[camera_name]['info'].publish(info_msg)
        
        # 버퍼에 저장
        self.image_buffers[camera_name].append(color_image)
        self.depth_buffers[camera_name].append(depth_image)
        self.info_buffers[camera_name].append(info_msg)
        
        # TF 발행
        self._publish_camera_tf(camera_name, camera_config, timestamp)
        
        # 통계 업데이트
        self.stats['total_frames'] += 1
    
    def _create_camera_info(self, camera_config: Dict, timestamp) -> CameraInfo:
        """카메라 정보 메시지 생성"""
        info_msg = CameraInfo()
        info_msg.header.stamp = timestamp
        info_msg.header.frame_id = camera_config['camera_frame']
        info_msg.height = camera_config['intrinsics']['height']
        info_msg.width = camera_config['intrinsics']['width']
        
        # 카메라 매트릭스
        info_msg.k = [
            camera_config['intrinsics']['fx'], 0, camera_config['intrinsics']['cx'],
            0, camera_config['intrinsics']['fy'], camera_config['intrinsics']['cy'],
            0, 0, 1
        ]
        
        # 왜곡 계수
        info_msg.d = [
            camera_config['distortion']['k1'],
            camera_config['distortion']['k2'],
            camera_config['distortion']['p1'],
            camera_config['distortion']['p2'],
            camera_config['distortion']['k3']
        ]
        
        return info_msg
    
    def _publish_camera_tf(self, camera_name: str, camera_config: Dict, timestamp):
        """카메라 TF 발행"""
        transform = TransformStamped()
        transform.header.stamp = timestamp
        transform.header.frame_id = camera_config.get('base_frame', 'world')
        transform.child_frame_id = camera_config['camera_frame']
        
        # 카메라 포즈 설정
        pose = camera_config.get('pose', {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': 0})
        
        transform.transform.translation.x = pose['x']
        transform.transform.translation.y = pose['y']
        transform.transform.translation.z = pose['z']
        
        # 오일러 각도를 쿼터니언으로 변환
        q = quaternion_from_euler(pose['roll'], pose['pitch'], pose['yaw'])
        transform.transform.rotation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
        
        self.tf_broadcaster.sendTransform(transform)
    
    def _try_sync_data(self):
        """모든 카메라의 데이터 동기화 시도"""
        with self.sync_lock:
            # 모든 카메라에 데이터가 있는지 확인
            if not all(len(self.image_buffers[name]) > 0 for name in self.image_buffers):
                return
            
            # 가장 최근 타임스탬프 찾기
            latest_timestamps = {}
            for name in self.image_buffers:
                if len(self.info_buffers[name]) > 0:
                    latest_timestamps[name] = self.info_buffers[name][-1].header.stamp.sec + \
                                            self.info_buffers[name][-1].header.stamp.nanosec * 1e-9
            
            # 동기화 가능한지 확인
            if self._can_sync_timestamps(latest_timestamps):
                # 동기화된 데이터 생성
                sync_data = self._create_sync_data(latest_timestamps)
                if sync_data:
                    self.sync_buffer.append(sync_data)
                    self.stats['sync_frames'] += 1
                    self.stats['last_sync_time'] = time.time()
    
    def _can_sync_timestamps(self, timestamps: Dict[str, float]) -> bool:
        """타임스탬프 동기화 가능 여부 확인"""
        if len(timestamps) < 2:
            return True
        
        threshold = self.config['processing']['sync_threshold']
        base_time = min(timestamps.values())
        
        for timestamp in timestamps.values():
            if abs(timestamp - base_time) > threshold:
                return False
        return True
    
    def _create_sync_data(self, timestamps: Dict[str, float]) -> Optional[Dict]:
        """동기화된 데이터 생성"""
        sync_data = {
            'timestamp': min(timestamps.values()),
            'cameras': {}
        }
        
        for camera_name in timestamps:
            if len(self.image_buffers[camera_name]) > 0:
                sync_data['cameras'][camera_name] = {
                    'image': self.image_buffers[camera_name][-1],
                    'depth': self.depth_buffers[camera_name][-1],
                    'info': self.info_buffers[camera_name][-1],
                    'timestamp': timestamps[camera_name]
                }
        
        return sync_data if len(sync_data['cameras']) == len(self.image_buffers) else None
    
    def get_latest_sync_data(self) -> Optional[Dict]:
        """최신 동기화된 데이터 반환"""
        with self.sync_lock:
            if len(self.sync_buffer) > 0:
                return self.sync_buffer[-1]
            return None
    
    def get_stats(self) -> Dict:
        """통계 정보 반환"""
        return self.stats.copy()
    
    def _publish_stats(self):
        """통계 정보 발행"""
        try:
            stats = self.get_stats()
            stats_msg = f"Total: {stats['total_frames']}, Sync: {stats['sync_frames']}, Dropped: {stats['dropped_frames']}"
            msg = String()
            msg.data = stats_msg
            self.stats_publisher.publish(msg)
        except Exception as e:
            self.get_logger().error(f"통계 발행 실패: {e}")
    
    def _cleanup(self):
        """정리 작업"""
        self.get_logger().info("멀티 카메라 노드를 종료합니다.")
        
        # 파이프라인 정지
        for camera_config in self.config['cameras']:
            if 'pipeline' in camera_config:
                try:
                    camera_config['pipeline'].stop()
                except Exception as e:
                    self.get_logger().warn(f"파이프라인 정지 실패: {e}")

def main(args=None):
    """메인 함수"""
    rclpy.init(args=args)
    
    try:
        node = MultiCameraNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"노드 실행 중 오류 발생: {e}")
    finally:
        node._cleanup()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
