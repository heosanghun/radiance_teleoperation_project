/*
 * Radiance Fields for Robotic Teleoperation - RViz NeRF 뷰어 플러그인
 * Phase 4: 시각화 시스템 구현
 * 
 * 이 플러그인은 RViz에서 NeRF 렌더링 결과를 실시간으로 표시합니다.
 */

#include <OGRE/OgreSceneNode.h>
#include <OGRE/OgreSceneManager.h>
#include <OGRE/OgreEntity.h>
#include <OGRE/OgreViewport.h>
#include <OGRE/OgreCamera.h>
#include <OGRE/OgreRenderWindow.h>

#include <rviz/display_context.h>
#include <rviz/frame_manager.h>
#include <rviz/properties/float_property.h>
#include <rviz/properties/bool_property.h>
#include <rviz/properties/int_property.h>
#include <rviz/properties/string_property.h>
#include <rviz/properties/ros_topic_property.h>
#include <rviz/viewport_mouse_event.h>
#include <rviz/load_resource.h>
#include <rviz/render_panel.h>
#include <rviz/visualization_manager.h>

#include <geometry_msgs/PoseStamped.h>
#include <sensor_msgs/Image.h>
#include <std_msgs/String.h>

#include "nerf_view_controller.h"

namespace rviz
{

NerfViewController::NerfViewController()
    : ViewController()
    , render_client_(nullptr)
    , current_pose_()
    , is_rendering_(false)
    , progressive_rendering_(true)
    , quality_level_(2)  // 0: 저해상도, 1: 중간, 2: 고해상도
{
}

NerfViewController::~NerfViewController()
{
    if (render_client_)
    {
        delete render_client_;
    }
}

void NerfViewController::onInitialize()
{
    ViewController::onInitialize();
    
    // ROS 서비스 클라이언트 초기화
    render_client_ = new ros::ServiceClient();
    
    // 속성 추가
    progressive_property_ = new BoolProperty("Progressive Rendering", true,
        "점진적 해상도 렌더링 활성화", this);
    
    quality_property_ = new IntProperty("Quality Level", 2,
        "렌더링 품질 레벨 (0-2)", this);
    quality_property_->setMin(0);
    quality_property_->setMax(2);
    
    render_topic_property_ = new RosTopicProperty("Render Topic", "/nerf/render_request",
        QString::fromStdString(ros::message_traits::datatype<geometry_msgs::PoseStamped>()),
        "NeRF 렌더링 요청 토픽", this);
    
    image_topic_property_ = new RosTopicProperty("Image Topic", "/nerf/rendered_image",
        QString::fromStdString(ros::message_traits::datatype<sensor_msgs::Image>()),
        "렌더링된 이미지 토픽", this);
    
    // 구독자 초기화
    image_sub_ = nh_.subscribe("/nerf/rendered_image", 1, 
        &NerfViewController::imageCallback, this);
    
    // 퍼블리셔 초기화
    pose_pub_ = nh_.advertise<geometry_msgs::PoseStamped>("/nerf/view_pose", 1);
    
    ROS_INFO("NeRF 뷰어 컨트롤러가 초기화되었습니다.");
}

void NerfViewController::onActivate()
{
    ViewController::onActivate();
    
    // 활성화 시 현재 카메라 포즈 발행
    publishCurrentPose();
    
    ROS_INFO("NeRF 뷰어 컨트롤러가 활성화되었습니다.");
}

void NerfViewController::onDeactivate()
{
    ViewController::onDeactivate();
    
    ROS_INFO("NeRF 뷰어 컨트롤러가 비활성화되었습니다.");
}

void NerfViewController::handleMouseEvent(ViewportMouseEvent& event)
{
    // 마우스 이벤트 처리
    if (event.type == QEvent::MouseMove)
    {
        // 카메라 이동
        if (event.left())
        {
            // 회전
            float yaw = -event.x_rel * 0.01f;
            float pitch = -event.y_rel * 0.01f;
            
            rotateCamera(yaw, pitch);
        }
        else if (event.middle())
        {
            // 이동
            float x = -event.x_rel * 0.01f;
            float y = event.y_rel * 0.01f;
            
            translateCamera(x, y);
        }
        
        // 포즈 업데이트 및 발행
        updateCameraPose();
        publishCurrentPose();
        
        // 렌더링 요청
        if (progressive_rendering_->getBool())
        {
            requestProgressiveRender();
        }
        else
        {
            requestRender();
        }
    }
    else if (event.type == QEvent::Wheel)
    {
        // 줌
        float zoom = event.wheel_delta > 0 ? 1.1f : 0.9f;
        zoomCamera(zoom);
        
        updateCameraPose();
        publishCurrentPose();
        requestRender();
    }
    
    event.ignore();
}

void NerfViewController::lookAt(const Ogre::Vector3& point)
{
    // 특정 점을 바라보도록 카메라 설정
    Ogre::Vector3 direction = point - camera_->getPosition();
    direction.normalise();
    
    // 방향 벡터를 쿼터니언으로 변환
    Ogre::Quaternion orientation;
    orientation.FromVectors(Ogre::Vector3::UNIT_Z, direction);
    
    camera_->setOrientation(orientation);
    
    updateCameraPose();
    publishCurrentPose();
    requestRender();
}

void NerfViewController::reset()
{
    // 카메라 위치 및 방향 초기화
    camera_->setPosition(Ogre::Vector3(0, 0, 5));
    camera_->setOrientation(Ogre::Quaternion::IDENTITY);
    
    updateCameraPose();
    publishCurrentPose();
    requestRender();
    
    ROS_INFO("NeRF 뷰어가 초기화되었습니다.");
}

void NerfViewController::rotateCamera(float yaw, float pitch)
{
    // 카메라 회전
    Ogre::Quaternion yaw_quat(Ogre::Radian(yaw), Ogre::Vector3::UNIT_Y);
    Ogre::Quaternion pitch_quat(Ogre::Radian(pitch), Ogre::Vector3::UNIT_X);
    
    camera_->setOrientation(camera_->getOrientation() * yaw_quat * pitch_quat);
}

void NerfViewController::translateCamera(float x, float y)
{
    // 카메라 이동
    Ogre::Vector3 right = camera_->getOrientation() * Ogre::Vector3::UNIT_X;
    Ogre::Vector3 up = camera_->getOrientation() * Ogre::Vector3::UNIT_Y;
    
    Ogre::Vector3 translation = right * x + up * y;
    camera_->setPosition(camera_->getPosition() + translation);
}

void NerfViewController::zoomCamera(float factor)
{
    // 카메라 줌
    Ogre::Vector3 forward = camera_->getOrientation() * Ogre::Vector3::NEGATIVE_UNIT_Z;
    Ogre::Vector3 new_position = camera_->getPosition() + forward * (factor - 1.0f) * 0.5f;
    
    camera_->setPosition(new_position);
}

void NerfViewController::updateCameraPose()
{
    // Ogre 카메라 포즈를 ROS 메시지로 변환
    Ogre::Vector3 position = camera_->getPosition();
    Ogre::Quaternion orientation = camera_->getOrientation();
    
    current_pose_.header.stamp = ros::Time::now();
    current_pose_.header.frame_id = "world";
    
    current_pose_.pose.position.x = position.x;
    current_pose_.pose.position.y = position.y;
    current_pose_.pose.position.z = position.z;
    
    current_pose_.pose.orientation.x = orientation.x;
    current_pose_.pose.orientation.y = orientation.y;
    current_pose_.pose.orientation.z = orientation.z;
    current_pose_.pose.orientation.w = orientation.w;
}

void NerfViewController::publishCurrentPose()
{
    // 현재 카메라 포즈 발행
    pose_pub_.publish(current_pose_);
}

void NerfViewController::requestRender()
{
    if (is_rendering_)
    {
        return;  // 이미 렌더링 중
    }
    
    // 렌더링 요청 메시지 생성
    geometry_msgs::PoseStamped render_request = current_pose_;
    render_request.header.frame_id = "world";
    
    // 서비스 호출 또는 토픽 발행
    // 여기서는 토픽 발행으로 구현
    static ros::Publisher render_pub = nh_.advertise<geometry_msgs::PoseStamped>(
        render_topic_property_->getTopicStd(), 1);
    
    render_pub.publish(render_request);
    
    is_rendering_ = true;
    
    // 렌더링 완료 대기 타이머 설정
    render_timer_ = nh_.createTimer(ros::Duration(0.1), 
        &NerfViewController::renderTimeoutCallback, this, true);
}

void NerfViewController::requestProgressiveRender()
{
    // 점진적 렌더링 요청
    int current_quality = quality_property_->getInt();
    
    // 저해상도부터 시작하여 점진적으로 품질 향상
    for (int quality = 0; quality <= current_quality; ++quality)
    {
        // 품질별 렌더링 요청
        geometry_msgs::PoseStamped render_request = current_pose_;
        render_request.header.frame_id = "world";
        
        // 품질 정보를 메시지에 포함 (실제로는 별도 필드 필요)
        static ros::Publisher render_pub = nh_.advertise<geometry_msgs::PoseStamped>(
            render_topic_property_->getTopicStd(), 1);
        
        render_pub.publish(render_request);
        
        // 짧은 지연
        ros::Duration(0.05).sleep();
    }
}

void NerfViewController::imageCallback(const sensor_msgs::Image::ConstPtr& msg)
{
    // 렌더링된 이미지 수신 처리
    is_rendering_ = false;
    
    // 이미지를 Ogre 텍스처로 변환하여 표시
    updateDisplayedImage(msg);
    
    ROS_DEBUG("렌더링된 이미지를 수신했습니다.");
}

void NerfViewController::updateDisplayedImage(const sensor_msgs::Image::ConstPtr& msg)
{
    // ROS 이미지를 Ogre 텍스처로 변환
    // 이 부분은 실제 구현에서 더 복잡한 이미지 처리 로직이 필요
    
    // 간단한 예시: 이미지 데이터를 텍스처로 변환
    if (msg->encoding == "rgb8" || msg->encoding == "bgr8")
    {
        // 이미지 데이터를 Ogre 텍스처로 변환하는 로직
        // 실제 구현에서는 cv_bridge 등을 사용하여 변환
        
        ROS_DEBUG("이미지 텍스처가 업데이트되었습니다.");
    }
}

void NerfViewController::renderTimeoutCallback(const ros::TimerEvent& event)
{
    // 렌더링 타임아웃 처리
    if (is_rendering_)
    {
        is_rendering_ = false;
        ROS_WARN("렌더링 요청이 타임아웃되었습니다.");
    }
}

void NerfViewController::sendRenderRequest(const geometry_msgs::PoseStamped& pose)
{
    // 특정 포즈에 대한 렌더링 요청
    current_pose_ = pose;
    
    if (progressive_rendering_->getBool())
    {
        requestProgressiveRender();
    }
    else
    {
        requestRender();
    }
}

void NerfViewController::update(float dt, float ros_dt)
{
    // 주기적 업데이트
    ViewController::update(dt, ros_dt);
    
    // 카메라 포즈가 변경되었는지 확인
    static Ogre::Vector3 last_position = camera_->getPosition();
    static Ogre::Quaternion last_orientation = camera_->getOrientation();
    
    Ogre::Vector3 current_position = camera_->getPosition();
    Ogre::Quaternion current_orientation = camera_->getOrientation();
    
    if (last_position != current_position || last_orientation != current_orientation)
    {
        updateCameraPose();
        publishCurrentPose();
        
        last_position = current_position;
        last_orientation = current_orientation;
    }
}

} // namespace rviz

#include <pluginlib/class_list_macros.h>
PLUGINLIB_EXPORT_CLASS(rviz::NerfViewController, rviz::ViewController)
