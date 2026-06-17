#!/bin/bash

# ArduSimple udev rules 설치 및 적용 스크립트
# 이 스크립트는 50-ardusimple.rules 파일을 시스템에 설치하고 udev daemon을 리로드합니다.

set -e  # 에러 발생 시 종료

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_FILE="$SCRIPT_DIR/50-ardusimple.rules"
UDEV_RULES_DIR="/etc/udev/rules.d"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== ArduSimple udev rules 설치 시작 ===${NC}"

# rules 파일 존재 확인
if [ ! -f "$RULES_FILE" ]; then
    echo -e "${RED}오류: rules 파일을 찾을 수 없습니다: $RULES_FILE${NC}"
    exit 1
fi

# 관리자 권한 확인
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}오류: 이 스크립트는 root 권한으로 실행해야 합니다.${NC}"
    echo "다시 실행해주세요: sudo $0"
    exit 1
fi

# 1. rules 파일 복사
echo -e "${YELLOW}1. udev rules 파일을 $UDEV_RULES_DIR로 복사 중...${NC}"
cp "$RULES_FILE" "$UDEV_RULES_DIR/"
chmod 644 "$UDEV_RULES_DIR/50-ardusimple.rules"
echo -e "${GREEN}✓ 파일 복사 완료${NC}"

# 2. udev 데이터베이스 리로드
echo -e "${YELLOW}2. udev daemon 리로드 중...${NC}"
udevadm control --reload-rules
udevadm trigger
echo -e "${GREEN}✓ udev daemon 리로드 완료${NC}"

# 3. 규칙 적용 확인
echo -e "${YELLOW}3. 설치 확인 중...${NC}"
if [ -f "$UDEV_RULES_DIR/50-ardusimple.rules" ]; then
    echo -e "${GREEN}✓ udev rules 파일이 성공적으로 설치되었습니다.${NC}"
    echo -e "${GREEN}✓ ArduSimple 장치 규칙:${NC}"
    cat "$UDEV_RULES_DIR/50-ardusimple.rules" | grep -v '^#'
else
    echo -e "${RED}✗ 파일 설치 확인 실패${NC}"
    exit 1
fi

echo -e "${GREEN}=== 설치 완료 ===${NC}"
echo ""
echo "다음 단계:"
echo "1. ArduSimple 장치를 USB로 연결하세요."
echo "2. 다음 명령으로 장치를 확인할 수 있습니다:"
echo "   ls -la /dev/tty_Ardusimple"
echo "   또는"
echo "   dmesg | tail -20"
