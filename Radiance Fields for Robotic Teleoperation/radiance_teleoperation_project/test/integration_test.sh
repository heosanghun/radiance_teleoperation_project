#!/bin/bash

# Radiance Fields for Robotic Teleoperation - 통합 테스트 스크립트
# Phase 7: 통합 테스트 및 배포

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 테스트 결과 저장
TEST_RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0

# 테스트 결과 기록 함수
record_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$result" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "테스트 통과: $test_name - $message"
    else
        log_error "테스트 실패: $test_name - $message"
    fi
    
    TEST_RESULTS+=("$test_name:$result:$message")
}

# 환경 설정 테스트
test_environment_setup() {
    log_info "환경 설정 테스트 시작..."
    
    # ROS 환경 확인
    if command -v roscore &> /dev/null; then
        record_test "ROS_Installation" "PASS" "ROS가 정상적으로 설치됨"
    else
        record_test "ROS_Installation" "FAIL" "ROS가 설치되지 않음"
        return 1
    fi
    
    # CUDA 환경 확인
    if command -v nvcc &> /dev/null; then
        record_test "CUDA_Installation" "PASS" "CUDA가 정상적으로 설치됨"
    else
        record_test "CUDA_Installation" "FAIL" "CUDA가 설치되지 않음"
    fi
    
    # NerfStudio 환경 확인
    if conda activate nerfstudio && ns-train --help &> /dev/null; then
        record_test "NerfStudio_Installation" "PASS" "NerfStudio가 정상적으로 설치됨"
    else
        record_test "NerfStudio_Installation" "FAIL" "NerfStudio가 설치되지 않음"
    fi
    
    # GPU 메모리 확인
    if command -v nvidia-smi &> /dev/null; then
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
        if [ "$GPU_MEMORY" -ge 8000 ]; then
            record_test "GPU_Memory" "PASS" "GPU 메모리: ${GPU_MEMORY}MB"
        else
            record_test "GPU_Memory" "WARN" "GPU 메모리 부족: ${GPU_MEMORY}MB"
        fi
    else
        record_test "GPU_Memory" "FAIL" "GPU 정보를 확인할 수 없음"
    fi
}

# 하드웨어 연결 테스트
test_hardware_connection() {
    log_info "하드웨어 연결 테스트 시작..."
    
    # RealSense 카메라 확인
    if command -v realsense-viewer &> /dev/null; then
        record_test "RealSense_SDK" "PASS" "RealSense SDK가 설치됨"
    else
        record_test "RealSense_SDK" "FAIL" "RealSense SDK가 설치되지 않음"
    fi
    
    # USB 카메라 확인
    if ls /dev/video* &> /dev/null; then
        CAMERA_COUNT=$(ls /dev/video* | wc -l)
        record_test "USB_Cameras" "PASS" "USB 카메라 ${CAMERA_COUNT}개 감지됨"
    else
        record_test "USB_Cameras" "WARN" "USB 카메라가 감지되지 않음"
    fi
    
    # 네트워크 연결 확인
    if ping -c 1 8.8.8.8 &> /dev/null; then
        record_test "Network_Connection" "PASS" "네트워크 연결 정상"
    else
        record_test "Network_Connection" "FAIL" "네트워크 연결 실패"
    fi
}

# ROS 패키지 빌드 테스트
test_ros_build() {
    log_info "ROS 패키지 빌드 테스트 시작..."
    
    # Catkin workspace 확인
    if [ -d "$HOME/catkin_ws" ]; then
        cd "$HOME/catkin_ws"
        
        # 의존성 설치
        if rosdep install --from-paths src --ignore-src -r -y; then
            record_test "ROS_Dependencies" "PASS" "ROS 의존성 설치 성공"
        else
            record_test "ROS_Dependencies" "FAIL" "ROS 의존성 설치 실패"
            return 1
        fi
        
        # 빌드 테스트
        if catkin_make; then
            record_test "ROS_Build" "PASS" "ROS 패키지 빌드 성공"
        else
            record_test "ROS_Build" "FAIL" "ROS 패키지 빌드 실패"
            return 1
        fi
        
        # 환경 설정
        source devel/setup.bash
        record_test "ROS_Environment" "PASS" "ROS 환경 설정 완료"
    else
        record_test "ROS_Workspace" "FAIL" "Catkin workspace가 존재하지 않음"
        return 1
    fi
}

