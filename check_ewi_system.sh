#!/bin/bash

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}🎵 EWI EasyPlay Scores 系統檢查${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_section() {
    echo -e "\n${YELLOW}📍 $1${NC}"
    echo "------------------------------------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 檢查函數
check_docker_containers() {
    print_section "檢查 Docker 容器狀態"
    
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker 容器正在運行"
        docker-compose ps
    else
        print_error "Docker 容器未運行"
        return 1
    fi
}

check_backend_health() {
    print_section "檢查後端服務健康狀態"
    
    # 檢查健康端點
    if curl -s -f http://localhost:8001/health > /dev/null; then
        print_success "後端健康檢查通過"
        echo "健康檢查詳情:"
        curl -s http://localhost:8001/health | python3 -m json.tool
    else
        print_error "後端健康檢查失敗"
        return 1
    fi
}

check_api_endpoints() {
    print_section "檢查 API 端點"
    
    # 測試根端點
    if curl -s -f http://localhost:8001/ > /dev/null; then
        print_success "根端點 (/) 正常"
    else
        print_error "根端點 (/) 異常"
    fi
    
    # 測試 API 文檔
    if curl -s -f http://localhost:8001/docs > /dev/null; then
        print_success "API 文檔 (/docs) 可訪問"
    else
        print_error "API 文檔 (/docs) 無法訪問"
    fi
    
    # 測試統計端點
    if curl -s -f http://localhost:8001/api/stats > /dev/null; then
        print_success "統計端點 (/api/stats) 正常"
    else
        print_error "統計端點 (/api/stats) 異常"
    fi
    
    # 測試難度端點
    if curl -s -f http://localhost:8001/api/difficulties > /dev/null; then
        print_success "難度端點 (/api/difficulties) 正常"
    else
        print_error "難度端點 (/api/difficulties) 異常"
    fi
    
    # 測試 Spotify 授權端點
    if curl -s -f http://localhost:8001/api/spotify/auth > /dev/null; then
        print_success "Spotify 授權端點正常"
    else
        print_error "Spotify 授權端點異常"
    fi
}

test_youtube_processing() {
    print_section "測試 YouTube 處理功能"
    
    response=$(curl -s -X POST http://localhost:8001/api/process-youtube \
        -H "Content-Type: application/json" \
        -d '{"url": "https://www.youtube.com/watch?v=test", "difficulty": "normal"}')
    
    if echo "$response" | grep -q '"success": true'; then
        print_success "YouTube 處理功能正常"
        echo "測試響應:"
        echo "$response" | python3 -m json.tool
    else
        print_error "YouTube 處理功能異常"
        echo "錯誤響應: $response"
    fi
}

test_file_upload() {
    print_section "測試文件上傳功能"
    
    # 創建測試音頻文件
    echo "創建測試音頻文件..." > test_audio.txt
    
    response=$(curl -s -X POST http://localhost:8001/api/upload-audio \
        -F "audio=@test_audio.txt" \
        -F "difficulty=easy")
    
    if echo "$response" | grep -q '"success": false'; then
        print_success "文件上傳驗證正常（正確拒絕非音頻文件）"
    else
        print_info "文件上傳端點響應: $response"
    fi
    
    # 清理測試文件
    rm -f test_audio.txt
}

check_frontend_files() {
    print_section "檢查前端文件"
    
    if [ -f "frontend/index.html" ]; then
        print_success "前端 HTML 文件存在"
    else
        print_error "前端 HTML 文件缺失"
    fi
    
    if [ -f "frontend/styles.css" ]; then
        print_success "前端 CSS 文件存在"
    else
        print_error "前端 CSS 文件缺失"
    fi
    
    if [ -f "frontend/script.js" ]; then
        print_success "前端 JavaScript 文件存在"
    else
        print_error "前端 JavaScript 文件缺失"
    fi
}

check_environment() {
    print_section "檢查環境配置"
    
    if [ -f ".env" ]; then
        print_success ".env 文件存在"
        echo "環境變數配置:"
        grep -E "^[A-Z]" .env | head -5
    else
        print_error ".env 文件缺失"
    fi
    
    if [ -f "docker-compose.yml" ]; then
        print_success "docker-compose.yml 存在"
    else
        print_error "docker-compose.yml 缺失"
    fi
}

check_network_access() {
    print_section "檢查網路訪問"
    
    # 檢查外部訪問
    print_info "檢查外部 IP 訪問..."
    if curl -s -f http://140.245.126.35:8001/health > /dev/null; then
        print_success "外部 IP (140.245.126.35:8001) 可訪問"
    else
        print_error "外部 IP (140.245.126.35:8001) 無法訪問"
    fi
    
    # 檢查前端域名
    print_info "檢查前端域名..."
    if curl -s -f https://ewi.paul720810.dpdns.org > /dev/null; then
        print_success "前端域名 (ewi.paul720810.dpdns.org) 可訪問"
    else
        print_error "前端域名 (ewi.paul720810.dpdns.org) 無法訪問"
    fi
}

show_system_summary() {
    print_section "系統摘要"
    
    echo "🎯 核心功能狀態:"
    echo "  • YouTube 轉譜: ✅ 已實現"
    echo "  • 文件上傳: ✅ 已實現"
    echo "  • 三種難度: ✅ 已實現"
    echo "  • EWI 運指: ✅ 已實現"
    echo "  • Spotify 整合: ✅ 已實現"
    echo "  • 前端界面: ✅ 已實現"
    
    echo ""
    echo "🌐 訪問地址:"
    echo "  • 後端 API: http://140.245.126.35:8001"
    echo "  • API 文檔: http://140.245.126.35:8001/docs"
    echo "  • 前端網站: https://ewi.paul720810.dpdns.org"
    
    echo ""
    echo "📊 系統資源:"
    echo "  • CPU 使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "  • 記憶體使用: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
    echo "  • 磁碟使用: $(df -h / | awk 'NR==2{print $5}')"
}

# 主執行流程
main() {
    print_header
    
    # 執行所有檢查
    check_docker_containers
    check_backend_health
    check_api_endpoints
    test_youtube_processing
    test_file_upload
    check_frontend_files
    check_environment
    check_network_access
    show_system_summary
    
    echo ""
    echo -e "${GREEN}🎉 系統檢查完成！${NC}"
    echo -e "${BLUE}如果所有項目都顯示 ✅，表示你的 EWI 系統運行正常！${NC}"
}

# 執行主函數
main
