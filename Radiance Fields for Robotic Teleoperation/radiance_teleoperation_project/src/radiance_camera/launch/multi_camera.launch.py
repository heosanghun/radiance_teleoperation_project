#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get the package directory
    pkg_dir = get_package_share_directory('radiance_camera')
    
    # Launch arguments
    config_file = LaunchConfiguration('config_file')
    
    # Declare launch arguments
    declare_config_file_cmd = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_dir, 'config', 'camera_config.yaml'),
        description='Path to camera configuration file'
    )
    
    # Multi camera node
    multi_camera_node = Node(
        package='radiance_camera',
        executable='multi_camera_node',
        name='multi_camera_node',
        output='screen',
        parameters=[config_file],
        remappings=[
            ('/front_camera/image_raw', '/camera/front/image_raw'),
            ('/front_camera/depth_raw', '/camera/front/depth_raw'),
            ('/front_camera/camera_info', '/camera/front/camera_info'),
            ('/rear_camera/image_raw', '/camera/rear/image_raw'),
            ('/rear_camera/depth_raw', '/camera/rear/depth_raw'),
            ('/rear_camera/camera_info', '/camera/rear/camera_info'),
            ('/side_camera/image_raw', '/camera/side/image_raw'),
            ('/side_camera/depth_raw', '/camera/side/depth_raw'),
            ('/side_camera/camera_info', '/camera/side/camera_info'),
        ]
    )
    
    # Image preprocessor node
    image_preprocessor_node = Node(
        package='radiance_camera',
        executable='image_preprocessor',
        name='image_preprocessor',
        output='screen',
        parameters=[config_file],
        remappings=[
            ('/camera/front/image_raw', '/camera/front/processed/image_raw'),
            ('/camera/front/depth_raw', '/camera/front/processed/depth_raw'),
            ('/camera/rear/image_raw', '/camera/rear/processed/image_raw'),
            ('/camera/rear/depth_raw', '/camera/rear/processed/depth_raw'),
            ('/camera/side/image_raw', '/camera/side/processed/image_raw'),
            ('/camera/side/depth_raw', '/camera/side/processed/depth_raw'),
        ]
    )
    
    # TF broadcaster for camera frames
    tf_broadcaster = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_tf_broadcaster',
        arguments=[
            '0', '0', '0', '0', '0', '0',
            'world', 'front_camera_color_optical_frame'
        ]
    )
    
    return LaunchDescription([
        declare_config_file_cmd,
        multi_camera_node,
        image_preprocessor_node,
        tf_broadcaster,
    ])
