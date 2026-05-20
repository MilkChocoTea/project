#!/bin/bash
# ============================================================
# 機械手臂控制系統 啟動腳本
# 用法：
#   ./start.sh           啟動主程式
#   ./start.sh --install 安裝環境
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_PY="$SCRIPT_DIR/main.py"

# 取得實際使用者資訊（sudo 執行時也能正確取得）
REAL_UID=$(id -u "${SUDO_USER:-$USER}")
REAL_USER="${SUDO_USER:-$USER}"

# ── 顏色輸出 ──────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
ok()   { echo -e "${GREEN}[v]${NC} $1"; }
info() { echo -e "${YELLOW}[*]${NC} $1"; }
err()  { echo -e "${RED}[!]${NC} $1"; }

# ── 檢查 main.py ──────────────────────────────────
if [ ! -f "$MAIN_PY" ]; then
    err "找不到 $MAIN_PY"
    err "請確認 start.sh 與 main.py 放在同一個資料夾"
    exit 1
fi

# ════════════════════════════════════════════════════
# 安裝模式
# ════════════════════════════════════════════════════
if [ "$1" == "--install" ]; then

    if [ "$EUID" -ne 0 ]; then
        err "安裝模式需要 sudo 權限，請執行："
        echo "    sudo ./start.sh --install"
        exit 1
    fi

    echo "============================================"
    echo "  機械手臂控制系統 — 環境安裝"
    echo "============================================"

    # ── 1. apt 套件 ───────────────────────────────
    echo ""
    info "檢查並安裝系統套件..."
    PACKAGES=(
        python3-pyqt5
        python3-smbus
        i2c-tools
        postgresql
        postgresql-client
        python3-psycopg2
        python3-opencv
        python3-numpy
        python3-requests
        libcamera-apps
        gstreamer1.0-libcamera
        gstreamer1.0-tools
        gstreamer1.0-plugins-base
        gstreamer1.0-plugins-good
    )

    apt update -qq

    for pkg in "${PACKAGES[@]}"; do
        if dpkg -l "$pkg" &>/dev/null; then
            ok "$pkg 已安裝"
        else
            info "正在安裝 $pkg ..."
            if apt install -y "$pkg" &>/dev/null; then
                ok "$pkg 安裝完成"
            else
                err "$pkg 安裝失敗（略過）"
            fi
        fi
    done

    # ── 2. PostgreSQL 服務 ────────────────────────
    echo ""
    info "檢查 PostgreSQL 服務..."
    if systemctl start postgresql && systemctl enable postgresql; then
        ok "PostgreSQL 服務已啟動並設為開機自動執行"
    else
        err "無法啟動 PostgreSQL，請手動檢查"
    fi

    # ── 3. I2C 啟用確認 ───────────────────────────
    echo ""
    info "檢查 I2C 設定..."
    if grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null || \
       grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null; then
        ok "I2C 已啟用"
    else
        err "I2C 未啟用，請執行 sudo raspi-config → Interface Options → I2C → Enable"
    fi

    # ── 4. 資料庫初始化 ───────────────────────────
    echo ""
    info "初始化資料庫..."
    sudo -u "$REAL_USER" \
        DISPLAY="${DISPLAY:-:0}" \
        XDG_RUNTIME_DIR="/run/user/$REAL_UID" \
        python3 -c "import setsql; setsql.check_user_exists(); setsql.initialize_all()" 2>&1 \
        && ok "資料庫初始化完成" \
        || err "資料庫初始化失敗，啟動程式時會再次嘗試"

    echo ""
    echo "============================================"
    ok "安裝完成！執行 ./start.sh 啟動"
    echo "============================================"
    exit 0
fi

# ════════════════════════════════════════════════════
# 啟動模式
# ════════════════════════════════════════════════════
echo "[ 機械手臂控制系統 ] 啟動中..."

sudo -E \
    DISPLAY="${DISPLAY:-:0}" \
    XDG_RUNTIME_DIR="/run/user/$REAL_UID" \
    QT_LOGGING_RULES="*.warning=false" \
    python3 "$MAIN_PY"