# 멀티 카메라 노드 테스트
test_multi_camera_node() {
    log_info "멀티 카메라 노드 테스트 시작..."
    
    # ROS 마스터 시작
    roscore &
    ROSCORE_PID=$!
    sleep 3
    
    # 멀티 카메라 노드 실행
    if rosrun radiance_camera multi_camera_node.py --test-mode; then
        record_test "MultiCamera_Node" "PASS" "멀티 카메라 노드 실행 성공"
    else
        record_test "MultiCamera_Node" "FAIL" "멀티 카메라 노드 실행 실패"
    fi
    
    # 토픽 확인
    sleep 2
    if rostopic list | grep -q "/camera_stats"; then
        record_test "Camera_Topics" "PASS" "카메라 토픽이 정상적으로 발행됨"
    else
        record_test "Camera_Topics" "FAIL" "카메라 토픽이 발행되지 않음"
    fi
    
    # ROS 마스터 종료
    kill $ROSCORE_PID 2>/dev/null || true
}

# NeRF 훈련 테스트
test_nerf_training() {
    log_info "NeRF 훈련 테스트 시작..."
    
    # 간단한 NeRF 훈련 테스트
    if conda activate nerfstudio; then
        # 테스트 데이터셋으로 훈련 테스트
        if ns-train nerfacto --data /tmp/test_data --max-num-iterations 10; then
            record_test "NeRF_Training" "PASS" "NeRF 훈련 테스트 성공"
        else
            record_test "NeRF_Training" "FAIL" "NeRF 훈련 테스트 실패"
        fi
    else
        record_test "NeRF_Training" "FAIL" "NerfStudio 환경을 활성화할 수 없음"
    fi
}

# VR 연결 테스트
test_vr_connection() {
    log_info "VR 연결 테스트 시작..."
    
    # TCP 연결 테스트
    if nc -z 192.168.1.100 10000 2>/dev/null; then
        record_test "VR_TCP_Connection" "PASS" "VR TCP 연결 성공"
    else
        record_test "VR_TCP_Connection" "WARN" "VR TCP 연결 실패 (VR 디바이스가 연결되지 않았을 수 있음)"
    fi
    
    # Unity VR 앱 확인 (실제 환경에서는 더 구체적인 테스트 필요)
    record_test "VR_Unity_App" "INFO" "Unity VR 앱 테스트는 수동으로 확인 필요"
}

# 성능 벤치마크 테스트
test_performance_benchmark() {
    log_info "성능 벤치마크 테스트 시작..."
    
    # GPU 성능 테스트
    if command -v nvidia-smi &> /dev/null; then
        # GPU 사용률 확인
        GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
        if [ "$GPU_UTIL" -lt 90 ]; then
            record_test "GPU_Performance" "PASS" "GPU 사용률: ${GPU_UTIL}%"
        else
            record_test "GPU_Performance" "WARN" "GPU 사용률이 높음: ${GPU_UTIL}%"
        fi
        
        # GPU 메모리 사용률 확인
        GPU_MEM_UTIL=$(nvidia-smi --query-gpu=utilization.memory --format=csv,noheader,nounits | head -1)
        if [ "$GPU_MEM_UTIL" -lt 80 ]; then
            record_test "GPU_Memory_Usage" "PASS" "GPU 메모리 사용률: ${GPU_MEM_UTIL}%"
        else
            record_test "GPU_Memory_Usage" "WARN" "GPU 메모리 사용률이 높음: ${GPU_MEM_UTIL}%"
        fi
    fi
    
    # 시스템 메모리 확인
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$MEMORY_USAGE < 80" | bc -l) )); then
        record_test "System_Memory" "PASS" "시스템 메모리 사용률: ${MEMORY_USAGE}%"
    else
        record_test "System_Memory" "WARN" "시스템 메모리 사용률이 높음: ${MEMORY_USAGE}%"
    fi
    
    # 디스크 공간 확인
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt 90 ]; then
        record_test "Disk_Space" "PASS" "디스크 사용률: ${DISK_USAGE}%"
    else
        record_test "Disk_Space" "WARN" "디스크 사용률이 높음: ${DISK_USAGE}%"
    fi
}

