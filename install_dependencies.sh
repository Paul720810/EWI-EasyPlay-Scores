#!/bin/bash
# EWI 專案依賴安裝腳本

set -e  # 遇到錯誤時退出

echo "🚀 開始安裝 EWI 專案依賴..."

# 檢查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 需要 Python $required_version 或更高版本，當前版本: $python_version"
    exit 1
fi

echo "✅ Python 版本檢查通過: $python_version"

# 創建虛擬環境
echo "📦 創建虛擬環境..."
python3 -m venv venv
source venv/bin/activate

# 升級 pip
echo "⬆️ 升級 pip..."
pip install --upgrade pip setuptools wheel

# 安裝依賴
echo "📥 安裝 Python 依賴..."
cd backend
pip install -r requirements.txt

echo "🧪 測試依賴..."
pip check

echo "✅ 依賴安裝完成！"
echo ""
echo "🎯 下一步："
echo "1. 複製 .env.example 為 .env"
echo "2. 編輯 .env 文件填入您的配置"
echo "3. 運行: docker-compose up -d"
echo ""
echo "🔗 有用的命令："
echo "  啟動服務: docker-compose up -d"
echo "  查看日誌: docker-compose logs -f"
echo "  停止服務: docker-compose down"
echo "  重建容器: docker-compose up -d --build"
