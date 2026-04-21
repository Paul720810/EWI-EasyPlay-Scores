#!/bin/bash

echo "🚀 部署前端到 Cloudflare Pages..."

# 確保在正確目錄
cd /home/opc/EWI-EasyPlay-Scores

# 檢查前端文件
echo "📁 檢查前端文件..."
ls -la frontend/

# 推送到 GitHub
echo "📤 推送到 GitHub..."
git add .
git commit -m "Update EWI frontend - $(date)"
git push origin main

echo "✅ 前端文件已推送到 GitHub"
echo "🌐 Cloudflare Pages 將自動部署"
echo "⏳ 請等待 2-3 分鐘後訪問: https://ewi.paul720810.dpdns.org"

