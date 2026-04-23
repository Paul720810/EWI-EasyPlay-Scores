// EWI EasyPlay Scores - 主應用程式
// 智能多版本互動簡譜神器

import './style.css';

// 全域變數
let currentTask = null;
let currentResults = null;
let audioContext = null;
let synth = null;
let currentMidi = null;
let isPlaying = false;
let playbackStartTime = 0;
let playbackPosition = 0;
let playbackSpeed = 1.0;

// DOM 元素
let sourceTabBtns = [];
let sourcePanels = [];
let youtubeInput = null;
let processBtn = null;
let spotifySearchInput = null;
let searchBtn = null;
let searchResults = null;
let recordBtn = null;
let progressSection = null;
let progressBar = null;
let progressText = null;
let resultsSection = null;
let appBootstrapped = false;

// API 基礎 URL - 支持多種域名配置
const API_BASE = (() => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    // 使用相對 URL - Worker 會攔截並轉發到後端
    return '/api';
})();

function renderAppShell() {
    const app = document.getElementById('app');
    if (!app) {
        return;
    }

    app.innerHTML = `
        <div class="container">
            <header class="header">
                <h1>🎵 EWI EasyPlay Scores</h1>
                <p class="subtitle">智能多版本互動簡譜神器</p>
                <p class="description">自動轉譜、三種難度、運指提示與互動練習，一次完成。</p>
            </header>

            <section class="card source-selection">
                <div class="source-tabs">
                    <button class="tab-btn active" data-source="youtube">YouTube 連結</button>
                    <button class="tab-btn" data-source="spotify">Spotify 搜尋</button>
                    <button class="tab-btn" data-source="file">本地音檔</button>
                </div>

                <div id="youtube-panel" class="source-panel active">
                    <div class="input-group">
                        <label for="youtube-url">YouTube 連結</label>
                        <input id="youtube-url" type="url" placeholder="貼上 YouTube 連結...">
                        <button id="process-btn" class="btn primary-btn">開始轉譜</button>
                    </div>
                </div>

                <div id="spotify-panel" class="source-panel">
                    <div class="input-group">
                        <label for="spotify-search">Spotify 搜尋</label>
                        <div class="search-section">
                            <input id="spotify-search" type="text" placeholder="輸入歌曲名稱或歌手">
                            <button id="search-btn" class="btn primary-btn">搜尋</button>
                        </div>
                        <div id="search-results" class="search-results"></div>
                        <div class="record-controls">
                            <label for="record-duration">錄製秒數</label>
                            <select id="record-duration">
                                <option value="10">10 秒</option>
                                <option value="30" selected>30 秒</option>
                                <option value="60">60 秒</option>
                            </select>
                            <button id="record-btn" class="btn spotify-btn" disabled>錄製並轉譜</button>
                        </div>
                    </div>
                </div>

                <div id="file-panel" class="source-panel">
                    <div class="input-group">
                        <label for="audio-file">上傳音檔</label>
                        <input id="audio-file" type="file" accept="audio/*">
                        <div class="drop-zone" id="drop-zone">
                            <p>拖曳音檔到這裡，或直接選擇檔案。</p>
                        </div>
                    </div>
                </div>
            </section>

            <section id="progress-section" class="progress-section" style="display: none;">
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">等待開始...</div>
                </div>
            </section>

            <section id="results-section" class="results-section" style="display: none;"></section>
        </div>
    `;
}

function bindDomElements() {
    sourceTabBtns = document.querySelectorAll('.tab-btn');
    sourcePanels = document.querySelectorAll('.source-panel');
    youtubeInput = document.getElementById('youtube-url');
    processBtn = document.getElementById('process-btn');
    spotifySearchInput = document.getElementById('spotify-search');
    searchBtn = document.getElementById('search-btn');
    searchResults = document.getElementById('search-results');
    recordBtn = document.getElementById('record-btn');
    progressSection = document.getElementById('progress-section');
    progressBar = document.querySelector('.progress-fill');
    progressText = document.querySelector('.progress-text');
    resultsSection = document.getElementById('results-section');
}

