#!/usr/bin/env python3
"""
combined_nodes.launch.py
ZED-F9P Rover + NTRIP 클라이언트 통합 런치 파일

가이드(ArduSimple Jazzy) 대비 개선 사항:
  [수정] tmode3: 1(Base) → 0(Rover)          — 가이드 최대 오류
  [수정] baudrate: 9600 → 460800             — RTCM+NavPVT 병목 해소
  [추가] dynamic_model: 4 (automotive)       — 멀티패스 내성 향상
  [추가] rate: 10Hz                          — 로봇 응용 위치 갱신
  [추가] GNSS 성좌: GPS+Galileo+GLONASS      — 위성 수 15~20개 확보
  [추가] hAcc 필터 노드                       — sv=0 점프 에포크 제거
  [추가] 한국 NGII VRS NTRIP 설정 예시       — u-blox PointPerfect 대안
"""

import os

from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable, DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # ═══════════════════════════════════════════════════════
    # Launch Arguments (실행 시 오버라이드 가능)
    # 예: ros2 launch combined_rtk combined_nodes.launch.py ntrip_host:=vrs.ngii.go.kr
    # ═══════════════════════════════════════════════════════
    ntrip_host_arg = DeclareLaunchArgument(
        'ntrip_host',
        # [개선] 한국 국토지리정보원 VRS NTRIP (기준점 간격 좁아 RTK 수렴 빠름)
        # 대안: 'ppntrip.services.u-blox.com' (u-blox PointPerfect)
        default_value='rts1.ngii.go.kr',
        description='NTRIP caster hostname'
    )
    ntrip_port_arg = DeclareLaunchArgument(
        'ntrip_port',
        default_value='2101',
        description='NTRIP caster port'
    )
    ntrip_mountpoint_arg = DeclareLaunchArgument(
        'ntrip_mountpoint',
        # NGII VRS 마운트포인트: MSM7 형식 권장 (MSM4보다 반송파 정수 수렴 빠름)
        # 마운트포인트 목록: http://vrs.ngii.go.kr:2101
        default_value='VRS-RTCM34',       # ← 실제 마운트포인트로 변경 필요
        description='NTRIP mountpoint'
    )
    ntrip_user_arg = DeclareLaunchArgument(
        'ntrip_user',
        default_value='zero0023001',      # ← 실제 계정으로 변경 필요
        description='NTRIP username'
    )
    ntrip_pass_arg = DeclareLaunchArgument(
        'ntrip_password',
        default_value='ngii',      # ← 실제 비밀번호로 변경 필요
        description='NTRIP password'
    )
    hacc_limit_arg = DeclareLaunchArgument(
        'hacc_limit',
        default_value='3.0',               # hAcc 필터 임계값 (m), 초과 시 /fix 발행 차단
        description='hAcc threshold for GPS filter (meters)'
    )

    # ═══════════════════════════════════════════════════════
    # 설정 파일 경로
    # ═══════════════════════════════════════════════════════
    # zed_f9p.yaml을 combined_rtk 패키지 내 config/에 복사해두면 아래 경로 사용
    # 없으면 직접 경로 지정: '/home/user/ros2_ws/config/zed_f9p.yaml'
    config_file = PathJoinSubstitution([
        FindPackageShare('combined_rtk'),
        'config',
        'zed_f9p.yaml'
    ])

    # ═══════════════════════════════════════════════════════
    # [Node 1] ublox_gps_node — ZED-F9P 드라이버
    # ═══════════════════════════════════════════════════════
    ublox_node = Node(
        package='ublox_gps',
        executable='ublox_gps_node',
        name='ublox_gps_node',
        output='screen',
        parameters=[
            config_file,          # zed_f9p.yaml 설정 파일 로드
            {
                # yaml 파일 값을 런타임에 오버라이드하고 싶을 때 여기에 추가
                # 예: 'rate.meas': 200  (5Hz로 낮추기)
            }
        ],
        remappings=[
            # [중요] ntrip_client가 발행하는 /rtcm을
            # ublox 드라이버의 RTCM 입력 포트로 연결
            # 이 remapping이 없으면 RTCM이 수신기로 주입되지 않음
            ('/rtcm', '/rtcm'),
        ]
    )

    # ═══════════════════════════════════════════════════════
    # [Node 2] ntrip_client — RTCM 보정 데이터 수신
    # ═══════════════════════════════════════════════════════
    set_ntrip_debug = SetEnvironmentVariable(
        name='NTRIP_CLIENT_DEBUG',
        value='false'
    )

    ntrip_node = Node(
        package='ntrip_client',
        executable='ntrip_ros.py',
        name='ntrip_client',
        output='screen',
        parameters=[{
            'host':             LaunchConfiguration('ntrip_host'),
            'port':             LaunchConfiguration('ntrip_port'),
            'mountpoint':       LaunchConfiguration('ntrip_mountpoint'),
            'authenticate':     True,
            'username':         LaunchConfiguration('ntrip_user'),
            'password':         LaunchConfiguration('ntrip_password'),
            'ntrip_version':    'None',
            'ssl':              False,
            'cert':             'None',
            'key':              'None',
            'ca_cert':          'None',

            # RTCM 메시지 포맷 — rtcm_msgs 패키지 사용 (bag과 동일)
            'rtcm_message_package': 'rtcm_msgs',
            'rtcm_frame_id':    'gps',

            # NMEA GGA 전송 (VRS 서비스는 현재 위치 정보가 필요)
            # ntrip_client가 /nmea를 구독하여 caster에 GGA 전송
            'nmea_max_length':  128,
            'nmea_min_length':  3,

            # 재연결 설정
            'reconnect_attempt_max':      10,
            'reconnect_attempt_wait_seconds': -1,
            'rtcm_timeout_seconds':       3,
        }],
        remappings=[
            # VRS는 현재 위치(GGA)를 caster에 보내야 보정 계산 가능
            # /nmea → ublox_gps_node가 발행하는 /nmea 연결
            ('/nmea', '/nmea'),
            # RTCM 출력 토픽 (ublox_node가 구독)
            ('/rtcm', '/rtcm'),
            # fix 리매핑 (가이드와 동일)
            ('/fix', '/ublox_gps_node/fix'),
        ]
    )

    # ═══════════════════════════════════════════════════════
    # [Node 3] gps_filter_node — hAcc/sv 품질 필터
    # ═══════════════════════════════════════════════════════
    # [추가] 가이드에 없음
    # bag 분석에서 확인된 sv=0, PDOP=99 에포크(→100m+ 점프)를 필터링
    # /ublox_gps_node/fix_raw 를 구독하여 품질 기준 통과한 것만 /ublox_gps_node/fix 재발행
    #
    # 이 노드는 별도 Python 스크립트로 작성 필요 (gps_filter.py 참조)
    # 당장 필터 노드가 없으면 아래 블록을 주석 처리하고
    # ublox_node의 토픽명을 직접 /ublox_gps_node/fix로 쓰면 됨
    gps_filter_node = Node(
        package='combined_rtk',
        executable='gps_filter',
        name='gps_filter',
        output='screen',
        parameters=[{
            'hacc_limit':   LaunchConfiguration('hacc_limit'),  # m
            'min_svs':      4,      # 이 미만이면 발행 차단
            'max_pdop':     8.0,    # 이 초과면 발행 차단
        }],
        remappings=[
            ('fix_in',  '/ublox_gps_node/navpvt'),   # NavPVT 구독 (hAcc, sv, carr_soln 포함)
            ('fix_out', '/ublox_gps_node/fix_filtered'),  # 필터링된 fix 발행
        ]
    )

    # ═══════════════════════════════════════════════════════
    # Launch 시작 로그
    # ═══════════════════════════════════════════════════════
    log_start = LogInfo(msg=[
        '\n',
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n',
        '  ZED-F9P RTK 런치 시작\n',
        '  NTRIP Host : ', LaunchConfiguration('ntrip_host'), '\n',
        '  Mountpoint : ', LaunchConfiguration('ntrip_mountpoint'), '\n',
        '  hAcc 필터  : ', LaunchConfiguration('hacc_limit'), ' m\n',
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
    ])

    return LaunchDescription([
        # Launch Arguments
        ntrip_host_arg,
        ntrip_port_arg,
        ntrip_mountpoint_arg,
        ntrip_user_arg,
        ntrip_pass_arg,
        hacc_limit_arg,

        # 시작 로그
        log_start,

        # 환경변수
        set_ntrip_debug,

        # 노드 시작 순서: ublox → ntrip → filter
        ublox_node,
        ntrip_node,
        # gps_filter_node,  # gps_filter.py 작성 후 주석 해제
    ])
