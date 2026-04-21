// 全域變數
let currentDifficulty = 'normal';
let isPlaying = false;
let currentSpeed = 1.0;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('EWI EasyPlay Scores 已載入');
    initializeApp();
});

function initializeApp() {
    // 設置事件監聽器
    setupEventListeners();
    
    // 檢查後端連接
    checkBackendConnection();
}

function setupEventListeners() {
    // 文件上傳
    const audioFile = document.getElementById('audio-file');
    if (audioFile) {
        audioFile.addEventListener('change', handleFileUpload);
    }
    
    // 拖拽功能
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('drop', handleFileDrop);
    }
    
    // 難度選擇
    const difficultyBtns = document.querySelectorAll('.difficulty-btn');
    difficultyBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            setDifficulty(this.dataset.difficulty);
        });
    });
}

// 檢查後端連接
async function checkBackendConnection() {
    try {
        const response = await fetch('http://140.245.126.35:8001/health');
        const data = await response.json();
        console.log('後端連接正常:', data);
    } catch (error) {
        console.error('後端連接失敗:', error);
        showNotification('後端服務連接失敗，請檢查服務狀態', 'error');
    }
}

// 標籤切換
function switchTab(tabName) {
    // 隱藏所有標籤內容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 移除所有按鈕的 active 類
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 顯示選中的標籤
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
}

// 設置難度
function setDifficulty(difficulty) {
    currentDifficulty = difficulty;
    
    // 更新按鈕狀態
    document.querySelectorAll('.difficulty-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.querySelector(`[data-difficulty="${difficulty}"]`).classList.add('active');
    
    console.log('難度設置為:', difficulty);
}

// 處理 YouTube 轉譜
async function processYouTube() {
    const urlInput = document.getElementById('youtube-url');
    const url = urlInput.value.trim();
    
    if (!url) {
        showNotification('請輸入 YouTube 連結', 'warning');
        return;
    }
    
    if (!isValidYouTubeUrl(url)) {
        showNotification('請輸入有效的 YouTube 連結', 'error');
        return;
    }
    
    try {
        showLoading(true);
        showProgress(true);
        
        const response = await fetch('http://140.245.126.35:8001/api/process-youtube', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                difficulty: currentDifficulty
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySheetMusic(result.sheet_music);
            showNotification('YouTube 音頻轉譜成功！', 'success');
        } else {
            throw new Error(result.error || '轉譜失敗');
        }
        
    } catch (error) {
        console.error('YouTube 處理錯誤:', error);
        showNotification('YouTube 轉譜失敗: ' + error.message, 'error');
    } finally {
        showLoading(false);
        showProgress(false);
    }
}

// 驗證 YouTube URL
function isValidYouTubeUrl(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
}

// 處理文件上傳
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        await processAudioFile(file);
    }
}

// 處理拖拽
function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.style.background = 'rgba(102, 126, 234, 0.1)';
}

function handleFileDrop(event) {
    event.preventDefault();
    event.currentTarget.style.background = '';
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processAudioFile(files[0]);
    }
}

// 處理音頻文件
async function processAudioFile(file) {
    if (!file.type.startsWith('audio/')) {
        showNotification('請選擇音頻文件', 'error');
        return;
    }
    
    try {
        showLoading(true);
        showProgress(true);
        
        const formData = new FormData();
        formData.append('audio', file);
        formData.append('difficulty', currentDifficulty);
        
        const response = await fetch('http://140.245.126.35:8001/api/upload-audio', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySheetMusic(result.sheet_music);
            showNotification('音頻文件轉譜成功！', 'success');
        } else {
            throw new Error(result.error || '轉譜失敗');
        }
        
    } catch (error) {
        console.error('文件處理錯誤:', error);
        showNotification('文件轉譜失敗: ' + error.message, 'error');
    } finally {
        showLoading(false);
        showProgress(false);
    }
}

