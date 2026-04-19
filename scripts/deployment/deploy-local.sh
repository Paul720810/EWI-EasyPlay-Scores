#!/bin/bash
# 本地開發部署腳本

set -e

echo "🚀 啟動本地開發環境..."

# 檢查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 創建必要目錄
mkdir -p backend/{temp,output,static,logs}
mkdir -p frontend/dist

# 停止現有服務
echo "停止現有服務..."
docker-compose down || true

# 建置並啟動服務
echo "建置並啟動服務..."
docker-compose up -d --build

# 等待服務啟動
echo "等待服務啟動..."
sleep 10

# 健康檢查
echo "檢查服務狀態..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 後端服務正常"
else
    echo "❌ 後端服務異常"
fi

if curl -f http://localhost > /dev/null 2>&1; then
    echo "✅ 前端服務正常"
else
    echo "❌ 前端服務異常"
fi

echo "🎉 本地開發環境啟動完成！"
echo "🌐 前端: http://localhost"
echo "🔧 後端: http://localhost:8000"
echo "📚 API 文件: http://localhost:8000/docs"
echo "📊 健康檢查: http://localhost:8000/health"
