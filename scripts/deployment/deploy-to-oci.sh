#!/bin/bash
# OCI 部署腳本

set -e

# 配置
OCI_HOST="140.245.126.35"
OCI_USER="opc"
PROJECT_DIR="/home/opc/EWI-EasyPlay-Scores"

echo "🚀 開始部署到 OCI..."

# 1. 連接到 OCI 並更新代碼
ssh -o StrictHostKeyChecking=no $OCI_USER@$OCI_HOST << 'ENDSSH'
    # 更新系統
    sudo apt update

    # 安裝 Docker 和 Docker Compose (如果尚未安裝)
    if ! command -v docker &> /dev/null; then
        echo "安裝 Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "安裝 Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    # 克隆或更新專案
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "克隆專案..."
        git clone https://github.com/Paul720810/EWI-EasyPlay-Scores.git $PROJECT_DIR
    else
        echo "更新專案..."
        cd $PROJECT_DIR
        git pull origin main
    fi

    cd $PROJECT_DIR

    # 停止現有服務
    echo "停止現有服務..."
    docker-compose down || true

    # 建置並啟動服務
    echo "建置並啟動服務..."
    docker-compose up -d --build

    # 清理未使用的映像
    echo "清理 Docker 映像..."
    docker system prune -f

    echo "✅ OCI 部署完成！"
    echo "🌐 服務地址: http://140.245.126.35"
    echo "📊 健康檢查: http://140.245.126.35:8000/health"
ENDSSH

echo "🎉 OCI 部署腳本執行完成！"