// 顯示簡譜
function displaySheetMusic(sheetMusic) {
    const sheetDisplay = document.getElementById('sheet-display');
    
    sheetDisplay.innerHTML = `
        <div class="sheet-content">
            <h3>${sheetMusic.title || '轉譜結果'}</h3>
            <div class="sheet-info">
                <span class="info-item">調性: ${sheetMusic.key || 'C'}</span>
                <span class="info-item">難度: ${sheetMusic.difficulty || 'normal'}</span>
                <span class="info-item">節拍: ${sheetMusic.tempo || 120} BPM</span>
            </div>
            <div class="sheet-notes">
                <h4>簡譜:</h4>
                <p class="notes-display">${sheetMusic.notes || '1 2 3 4 5'}</p>
            </div>
            ${sheetMusic.fingering ? `
                <div class="sheet-fingering">
                    <h4>🎺 EWI 運指提示:</h4>
                    <p class="fingering-display">${sheetMusic.fingering}</p>
                </div>
            ` : ''}
        </div>
    `;
    
    // 顯示運指區域
    const fingeringSection = document.getElementById('fingering-section');
    if (fingeringSection && sheetMusic.fingering) {
        fingeringSection.style.display = 'block';
        document.getElementById('fingering-display').innerHTML = sheetMusic.fingering;
    }
}

// Spotify 連接
async function connectSpotify() {
    try {
        const response = await fetch('http://140.245.126.35:8001/api/spotify/auth');
        const result = await response.json();
        
        if (result.auth_url) {
            window.open(result.auth_url, '_blank');
            showNotification('請在新視窗中完成 Spotify 授權', 'info');
        } else {
            throw new Error('無法獲取 Spotify 授權連結');
        }
        
    } catch (error) {
        console.error('Spotify 連接錯誤:', error);
        showNotification('Spotify 連接失敗: ' + error.message, 'error');
    }
}

// 播放控制
function togglePlay() {
    const playBtn = document.getElementById('play-btn');
    const playIcon = playBtn.querySelector('.play-icon');
    
    if (isPlaying) {
        // 暫停播放
        isPlaying = false;
        playIcon.textContent = '▶️';
        playBtn.querySelector('span:last-child').textContent = '播放';
    } else {
        // 開始播放
        isPlaying = true;
        playIcon.textContent = '⏸️';
        playBtn.querySelector('span:last-child').textContent = '暫停';
    }
    
    console.log('播放狀態:', isPlaying ? '播放中' : '已暫停');
}

function stopPlay() {
    isPlaying = false;
    const playBtn = document.getElementById('play-btn');
    const playIcon = playBtn.querySelector('.play-icon');
    
    playIcon.textContent = '▶️';
    playBtn.querySelector('span:last-child').textContent = '播放';
    
    console.log('播放已停止');
}

// 速度控制
function changeSpeed(speed) {
    currentSpeed = speed;
    
    // 更新按鈕狀態
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    event.target.classList.add('active');
    
    console.log('播放速度設置為:', speed + 'x');
}

// 顯示載入狀態
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

// 顯示進度
function showProgress(show) {
    const progressSection = document.getElementById('progress-section');
    if (progressSection) {
        progressSection.style.display = show ? 'block' : 'none';
    }
    
    if (show) {
        // 模擬進度更新
        updateProgress(0, '開始處理...');
        setTimeout(() => updateProgress(25, '下載音頻...'), 500);
        setTimeout(() => updateProgress(50, '分析音頻...'), 1500);
        setTimeout(() => updateProgress(75, '生成簡譜...'), 3000);
        setTimeout(() => updateProgress(100, '完成！'), 4000);
    }
}

// 更新進度
function updateProgress(percent, text) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    if (progressFill) {
        progressFill.style.width = percent + '%';
    }
    
    if (progressText) {
        progressText.textContent = text;
    }
}

// 顯示通知
function showNotification(message, type = 'info') {
    // 創建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // 添加樣式
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    // 設置顏色
    switch (type) {
        case 'success':
            notification.style.background = '#28a745';
            break;
        case 'error':
            notification.style.background = '#dc3545';
            break;
        case 'warning':
            notification.style.background = '#ffc107';
            notification.style.color = '#333';
            break;
        default:
            notification.style.background = '#17a2b8';
    }
    
    // 添加到頁面
    document.body.appendChild(notification);
    
    // 3秒後自動移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 添加動畫樣式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .sheet-content {
        text-align: left;
    }
    
    .sheet-info {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
        flex-wrap: wrap;
    }
    
    .info-item {
        background: #e9ecef;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    
    .notes-display {
        font-family: 'Courier New', monospace;
        font-size: 1.2rem;
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        letter-spacing: 0.2rem;
    }
    
    .fingering-display {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
    }
`;
document.head.appendChild(style);