function bootstrapApp() {
    if (appBootstrapped) {
        return;
    }

    appBootstrapped = true;
    console.log('🎵 EWI EasyPlay Scores 初始化中...');

    renderAppShell();
    bindDomElements();

    // 初始化事件監聽器
    initializeEventListeners();

    // 檢查 Web Audio API 支援
    checkWebAudioSupport();

    console.log('✅ 應用程式初始化完成');
}

// 初始化應用程式
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrapApp);
} else {
    bootstrapApp();
}

// 初始化事件監聽器
function initializeEventListeners() {
    // 來源選擇標籤
    sourceTabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchSourceTab(btn.dataset.source));
    });

    // YouTube 處理
    if (processBtn) {
        processBtn.addEventListener('click', processYouTubeUrl);
    }

    // Spotify 搜尋
    if (searchBtn) {
        searchBtn.addEventListener('click', searchSpotifyTracks);
    }

    if (spotifySearchInput) {
        spotifySearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchSpotifyTracks();
            }
        });
    }

    // Spotify 錄製
    if (recordBtn) {
        recordBtn.addEventListener('click', recordAndProcessSpotify);
    }
}

// 檢查 Web Audio API 支援
function checkWebAudioSupport() {
    if (!window.AudioContext && !window.webkitAudioContext) {
        showAlert('您的瀏覽器不支援 Web Audio API，音訊播放功能可能無法正常運作。', 'warning');
        return false;
    }

    if (!window.Tone) {
        showAlert('Tone.js 載入失敗，音訊播放功能將無法使用。', 'error');
        return false;
    }

    return true;
}

// 切換來源標籤
function switchSourceTab(source) {
    // 更新標籤按鈕狀態
    sourceTabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.source === source);
    });

    // 更新面板顯示
    sourcePanels.forEach(panel => {
        panel.classList.toggle('active', panel.id === `${source}-panel`);
    });

    console.log(`切換到 ${source} 模式`);
}

