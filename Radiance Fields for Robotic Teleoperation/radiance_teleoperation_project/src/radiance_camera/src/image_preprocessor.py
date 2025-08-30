#!/usr/bin/env python3

"""
Radiance Fields for Robotic Teleoperation - 이미지 전처리 모듈
Phase 2: 데이터 수집 및 처리 파이프라인

이 모듈은 카메라에서 수집된 이미지와 깊이 데이터를 전처리하여
NeRF 훈련에 적합한 형태로 변환합니다.
"""

import cv2
import numpy as np
import rospy
from typing import Dict, Tuple, Optional
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge

class ImagePreprocessor:
    """
    이미지 및 깊이 데이터 전처리 클래스
    """
    
    def __init__(self, config: Dict):
        """
        전처리기 초기화
        
        Args:
            config: 설정 딕셔너리
        """
        self.config = config
        self.bridge = CvBridge()
        
        # 왜곡 보정을 위한 맵 생성
        self.undistort_maps = {}
        self._init_undistort_maps()
        
        # 필터링 설정
        self.depth_min = config['processing']['depth_min']
        self.depth_max = config['processing']['depth_max']
        
        # 타겟 크기
        self.target_size = tuple(config['processing']['target_size'])
        
        rospy.loginfo("이미지 전처리기가 초기화되었습니다.")
    
    def _init_undistort_maps(self):
        """왜곡 보정 맵 초기화"""
        for camera in self.config['cameras']:
            camera_name = camera['name']
            
            # 카메라 매트릭스
            K = np.array([
                [camera['intrinsics']['fx'], 0, camera['intrinsics']['cx']],
                [0, camera['intrinsics']['fy'], camera['intrinsics']['cy']],
                [0, 0, 1]
            ])
            
            # 왜곡 계수
            D = np.array([
                camera['distortion']['k1'],
                camera['distortion']['k2'],
                camera['distortion']['p1'],
                camera['distortion']['p2'],
                camera['distortion']['k3']
            ])
            
            # 왜곡 보정 맵 생성
            h, w = camera['intrinsics']['height'], camera['intrinsics']['width']
            map1, map2 = cv2.initUndistortRectifyMap(K, D, None, K, (w, h), cv2.CV_32FC1)
            
            self.undistort_maps[camera_name] = (map1, map2)
            
            rospy.loginfo(f"카메라 {camera_name}의 왜곡 보정 맵이 생성되었습니다.")
    
    def preprocess_image(self, image: np.ndarray, camera_name: str) -> np.ndarray:
        """
        이미지 전처리
        
        Args:
            image: 입력 이미지 (BGR)
            camera_name: 카메라 이름
            
        Returns:
            전처리된 이미지 (RGB, 정규화됨)
        """
        try:
            # 왜곡 보정
            if self.config['processing']['enable_undistortion'] and camera_name in self.undistort_maps:
                map1, map2 = self.undistort_maps[camera_name]
                image = cv2.remap(image, map1, map2, cv2.INTER_LINEAR)
            
            # 색상 정규화
            if self.config['processing']['enable_normalization']:
                image = self._normalize_colors(image)
            
            # 해상도 조정
            if self.target_size and image.shape[:2] != self.target_size[::-1]:
                image = cv2.resize(image, self.target_size, interpolation=cv2.INTER_LINEAR)
            
            return image
            
        except Exception as e:
            rospy.logerr(f"이미지 전처리 실패: {e}")
            return image
    
    def preprocess_depth(self, depth_image: np.ndarray, camera_name: str) -> np.ndarray:
        """
        깊이 이미지 전처리
        
        Args:
            depth_image: 입력 깊이 이미지 (16UC1)
            camera_name: 카메라 이름
            
        Returns:
            전처리된 깊이 이미지 (미터 단위, 필터링됨)
        """
        try:
            # 깊이 이미지를 미터 단위로 변환
            depth_meters = depth_image.astype(np.float32) / 1000.0
            
            # 깊이 필터링
            if self.config['processing']['enable_depth_filtering']:
                depth_meters = self._filter_depth(depth_meters)
            
            # 해상도 조정
            if self.target_size and depth_meters.shape != self.target_size[::-1]:
                depth_meters = cv2.resize(depth_meters, self.target_size, interpolation=cv2.INTER_NEAREST)
            
            return depth_meters
            
        except Exception as e:
            rospy.logerr(f"깊이 이미지 전처리 실패: {e}")
            return depth_image.astype(np.float32) / 1000.0
    
    def _normalize_colors(self, image: np.ndarray) -> np.ndarray:
        """
        색상 정규화
        
        Args:
            image: 입력 이미지 (BGR)
            
        Returns:
            정규화된 이미지 (RGB, 0-1 범위)
        """
        # BGR to RGB 변환
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 정규화 (0-1 범위)
        image_normalized = image_rgb.astype(np.float32) / 255.0
        
        return image_normalized
    
    def _filter_depth(self, depth_meters: np.ndarray) -> np.ndarray:
        """
        깊이 필터링
        
        Args:
            depth_meters: 깊이 이미지 (미터 단위)
            
        Returns:
            필터링된 깊이 이미지
        """
        # 무효한 깊이값 필터링
        depth_filtered = depth_meters.copy()
        
        # 0값을 NaN으로 변환
        depth_filtered[depth_filtered == 0] = np.nan
        
        # 범위 필터링
        depth_filtered[depth_filtered < self.depth_min] = np.nan
        depth_filtered[depth_filtered > self.depth_max] = np.nan
        
        # 통계적 이상치 제거 (선택적)
        if np.any(~np.isnan(depth_filtered)):
            mean_depth = np.nanmean(depth_filtered)
            std_depth = np.nanstd(depth_filtered)
            
            # 3시그마 규칙 적용
            lower_bound = mean_depth - 3 * std_depth
            upper_bound = mean_depth + 3 * std_depth
            
            depth_filtered[depth_filtered < lower_bound] = np.nan
            depth_filtered[depth_filtered > upper_bound] = np.nan
        
        return depth_filtered
    
    def create_camera_matrix(self, camera_config: Dict) -> np.ndarray:
        """
        카메라 매트릭스 생성
        
        Args:
            camera_config: 카메라 설정
            
        Returns:
            카메라 매트릭스 (3x3)
        """
        fx = camera_config['intrinsics']['fx']
        fy = camera_config['intrinsics']['fy']
        cx = camera_config['intrinsics']['cx']
        cy = camera_config['intrinsics']['cy']
        
        # 해상도 조정에 따른 스케일링
        if self.target_size:
            scale_x = self.target_size[0] / camera_config['intrinsics']['width']
            scale_y = self.target_size[1] / camera_config['intrinsics']['height']
            
            fx *= scale_x
            fy *= scale_y
            cx *= scale_x
            cy *= scale_y
        
        return np.array([
            [fx, 0, cx],
            [0, fy, cy],
            [0, 0, 1]
        ])
    
    def process_camera_data(self, camera_data: Dict) -> Dict:
        """
        카메라 데이터 전체 전처리
        
        Args:
            camera_data: 카메라 데이터 딕셔너리
                {
                    'image': np.ndarray,
                    'depth': np.ndarray,
                    'info': CameraInfo,
                    'camera_name': str
                }
            
        Returns:
            전처리된 데이터 딕셔너리
        """
        try:
            camera_name = camera_data['camera_name']
            
            # 이미지 전처리
            processed_image = self.preprocess_image(camera_data['image'], camera_name)
            
            # 깊이 전처리
            processed_depth = self.preprocess_depth(camera_data['depth'], camera_name)
            
            # 카메라 매트릭스 생성
            camera_config = self._get_camera_config(camera_name)
            if camera_config:
                camera_matrix = self.create_camera_matrix(camera_config)
            else:
                camera_matrix = None
            
            return {
                'image': processed_image,
                'depth': processed_depth,
                'camera_matrix': camera_matrix,
                'camera_name': camera_name,
                'timestamp': camera_data.get('timestamp', rospy.Time.now())
            }
            
        except Exception as e:
            rospy.logerr(f"카메라 데이터 전처리 실패: {e}")
            return camera_data
    
    def _get_camera_config(self, camera_name: str) -> Optional[Dict]:
        """카메라 설정 가져오기"""
        for camera in self.config['cameras']:
            if camera['name'] == camera_name:
                return camera
        return None
    
    def batch_process(self, sync_data: Dict) -> Dict:
        """
        동기화된 데이터 배치 전처리
        
        Args:
            sync_data: 동기화된 데이터
                {
                    'timestamp': float,
                    'cameras': {
                        'camera_name': {
                            'image': np.ndarray,
                            'depth': np.ndarray,
                            'info': CameraInfo
                        }
                    }
                }
            
        Returns:
            전처리된 배치 데이터
        """
        processed_batch = {
            'timestamp': sync_data['timestamp'],
            'cameras': {}
        }
        
        for camera_name, camera_data in sync_data['cameras'].items():
            camera_data['camera_name'] = camera_name
            processed_data = self.process_camera_data(camera_data)
            processed_batch['cameras'][camera_name] = processed_data
        
        return processed_batch
    
    def get_processing_stats(self) -> Dict:
        """전처리 통계 반환"""
        return {
            'target_size': self.target_size,
            'depth_range': (self.depth_min, self.depth_max),
            'undistortion_enabled': self.config['processing']['enable_undistortion'],
            'normalization_enabled': self.config['processing']['enable_normalization'],
            'depth_filtering_enabled': self.config['processing']['enable_depth_filtering']
        }