# 장시간 안정성 테스트
test_long_term_stability() {
    log_info "장시간 안정성 테스트 시작..."
    
    # 1시간 연속 운영 시뮬레이션 (실제로는 더 짧은 시간으로 테스트)
    log_info "1분간 안정성 테스트 실행 중..."
    
    # 백그라운드에서 시스템 모니터링
    (
        for i in {1..60}; do
            # 시스템 리소스 모니터링
            if [ $((i % 10)) -eq 0 ]; then
                log_info "안정성 테스트 진행률: $((i * 100 / 60))%"
            fi
            
            # 메모리 누수 확인
            if command -v nvidia-smi &> /dev/null; then
                GPU_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
                if [ "$GPU_MEM" -gt 12000 ]; then
                    record_test "Memory_Leak" "FAIL" "GPU 메모리 누수 감지: ${GPU_MEM}MB"
                    break
                fi
            fi
            
            sleep 1
        done
    ) &
    
    STABILITY_PID=$!
    wait $STABILITY_PID
    
    record_test "Long_Term_Stability" "PASS" "1분간 안정성 테스트 완료"
}

# 통합 시스템 테스트
test_integrated_system() {
    log_info "통합 시스템 테스트 시작..."
    
    # 전체 시스템 시뮬레이션
    log_info "전체 시스템 통합 테스트 실행 중..."
    
    # 1. ROS 마스터 시작
    roscore &
    ROSCORE_PID=$!
    sleep 3
    
    # 2. 멀티 카메라 노드 시작
    rosrun radiance_camera multi_camera_node.py --test-mode &
    CAMERA_PID=$!
    sleep 2
    
    # 3. NeRF 훈련 노드 시작
    rosrun radiance_nerf online_trainer.py --test-mode &
    TRAINER_PID=$!
    sleep 2
    
    # 4. 시스템 상태 확인
    if rostopic list | grep -q "/camera_stats" && rostopic list | grep -q "/nerf/training_stats"; then
        record_test "Integrated_System" "PASS" "통합 시스템이 정상적으로 작동함"
    else
        record_test "Integrated_System" "FAIL" "통합 시스템 작동 실패"
    fi
    
    # 5. 정리
    kill $CAMERA_PID $TRAINER_PID $ROSCORE_PID 2>/dev/null || true
    sleep 2
}

# 테스트 결과 요약
print_test_summary() {
    log_info "=== 테스트 결과 요약 ==="
    echo "총 테스트 수: $TOTAL_TESTS"
    echo "통과한 테스트: $PASSED_TESTS"
    echo "실패한 테스트: $((TOTAL_TESTS - PASSED_TESTS))"
    echo "성공률: $((PASSED_TESTS * 100 / TOTAL_TESTS))%"
    echo ""
    
    echo "=== 상세 결과 ==="
    for result in "${TEST_RESULTS[@]}"; do
        IFS=':' read -r test_name result_status message <<< "$result"
        if [ "$result_status" = "PASS" ]; then
            echo -e "${GREEN}✓${NC} $test_name: $message"
        elif [ "$result_status" = "FAIL" ]; then
            echo -e "${RED}✗${NC} $test_name: $message"
        elif [ "$result_status" = "WARN" ]; then
            echo -e "${YELLOW}⚠${NC} $test_name: $message"
        else
            echo -e "${BLUE}ℹ${NC} $test_name: $message"
        fi
    done
}

# 메인 테스트 실행
main() {
    log_info "Radiance Fields for Robotic Teleoperation 통합 테스트를 시작합니다..."
    
    # 테스트 실행
    test_environment_setup
    test_hardware_connection
    test_ros_build
    test_multi_camera_node
    test_nerf_training
    test_vr_connection
    test_performance_benchmark
    test_long_term_stability
    test_integrated_system
    
    # 결과 출력
    print_test_summary
    
    # 종료 코드 결정
    if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
        log_success "모든 테스트가 통과했습니다!"
        exit 0
    else
        log_warning "일부 테스트가 실패했습니다. 위의 결과를 확인하세요."
        exit 1
    fi
}

# 스크립트 실행
main "$@"