// 處理 YouTube URL
async function processYouTubeUrl() {
    const url = youtubeInput.value.trim();

    if (!url) {
        showAlert('請輸入 YouTube 連結', 'error');
        return;
    }

    if (!isValidYouTubeUrl(url)) {
        showAlert('請輸入有效的 YouTube 連結', 'error');
        return;
    }

    try {
        processBtn.disabled = true;
        processBtn.textContent = '處理中...';

        showProgress(true);
        updateProgress(0, '準備處理...');

        // 發送處理請求
        const response = await fetch(`${API_BASE}/api/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                youtube_url: url,
                difficulty_levels: ['easy', 'normal', 'hard']
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        currentTask = result.task_id;

        console.log('任務已建立:', currentTask);

        // 開始輪詢任務狀態
        pollTaskStatus(currentTask);

    } catch (error) {
        console.error('處理失敗:', error);
        showAlert(`處理失敗: ${error.message}`, 'error');
        resetProcessButton();
        showProgress(false);
    }
}

// 輪詢任務狀態
async function pollTaskStatus(taskId) {
    try {
        const response = await fetch(`${API_BASE}/api/status/${taskId}`);

        if (!response.ok) {
            throw new Error(`無法獲取任務狀態: ${response.status}`);
        }

        const status = await response.json();

        // 更新進度
        updateProgress(status.progress, status.current_step || status.status);

        if (status.status === 'completed') {
            // 任務完成
            console.log('任務完成:', status);
            currentResults = status.results;
            showResults(status);
            resetProcessButton();
            showProgress(false);

        } else if (status.status === 'error') {
            // 任務失敗
            throw new Error(status.error || '處理過程中發生錯誤');

        } else {
            // 繼續輪詢
            setTimeout(() => pollTaskStatus(taskId), 2000);
        }

    } catch (error) {
        console.error('狀態查詢失敗:', error);
        showAlert(`狀態查詢失敗: ${error.message}`, 'error');
        resetProcessButton();
        showProgress(false);
    }
}

// 搜尋 Spotify 音樂
async function searchSpotifyTracks() {
    const query = spotifySearchInput.value.trim();

    if (!query) {
        showAlert('請輸入搜尋關鍵字', 'error');
        return;
    }

    try {
        searchBtn.disabled = true;
        searchBtn.textContent = '搜尋中...';

        const response = await fetch(`${API_BASE}/api/spotify/search?q=${encodeURIComponent(query)}&limit=10`);

        if (!response.ok) {
            throw new Error(`搜尋失敗: ${response.status}`);
        }

        const results = await response.json();
        displaySearchResults(results.tracks?.items || []);

    } catch (error) {
        console.error('搜尋失敗:', error);
        showAlert(`搜尋失敗: ${error.message}`, 'error');
    } finally {
        searchBtn.disabled = false;
        searchBtn.textContent = '🔍 搜尋';
    }
}

// 顯示搜尋結果
function displaySearchResults(tracks) {
    if (!searchResults) return;

    if (tracks.length === 0) {
        searchResults.innerHTML = '<p class="no-results">沒有找到相關音樂</p>';
        return;
    }

    searchResults.innerHTML = tracks.map(track => `
        <div class="track-item" data-track-id="${track.id}">
            <img src="${track.album.images[2]?.url || '/placeholder-album.png'}"
                 alt="${track.name}" class="track-image">
            <div class="track-info">
                <h4>${track.name}</h4>
                <p>${track.artists.map(artist => artist.name).join(', ')}</p>
                <p class="album-name">${track.album.name}</p>
            </div>
            <button class="select-btn" onclick="selectTrack('${track.id}', '${track.name}', '${track.artists[0].name}')">
                選擇
            </button>
        </div>
    `).join('');
}

// 選擇音樂
function selectTrack(trackId, trackName, artistName) {
    // 移除之前的選擇
    document.querySelectorAll('.track-item').forEach(item => {
        item.classList.remove('selected');
    });

    // 標記當前選擇
    const selectedItem = document.querySelector(`[data-track-id="${trackId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('selected');
    }

    // 啟用錄製按鈕
    if (recordBtn) {
        recordBtn.disabled = false;
        recordBtn.dataset.trackId = trackId;
        recordBtn.dataset.trackName = trackName;
        recordBtn.dataset.artistName = artistName;
    }

    console.log(`已選擇: ${trackName} - ${artistName}`);
}

// 錄製並處理 Spotify 音樂
async function recordAndProcessSpotify() {
    const trackId = recordBtn.dataset.trackId;
    const trackName = recordBtn.dataset.trackName;
    const duration = document.getElementById('record-duration')?.value || 30;

    if (!trackId) {
        showAlert('請先選擇一首音樂', 'error');
        return;
    }

    try {
        recordBtn.disabled = true;
        recordBtn.textContent = '錄製中...';

        showProgress(true);
        updateProgress(0, '準備錄製...');

        // 發送錄製請求
        const response = await fetch(`${API_BASE}/api/spotify/record-and-process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                spotify_track_id: trackId,
                title: trackName,
                recording_duration: parseInt(duration),
                difficulty_levels: ['easy', 'normal', 'hard']
            })
        });

        if (!response.ok) {
            throw new Error(`錄製失敗: ${response.status}`);
        }

        const result = await response.json();
        currentTask = result.task_id;

        console.log('錄製任務已建立:', currentTask);

        // 開始輪詢任務狀態
        pollTaskStatus(currentTask);

    } catch (error) {
        console.error('錄製失敗:', error);
        showAlert(`錄製失敗: ${error.message}`, 'error');
        resetRecordButton();
        showProgress(false);
    }
}

// 顯示結果
function showResults(taskStatus) {
    if (!resultsSection || !taskStatus.results) return;

    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });

    const songTitle = taskStatus.title || '未知歌曲';

    resultsSection.innerHTML = `
        <div class="song-info">
            <h3>🎵 ${songTitle}</h3>
            <p>轉譜完成！選擇難度開始練習：</p>
        </div>

        <div class="difficulty-tabs">
            <button class="tab-btn active" data-difficulty="easy">Easy 簡易版</button>
            <button class="tab-btn" data-difficulty="normal">Normal 標準版</button>
            <button class="tab-btn" data-difficulty="hard">Hard 困難版</button>
        </div>

        <div class="player-controls">
            <button class="control-btn" id="play-btn">▶️ 播放</button>
            <button class="control-btn" id="pause-btn" disabled>⏸️ 暫停</button>
            <button class="control-btn" id="stop-btn" disabled>⏹️ 停止</button>

            <div class="speed-control">
                <label>速度:</label>
                <input type="range" id="speed-slider" min="0.5" max="1.5" step="0.1" value="1.0">
                <span id="speed-display">1.0x</span>
            </div>
        </div>

        <div class="playback-progress">
            <div class="time-display">
                <span id="current-time">0:00</span>
                <span id="total-time">0:00</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="playback-fill"></div>
            </div>
        </div>

        <div class="score-display">
            <div class="jianpu-container">
                <p>簡譜將在此顯示...</p>
            </div>
        </div>

        <div class="fingering-guide">
            <h4>🎹 EWI 運指提示</h4>
            <div class="fingering-display">
                <div class="fingering-note">準備開始練習</div>
                <div class="fingering-description">選擇難度並點擊播放開始</div>
            </div>
        </div>

        <div class="download-section">
            <h4>📥 下載檔案</h4>
            <div class="download-buttons">
                ${Object.entries(taskStatus.results).map(([difficulty, files]) => `
                    <a href="${API_BASE}${files.midi}" class="download-btn" download>
                        📄 ${difficulty.toUpperCase()} MIDI
                    </a>
                    ${files.pdf ? `<a href="${API_BASE}${files.pdf}" class="download-btn" download>
                        📄 ${difficulty.toUpperCase()} PDF
                    </a>` : ''}
                `).join('')}
            </div>
        </div>
    `;

    // 初始化播放器控制
    initializePlayer();
}

// 初始化播放器
function initializePlayer() {
    const playBtn = document.getElementById('play-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const stopBtn = document.getElementById('stop-btn');
    const speedSlider = document.getElementById('speed-slider');
    const speedDisplay = document.getElementById('speed-display');
    const difficultyTabs = document.querySelectorAll('.difficulty-tabs .tab-btn');

    // 難度切換
    difficultyTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            difficultyTabs.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadMidiForDifficulty(btn.dataset.difficulty);
        });
    });

    // 播放控制
    if (playBtn) {
        playBtn.addEventListener('click', startPlayback);
    }

    if (pauseBtn) {
        pauseBtn.addEventListener('click', pausePlayback);
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', stopPlayback);
    }

    // 速度控制
    if (speedSlider) {
        speedSlider.addEventListener('input', (e) => {
            playbackSpeed = parseFloat(e.target.value);
            speedDisplay.textContent = `${playbackSpeed}x`;

            if (isPlaying && synth) {
                // 重新開始播放以應用新速度
                stopPlayback();
                setTimeout(startPlayback, 100);
            }
        });
    }

    // 載入預設難度 (Easy)
    loadMidiForDifficulty('easy');
}

// 載入指定難度的 MIDI
async function loadMidiForDifficulty(difficulty) {
    if (!currentResults || !currentResults[difficulty]) {
        console.error(`沒有找到 ${difficulty} 難度的結果`);
        return;
    }

    try {
        const midiUrl = `${API_BASE}${currentResults[difficulty].midi}`;
        console.log(`載入 ${difficulty} MIDI:`, midiUrl);

        // 使用 Tone.js 載入 MIDI
        if (window.Midi) {
            const midi = await window.Midi.fromUrl(midiUrl);
            currentMidi = midi;
            console.log(`${difficulty} MIDI 載入成功:`, midi);

            // 更新總時長顯示
            const totalTime = document.getElementById('total-time');
            if (totalTime && midi.duration) {
                totalTime.textContent = formatTime(midi.duration);
            }
        }

    } catch (error) {
        console.error(`載入 ${difficulty} MIDI 失敗:`, error);
        showAlert(`載入 ${difficulty} 版本失敗`, 'error');
    }
}

// 開始播放
async function startPlayback() {
    if (!currentMidi) {
        showAlert('請先選擇難度版本', 'error');
        return;
    }

    try {
        // 初始化 Tone.js (需要用戶互動)
        if (!audioContext) {
            await Tone.start();
            audioContext = Tone.context;
            synth = new Tone.PolySynth(Tone.Synth).toDestination();
        }

        // 停止之前的播放
        if (isPlaying) {
            stopPlayback();
        }

        isPlaying = true;
        playbackStartTime = Tone.now();

        // 更新按鈕狀態
        document.getElementById('play-btn').disabled = true;
        document.getElementById('pause-btn').disabled = false;
        document.getElementById('stop-btn').disabled = false;

        // 播放 MIDI
        currentMidi.tracks.forEach(track => {
            track.notes.forEach(note => {
                synth.triggerAttackRelease(
                    note.name,
                    note.duration / playbackSpeed,
                    (note.time / playbackSpeed) + playbackStartTime,
                    note.velocity
                );
            });
        });

        // 開始進度更新
        updatePlaybackProgress();

        console.log('開始播放，速度:', playbackSpeed);

    } catch (error) {
        console.error('播放失敗:', error);
        showAlert(`播放失敗: ${error.message}`, 'error');
        resetPlaybackState();
    }
}

// 暫停播放
function pausePlayback() {
    if (synth) {
        synth.releaseAll();
    }

    isPlaying = false;

    // 更新按鈕狀態
    document.getElementById('play-btn').disabled = false;
    document.getElementById('pause-btn').disabled = true;
    document.getElementById('stop-btn').disabled = false;

    console.log('播放已暫停');
}

// 停止播放
function stopPlayback() {
    if (synth) {
        synth.releaseAll();
    }

    isPlaying = false;
    playbackPosition = 0;

    // 重置按鈕狀態
    resetPlaybackState();

    // 重置進度條
    const progressFill = document.getElementById('playback-fill');
    const currentTime = document.getElementById('current-time');

    if (progressFill) progressFill.style.width = '0%';
    if (currentTime) currentTime.textContent = '0:00';

    console.log('播放已停止');
}

// 更新播放進度
function updatePlaybackProgress() {
    if (!isPlaying || !currentMidi) return;

    const currentTime = Tone.now() - playbackStartTime;
    const progress = Math.min(currentTime / (currentMidi.duration / playbackSpeed), 1);

    // 更新進度條
    const progressFill = document.getElementById('playback-fill');
    const currentTimeDisplay = document.getElementById('current-time');

    if (progressFill) {
        progressFill.style.width = `${progress * 100}%`;
    }

    if (currentTimeDisplay) {
        currentTimeDisplay.textContent = formatTime(currentTime * playbackSpeed);
    }

    // 檢查是否播放完成
    if (progress >= 1) {
        stopPlayback();
        return;
    }

    // 繼續更新
    if (isPlaying) {
        requestAnimationFrame(updatePlaybackProgress);
    }
}

// 重置播放狀態
function resetPlaybackState() {
    document.getElementById('play-btn').disabled = false;
    document.getElementById('pause-btn').disabled = true;
    document.getElementById('stop-btn').disabled = true;
}

// 工具函數
function isValidYouTubeUrl(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/;
    return youtubeRegex.test(url);
}

function showProgress(show) {
    if (progressSection) {
        progressSection.style.display = show ? 'block' : 'none';
    }
}

function updateProgress(percent, message) {
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    }

    if (progressText) {
        progressText.textContent = message;
    }
}

function resetProcessButton() {
    if (processBtn) {
        processBtn.disabled = false;
        processBtn.textContent = '🎵 開始轉譜';
    }
}

function resetRecordButton() {
    if (recordBtn) {
        recordBtn.disabled = true;
        recordBtn.textContent = '🎤 錄製並轉譜';
    }
}

function showAlert(message, type = 'info') {
    // 創建警告元素
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    // 插入到頁面頂部
    document.body.insertBefore(alert, document.body.firstChild);

    // 3 秒後自動移除
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 3000);

    console.log(`[${type.toUpperCase()}] ${message}`);
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// 導出全域函數供 HTML 使用
window.selectTrack = selectTrack;

console.log('🎵 EWI EasyPlay Scores 主程式載入完成');