class ROSImagePreprocessor(ImagePreprocessor):
    """
    ROS 메시지 기반 이미지 전처리기
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.bridge = CvBridge()
    
    def process_image_msg(self, image_msg: Image, camera_name: str) -> np.ndarray:
        """
        ROS 이미지 메시지 전처리
        
        Args:
            image_msg: ROS 이미지 메시지
            camera_name: 카메라 이름
            
        Returns:
            전처리된 이미지
        """
        try:
            # ROS 메시지를 numpy 배열로 변환
            image = self.bridge.imgmsg_to_cv2(image_msg, "bgr8")
            
            # 전처리 수행
            return self.preprocess_image(image, camera_name)
            
        except Exception as e:
            rospy.logerr(f"ROS 이미지 메시지 전처리 실패: {e}")
            return None
    
    def process_depth_msg(self, depth_msg: Image, camera_name: str) -> np.ndarray:
        """
        ROS 깊이 메시지 전처리
        
        Args:
            depth_msg: ROS 깊이 메시지
            camera_name: 카메라 이름
            
        Returns:
            전처리된 깊이 이미지
        """
        try:
            # ROS 메시지를 numpy 배열로 변환
            depth_image = self.bridge.imgmsg_to_cv2(depth_msg, "16UC1")
            
            # 전처리 수행
            return self.preprocess_depth(depth_image, camera_name)
            
        except Exception as e:
            rospy.logerr(f"ROS 깊이 메시지 전처리 실패: {e}")
            return None
    
    def process_camera_info(self, info_msg: CameraInfo, camera_name: str) -> np.ndarray:
        """
        ROS 카메라 정보 메시지 처리
        
        Args:
            info_msg: ROS 카메라 정보 메시지
            camera_name: 카메라 이름
            
        Returns:
            카메라 매트릭스
        """
        try:
            # 카메라 매트릭스 추출
            K = np.array(info_msg.K).reshape(3, 3)
            
            # 해상도 조정에 따른 스케일링
            if self.target_size:
                scale_x = self.target_size[0] / info_msg.width
                scale_y = self.target_size[1] / info_msg.height
                
                K[0, 0] *= scale_x  # fx
                K[1, 1] *= scale_y  # fy
                K[0, 2] *= scale_x  # cx
                K[1, 2] *= scale_y  # cy
            
            return K
            
        except Exception as e:
            rospy.logerr(f"ROS 카메라 정보 처리 실패: {e}")
            return None
