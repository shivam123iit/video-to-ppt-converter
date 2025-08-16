# simple_web_app.py - Complete web interface with unlimited playlist support
from flask import Flask, request, jsonify, render_template_string, send_file, send_from_directory
import os
import uuid
import threading
from video_to_ppt_converter import VideoToPPTConverter
import time
import zipfile
import shutil

app = Flask(__name__)

# In-memory task storage
tasks = {}

# Complete HTML template with unlimited playlist support
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Video to PPT Converter - Unlimited Playlist Support</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white; 
            padding: 30px; 
            text-align: center; 
        }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; font-weight: 300; }
        .header p { opacity: 0.9; font-size: 1.1rem; }
        .header .subtitle { font-size: 0.9rem; margin-top: 10px; opacity: 0.8; }
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .tab {
            flex: 1;
            padding: 20px;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s;
            color: #6c757d;
        }
        .tab.active {
            background: white;
            color: #007bff;
            border-bottom: 3px solid #007bff;
            transform: translateY(-2px);
        }
        .tab:hover:not(.active) {
            background: #e9ecef;
            color: #495057;
        }
        .tab-content {
            display: none;
            padding: 40px;
        }
        .tab-content.active {
            display: block;
        }
        .form-group { margin-bottom: 25px; }
        label { 
            display: block; 
            margin-bottom: 10px; 
            font-weight: 600; 
            color: #333;
            font-size: 16px;
        }
        input[type="text"], input[type="number"] { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            font-size: 16px;
            transition: all 0.3s;
        }
        input:focus { 
            outline: none; 
            border-color: #4facfe; 
            box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
        }
        .settings { 
            display: grid; 
            grid-template-columns: 1fr 1fr 1fr; 
            gap: 20px; 
        }
        button { 
            width: 100%; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 18px; 
            border: none; 
            border-radius: 10px; 
            font-size: 18px; 
            font-weight: 600;
            cursor: pointer; 
            transition: all 0.3s;
        }
        button:hover:not(:disabled) { 
            transform: translateY(-3px); 
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        button:disabled { 
            opacity: 0.6; 
            cursor: not-allowed; 
            transform: none; 
            box-shadow: none;
        }
        .status { 
            margin-top: 30px; 
            padding: 25px; 
            border-radius: 10px; 
            display: none; 
        }
        .status.pending { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .status.processing { background: #cce5ff; color: #004085; border: 1px solid #74b9ff; }
        .status.completed { background: #d4edda; color: #155724; border: 1px solid #00b894; }
        .status.failed { background: #f8d7da; color: #721c24; border: 1px solid #e17055; }
        .progress { 
            background: #e9ecef; 
            height: 12px; 
            border-radius: 6px; 
            margin: 15px 0; 
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }
        .progress-bar { 
            background: linear-gradient(90deg, #00b894, #00cec9); 
            height: 100%; 
            transition: width 0.5s ease; 
            width: 0%;
            border-radius: 6px;
        }
        .download { 
            display: inline-block; 
            background: #28a745; 
            color: white; 
            padding: 12px 20px; 
            text-decoration: none; 
            border-radius: 8px; 
            margin: 8px 8px 8px 0;
            font-weight: 600;
            transition: all 0.3s;
        }
        .download:hover {
            background: #218838;
            transform: translateY(-2px);
            text-decoration: none;
            color: white;
        }
        .download.zip { 
            background: #ff6b35; 
            font-size: 16px;
            padding: 15px 25px;
        }
        .download.zip:hover { background: #e55a2b; }
        .help-text { 
            font-size: 14px; 
            color: #6c757d; 
            margin-top: 8px; 
            line-height: 1.4;
        }
        .video-list {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            max-height: 250px;
            overflow-y: auto;
            border: 1px solid #dee2e6;
        }
        .video-item {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .video-item:last-child {
            border-bottom: none;
        }
        .video-title {
            flex: 1;
            margin-right: 10px;
        }
        .video-status {
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        .video-status.pending { background: #fff3cd; color: #856404; }
        .video-status.processing { background: #cce5ff; color: #004085; }
        .video-status.completed { background: #d4edda; color: #155724; }
        .video-status.failed { background: #f8d7da; color: #721c24; }
        .playlist-stats {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border: 1px solid #2196f3;
        }
        .playlist-stats h4 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        .preset-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin: 15px 0;
        }
        .preset-btn {
            padding: 10px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
            font-size: 14px;
            transition: all 0.3s;
        }
        .preset-btn:hover {
            background: #e9ecef;
            border-color: #007bff;
        }
        .preset-btn.active {
            background: #007bff;
            color: white;
            border-color: #007bff;
        }
        .example-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }
        .example-url {
            background: white;
            padding: 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 14px;
            border: 1px solid #dee2e6;
            cursor: pointer;
            margin: 8px 0;
            transition: all 0.3s;
        }
        .example-url:hover {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        @media (max-width: 768px) {
            .settings { grid-template-columns: 1fr; }
            .preset-buttons { grid-template-columns: 1fr; }
            .header h1 { font-size: 2rem; }
            .tab-content { padding: 20px; }
            .container { margin: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 Video to PowerPoint Converter</h1>
            <p>Convert YouTube videos or entire playlists to presentation slides</p>
            <div class="subtitle">✨ Now with unlimited playlist support - process entire channels!</div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('single')">📱 Single Video</button>
            <button class="tab" onclick="switchTab('playlist')">📋 Full Playlist</button>
        </div>
        
        <!-- Single Video Tab -->
        <div id="single-tab" class="tab-content active">
            <form id="singleForm">
                <div class="form-group">
                    <label for="singleVideoUrl">🎬 YouTube Video URL</label>
                    <input type="text" id="singleVideoUrl" placeholder="https://www.youtube.com/watch?v=..." required>
                    <div class="help-text">Paste any YouTube video URL here for single video conversion</div>
                </div>
                
                <div class="form-group">
                    <label>⚙️ Quality Presets</label>
                    <div class="preset-buttons">
                        <div class="preset-btn active" onclick="setSinglePreset('balanced')">
                            <strong>Balanced</strong><br>
                            <small>Good quality & speed</small>
                        </div>
                        <div class="preset-btn" onclick="setSinglePreset('detailed')">
                            <strong>Detailed</strong><br>
                            <small>More slides</small>
                        </div>
                        <div class="preset-btn" onclick="setSinglePreset('fast')">
                            <strong>Fast</strong><br>
                            <small>Fewer slides</small>
                        </div>
                    </div>
                </div>
                
                <div class="settings">
                    <div class="form-group">
                        <label for="singleThreshold">Similarity Threshold</label>
                        <input type="number" id="singleThreshold" min="0.80" max="0.99" step="0.01" value="0.90">
                        <div class="help-text">Lower = more slides</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="singleInterval">Frame Interval</label>
                        <input type="number" id="singleInterval" min="15" max="120" value="30">
                        <div class="help-text">Higher = fewer slides</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Processing Mode</label>
                        <select id="singleMode" style="width: 100%; padding: 15px; border: 2px solid #e1e5e9; border-radius: 10px; font-size: 16px;">
                            <option value="standard">Standard Quality</option>
                            <option value="fast">Fast Processing</option>
                            <option value="detailed">Detailed Analysis</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" id="singleBtn">🚀 Convert Single Video</button>
            </form>
        </div>
        
        <!-- Playlist Tab -->
        <div id="playlist-tab" class="tab-content">
            <div class="example-section">
                <h4>📋 Example Playlist (Click to Use)</h4>
                <div class="example-url" onclick="fillPlaylistUrl('https://www.youtube.com/playlist?list=PLHmPsm34AX4bg-pFUgI1eA5bNvunl_Vmb')">
                    https://www.youtube.com/playlist?list=PLHmPsm34AX4bg-pFUgI1eA5bNvunl_Vmb
                </div>
                <p class="help-text">This is your specified playlist - click above to auto-fill it!</p>
            </div>
            
            <form id="playlistForm">
                <div class="form-group">
                    <label for="playlistUrl">📋 YouTube Playlist URL</label>
                    <input type="text" id="playlistUrl" placeholder="https://www.youtube.com/playlist?list=..." required>
                    <div class="help-text">
                        Paste any YouTube playlist URL here. Works with:
                        <br>• Public playlists • Educational content • Tutorial series • Conference talks
                    </div>
                </div>
                
                <div class="form-group">
                    <label>⚙️ Content Type Presets</label>
                    <div class="preset-buttons">
                        <div class="preset-btn active" onclick="setPlaylistPreset('educational')">
                            <strong>📚 Educational</strong><br>
                            <small>Lectures, Courses</small>
                        </div>
                        <div class="preset-btn" onclick="setPlaylistPreset('tutorial')">
                            <strong>🛠️ Tutorial</strong><br>
                            <small>How-to, Coding</small>
                        </div>
                        <div class="preset-btn" onclick="setPlaylistPreset('presentation')">
                            <strong>🎤 Presentation</strong><br>
                            <small>Talks, Slides</small>
                        </div>
                    </div>
                </div>
                
                <div class="settings">
                    <div class="form-group">
                        <label for="playlistThreshold">Similarity Threshold</label>
                        <input type="number" id="playlistThreshold" min="0.80" max="0.99" step="0.01" value="0.90">
                        <div class="help-text">Lower = more slides per video</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="playlistInterval">Frame Interval</label>
                        <input type="number" id="playlistInterval" min="15" max="120" value="45">
                        <div class="help-text">Higher = fewer slides per video</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="maxVideos">Max Videos (Optional)</label>
                        <input type="number" id="maxVideos" min="1" max="999" placeholder="Leave empty for ALL videos">
                        <div class="help-text">
                            <strong>Leave empty to process ALL videos in playlist!</strong><br>
                            Or set a limit if you want to test with fewer videos first.
                        </div>
                    </div>
                </div>
                
                <button type="submit" id="playlistBtn">🎬 Convert Entire Playlist</button>
            </form>
            
            <div id="playlistInfo" style="display: none;"></div>
        </div>
        
        <div id="status" class="status">
            <h4 id="statusTitle">Processing...</h4>
            <p id="statusText">Starting conversion...</p>
            <div class="progress">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            <div id="videoProgress" class="video-list" style="display: none;"></div>
            <div id="downloadSection"></div>
        </div>
    </div>

    <script>
        let currentTaskId = null;
        let statusInterval = null;
        let activeTab = 'single';
        
        function switchTab(tab) {
            activeTab = tab;
            
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`[onclick="switchTab('${tab}')"]`).classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.getElementById(`${tab}-tab`).classList.add('active');
            
            // Hide status if switching tabs
            document.getElementById('status').style.display = 'none';
        }
        
        function fillPlaylistUrl(url) {
            document.getElementById('playlistUrl').value = url;
            // Auto-focus the field to show it's filled
            document.getElementById('playlistUrl').focus();
            document.getElementById('playlistUrl').style.background = '#e3f2fd';
            setTimeout(() => {
                document.getElementById('playlistUrl').style.background = '';
            }, 2000);
        }
        
        function setSinglePreset(type) {
            // Update button states
            document.querySelectorAll('#single-tab .preset-btn').forEach(btn => btn.classList.remove('active'));
            event.target.closest('.preset-btn').classList.add('active');
            
            const threshold = document.getElementById('singleThreshold');
            const interval = document.getElementById('singleInterval');
            
            switch(type) {
                case 'detailed':
                    threshold.value = 0.85;
                    interval.value = 20;
                    break;
                case 'fast':
                    threshold.value = 0.95;
                    interval.value = 60;
                    break;
                default: // balanced
                    threshold.value = 0.90;
                    interval.value = 30;
            }
        }
        
        function setPlaylistPreset(type) {
            // Update button states
            document.querySelectorAll('#playlist-tab .preset-btn').forEach(btn => btn.classList.remove('active'));
            event.target.closest('.preset-btn').classList.add('active');
            
            const threshold = document.getElementById('playlistThreshold');
            const interval = document.getElementById('playlistInterval');
            
            switch(type) {
                case 'tutorial':
                    threshold.value = 0.88;
                    interval.value = 20;
                    break;
                case 'presentation':
                    threshold.value = 0.95;
                    interval.value = 60;
                    break;
                default: // educational
                    threshold.value = 0.92;
                    interval.value = 45;
            }
        }
        
        document.getElementById('singleForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const videoUrl = document.getElementById('singleVideoUrl').value.trim();
            const threshold = parseFloat(document.getElementById('singleThreshold').value);
            const interval = parseInt(document.getElementById('singleInterval').value);
            const mode = document.getElementById('singleMode').value;
            
            if (!videoUrl) {
                alert('Please enter a YouTube video URL');
                return;
            }
            
            await startConversion({
                type: 'single',
                video_url: videoUrl,
                threshold: threshold,
                interval: interval,
                mode: mode
            }, 'singleBtn');
        };
        
        document.getElementById('playlistForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const playlistUrl = document.getElementById('playlistUrl').value.trim();
            const threshold = parseFloat(document.getElementById('playlistThreshold').value);
            const interval = parseInt(document.getElementById('playlistInterval').value);
            const maxVideosInput = document.getElementById('maxVideos').value.trim();
            const maxVideos = maxVideosInput ? parseInt(maxVideosInput) : null;
            
            if (!playlistUrl) {
                alert('Please enter a YouTube playlist URL');
                return;
            }
            
            if (!playlistUrl.includes('playlist') && !playlistUrl.includes('list=')) {
                alert('Please enter a valid YouTube playlist URL\\n\\nExample: https://www.youtube.com/playlist?list=...');
                return;
            }
            
            // Confirm if processing all videos
            if (!maxVideos) {
                const confirm = window.confirm(
                    'You are about to process ALL videos in this playlist.\\n\\n' +
                    'This could take several hours depending on playlist size.\\n\\n' +
                    'Continue with unlimited processing?'
                );
                if (!confirm) return;
            }
            
            await startConversion({
                type: 'playlist',
                playlist_url: playlistUrl,
                threshold: threshold,
                interval: interval,
                max_videos: maxVideos
            }, 'playlistBtn');
        };
        
        async function startConversion(data, buttonId) {
            try {
                // Disable form
                const btn = document.getElementById(buttonId);
                btn.disabled = true;
                btn.textContent = 'Starting...';
                
                // Show status
                const statusDiv = document.getElementById('status');
                statusDiv.style.display = 'block';
                statusDiv.className = 'status processing';
                document.getElementById('statusTitle').textContent = 'Starting Conversion';
                document.getElementById('statusText').textContent = 'Initializing...';
                
                // Start conversion
                const response = await fetch('/convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Conversion failed');
                }
                
                const result = await response.json();
                currentTaskId = result.task_id;
                
                // Show playlist info if available
                if (result.playlist_info) {
                    showPlaylistInfo(result.playlist_info);
                }
                
                // Start status checking
                checkStatus();
                statusInterval = setInterval(checkStatus, 3000);
                
            } catch (error) {
                showError('Failed to start conversion: ' + error.message);
                resetForm(buttonId);
            }
        }
        
        function showPlaylistInfo(info) {
            const infoDiv = document.getElementById('playlistInfo');
            infoDiv.style.display = 'block';
            infoDiv.innerHTML = `
                <div class="playlist-stats">
                    <h4>📋 ${info.title}</h4>
                    <p><strong>👤 Channel:</strong> ${info.uploader}</p>
                    <p><strong>📹 Total Videos:</strong> ${info.video_count}</p>
                    <p><strong>🚀 Processing:</strong> ${info.video_count} videos (unlimited mode)</p>
                    <p><strong>⏱️ Estimated Time:</strong> ${Math.round(info.video_count * 4)} - ${Math.round(info.video_count * 8)} minutes</p>
                </div>
            `;
        }
        
        async function checkStatus() {
            if (!currentTaskId) return;
            
            try {
                const response = await fetch(`/status/${currentTaskId}`);
                if (!response.ok) throw new Error('Status check failed');
                
                const task = await response.json();
                updateStatusDisplay(task);
                
                if (task.status === 'completed') {
                    clearInterval(statusInterval);
                    showSuccess(task);
                    resetForm();
                } else if (task.status === 'failed') {
                    clearInterval(statusInterval);
                    showError(task.error || 'Conversion failed');
                    resetForm();
                }
                
            } catch (error) {
                console.error('Status check error:', error);
            }
        }
        
        function updateStatusDisplay(task) {
            const statusDiv = document.getElementById('status');
            const titleEl = document.getElementById('statusTitle');
            const textEl = document.getElementById('statusText');
            const progressBar = document.getElementById('progressBar');
            
            statusDiv.className = `status ${task.status}`;
            
            switch(task.status) {
                case 'pending':
                    titleEl.textContent = '⏳ Queued';
                    textEl.textContent = 'Waiting to start...';
                    break;
                case 'processing':
                    if (task.type === 'playlist') {
                        titleEl.textContent = '🎬 Converting Playlist (Unlimited Mode)';
                        const current = task.current_video || 0;
                        const total = task.total_videos || '?';
                        textEl.textContent = `Processing video ${current}/${total} - ${Math.round((current/total)*100) || 0}% complete`;
                        
                        // Show video progress if available
                        if (task.video_progress) {
                            showVideoProgress(task.video_progress);
                        }
                    } else {
                        titleEl.textContent = '🎥 Converting Single Video';
                        textEl.textContent = 'Extracting frames and creating slides...';
                    }
                    break;
                case 'completed':
                    titleEl.textContent = '✅ Conversion Complete!';
                    if (task.type === 'playlist') {
                        const count = task.output_files?.length || 0;
                        textEl.textContent = `Successfully processed ${count} videos from playlist!`;
                    } else {
                        textEl.textContent = 'Your PowerPoint presentation is ready for download.';
                    }
                    break;
                case 'failed':
                    titleEl.textContent = '❌ Conversion Failed';
                    textEl.textContent = task.error || 'An error occurred during processing';
                    break;
            }
            
            const progress = task.progress || 0;
            progressBar.style.width = progress + '%';
        }
        
        function showVideoProgress(videoProgress) {
            const progressDiv = document.getElementById('videoProgress');
            progressDiv.style.display = 'block';
            progressDiv.innerHTML = '<h5>📹 Video Processing Status:</h5>';
            
            videoProgress.forEach((video, index) => {
                const videoItem = document.createElement('div');
                videoItem.className = 'video-item';
                videoItem.innerHTML = `
                    <div class="video-title">${index + 1}. ${video.title}</div>
                    <div class="video-status ${video.status}">${video.status.toUpperCase()}</div>
                `;
                progressDiv.appendChild(videoItem);
            });
        }
        
        function showSuccess(task) {
            const downloadSection = document.getElementById('downloadSection');
            
            if (task.type === 'playlist' && task.output_files && task.output_files.length > 0) {
                let downloadHtml = `
                    <h4>🎉 Playlist Conversion Complete!</h4>
                    <p><strong>✅ Successfully processed:</strong> ${task.output_files.length - 1} videos</p>
                    <br>
                    <a href="/download/${task.id}/all" class="download zip">📦 Download All Presentations (ZIP)</a>
                    <br><br>
                    <h5>📄 Individual Files:</h5>
                `;
                
                // Show first 15 individual files
                const individualFiles = task.output_files.filter(f => !f.endsWith('.zip')).slice(0, 15);
                individualFiles.forEach((file, index) => {
                    downloadHtml += `
                        <a href="/download/${task.id}/${file}" class="download">📄 ${index + 1}. ${file.replace('.pptx', '')}</a>
                    `;
                });
                
                if (task.output_files.length > 16) {
                    downloadHtml += `
                        <p class="help-text">
                            <strong>📦 Download the ZIP file above to get all ${task.output_files.length - 1} presentations!</strong>
                        </p>
                    `;
                }
                
                downloadSection.innerHTML = downloadHtml;
            } else {
                downloadSection.innerHTML = `
                    <h4>🎉 Video Conversion Complete!</h4>
                    <a href="/download/${task.id}" class="download">📥 Download PowerPoint Presentation</a>
                    <div class="help-text" style="margin-top: 15px;">
                        <strong>Task ID:</strong> ${task.id}<br>
                        Right-click download link and "Save As" if needed
                    </div>
                `;
            }
        }
        
        function showError(message) {
            const statusDiv = document.getElementById('status');
            statusDiv.style.display = 'block';
            statusDiv.className = 'status failed';
            document.getElementById('statusTitle').textContent = '❌ Error';
            document.getElementById('statusText').textContent = message;
        }
        
        function resetForm(buttonId = null) {
            if (buttonId) {
                const btn = document.getElementById(buttonId);
                btn.disabled = false;
                if (buttonId === 'singleBtn') {
                    btn.textContent = '🚀 Convert Single Video';
                } else {
                    btn.textContent = '🎬 Convert Entire Playlist';
                }
            } else {
                // Reset all buttons
                document.getElementById('singleBtn').disabled = false;
                document.getElementById('singleBtn').textContent = '🚀 Convert Single Video';
                document.getElementById('playlistBtn').disabled = false;
                document.getElementById('playlistBtn').textContent = '🎬 Convert Entire Playlist';
            }
        }
        
        // Auto-fill the example playlist on page load
        window.onload = function() {
            document.getElementById('playlistUrl').value = 'https://www.youtube.com/playlist?list=PLHmPsm34AX4bg-pFUgI1eA5bNvunl_Vmb';
        };
    </script>
</body>
</html>
'''

class SimpleTaskManager:
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, task_id, task_type, **kwargs):
        self.tasks[task_id] = {
            'id': task_id,
            'type': task_type,
            'status': 'pending',
            'progress': 0,
            'output_files': [],
            'error': None,
            'current_video': 0,
            'total_videos': 0,
            'video_progress': [],
            **kwargs
        }
        return task_id
    
    def update_task(self, task_id, **kwargs):
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
    
    def get_task(self, task_id):
        return self.tasks.get(task_id)

task_manager = SimpleTaskManager()

def process_single_video_background(task_id, video_url, threshold, interval, mode='standard'):
    """Background single video processing with enhanced options"""
    try:
        print(f"Starting single video task {task_id}: {video_url} (mode: {mode})")
        task_manager.update_task(task_id, status='processing', progress=10)
        
        # Adjust settings based on mode
        if mode == 'fast':
            threshold = min(threshold + 0.03, 0.98)
            interval = max(interval + 15, 45)
        elif mode == 'detailed':
            threshold = max(threshold - 0.03, 0.82)
            interval = max(interval - 10, 15)
        
        converter = VideoToPPTConverter(
            similarity_threshold=threshold,
            min_frame_interval=interval
        )
        
        task_manager.update_task(task_id, progress=25)
        
        output_filename = f"presentation_{task_id}.pptx"
        output_path = os.path.join('outputs', output_filename)
        
        task_manager.update_task(task_id, progress=50)
        
        result = converter.process_video(
            video_url,
            output_ppt=output_path,
            cleanup_temp=True
        )
        
        if result and os.path.exists(output_path):
            task_manager.update_task(
                task_id,
                status='completed',
                progress=100,
                output_files=[output_filename]
            )
            print(f"Single video task {task_id}: Completed successfully")
        else:
            raise Exception("Failed to create PowerPoint file")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Single video task {task_id}: Failed with error: {error_msg}")
        task_manager.update_task(task_id, status='failed', error=error_msg)

def process_playlist_background(task_id, playlist_url, threshold, interval, max_videos=None):
    """Background playlist processing with unlimited support"""
    try:
        print(f"Starting playlist task {task_id}: {playlist_url} (max_videos: {max_videos or 'UNLIMITED'})")
        task_manager.update_task(task_id, status='processing', progress=5)
        
        converter = VideoToPPTConverter(
            similarity_threshold=threshold,
            min_frame_interval=interval
        )
        
        # Create playlist output directory
        playlist_output_dir = os.path.join('outputs', f"playlist_{task_id}")
        os.makedirs(playlist_output_dir, exist_ok=True)
        
        task_manager.update_task(task_id, progress=10)
        
        # Process playlist with unlimited videos if max_videos is None
        results = converter.process_playlist(
            playlist_url=playlist_url,
            output_dir=playlist_output_dir,
            max_videos=max_videos,  # None means unlimited
            cleanup_temp=True
        )
        
        # Track video progress
        video_progress = []
        output_files = []
        
        if results['processed_videos']:
            for i, video in enumerate(results['processed_videos']):
                filename = os.path.basename(video['output_path'])
                output_files.append(filename)
                
                video_progress.append({
                    'title': video['title'][:50] + '...' if len(video['title']) > 50 else video['title'],
                    'status': 'completed'
                })
                
                # Update progress during processing
                current_video = len(output_files)
                total_videos = results['total_videos']
                progress = 10 + (current_video / total_videos) * 80
                
                task_manager.update_task(
                    task_id, 
                    current_video=current_video,
                    total_videos=total_videos,
                    progress=min(90, progress),
                    video_progress=video_progress
                )
                
                print(f"Playlist {task_id}: Completed video {current_video}/{total_videos}")
        
        # Add failed videos to progress
        if results['failed_videos']:
            for video in results['failed_videos']:
                video_progress.append({
                    'title': video['title'][:50] + '...' if len(video['title']) > 50 else video['title'],
                    'status': 'failed'
                })
        
        # Create ZIP file of all presentations
        if output_files:
            zip_filename = f"playlist_{task_id}_all.zip"
            zip_path = os.path.join('outputs', zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in output_files:
                    file_path = os.path.join(playlist_output_dir, filename)
                    if os.path.exists(file_path):
                        # Use a clean filename in the ZIP
                        clean_name = filename.replace(f'_{task_id}', '').replace('presentation_', '')
                        zipf.write(file_path, clean_name)
            
            output_files.append(zip_filename)
        
        task_manager.update_task(
            task_id,
            status='completed',
            progress=100,
            output_files=output_files,
            processed_count=len(results['processed_videos']),
            failed_count=len(results['failed_videos']),
            video_progress=video_progress
        )
        
        print(f"Playlist task {task_id}: Completed successfully")
        print(f"Results: {len(results['processed_videos'])} successful, {len(results['failed_videos'])} failed")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Playlist task {task_id}: Failed with error: {error_msg}")
        task_manager.update_task(task_id, status='failed', error=error_msg)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        conversion_type = data.get('type', 'single')
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())[:8]
        
        if conversion_type == 'playlist':
            playlist_url = data.get('playlist_url', '').strip()
            threshold = float(data.get('threshold', 0.90))
            interval = int(data.get('interval', 45))
            max_videos = data.get('max_videos')  # Can be None for unlimited
            
            if not playlist_url:
                return jsonify({'error': 'No playlist URL provided'}), 400
            
            if not ('playlist' in playlist_url or 'list=' in playlist_url):
                return jsonify({'error': 'Please provide a valid YouTube playlist URL'}), 400
            
            # Get playlist info first
            try:
                converter = VideoToPPTConverter()
                playlist_info = converter.get_playlist_info(playlist_url)
                
                # Update video count if limited
                if max_videos and max_videos < playlist_info['video_count']:
                    playlist_info['video_count'] = max_videos
                
                print(f"Playlist info: {playlist_info['title']} - {playlist_info['video_count']} videos")
                
            except Exception as e:
                return jsonify({'error': f'Failed to get playlist info: {str(e)}'}), 400
            
            # Create playlist task
            task_manager.create_task(
                task_id, 
                'playlist',
                playlist_url=playlist_url,
                threshold=threshold,
                interval=interval,
                max_videos=max_videos,
                total_videos=playlist_info['video_count']
            )
            
            # Start background processing
            thread = threading.Thread(
                target=process_playlist_background,
                args=(task_id, playlist_url, threshold, interval, max_videos),
                daemon=True
            )
            thread.start()
            
            return jsonify({
                'task_id': task_id,
                'status': 'started',
                'type': 'playlist',
                'playlist_info': playlist_info
            })
            
        else:  # Single video
            video_url = data.get('video_url', '').strip()
            threshold = float(data.get('threshold', 0.90))
            interval = int(data.get('interval', 30))
            mode = data.get('mode', 'standard')
            
            if not video_url:
                return jsonify({'error': 'No video URL provided'}), 400
            
            if not ('youtube.com' in video_url or 'youtu.be' in video_url):
                return jsonify({'error': 'Please provide a valid YouTube URL'}), 400
            
            # Create single video task
            task_manager.create_task(
                task_id,
                'single',
                video_url=video_url,
                threshold=threshold,
                interval=interval,
                mode=mode
            )
            
            # Start background processing
            thread = threading.Thread(
                target=process_single_video_background,
                args=(task_id, video_url, threshold, interval, mode),
                daemon=True
            )
            thread.start()
            
            return jsonify({
                'task_id': task_id,
                'status': 'started',
                'type': 'single'
            })
        
    except Exception as e:
        print(f"Convert endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status/<task_id>')
def status(task_id):
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@app.route('/download/<task_id>')
@app.route('/download/<task_id>/<filename>')
def download(task_id, filename=None):
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Conversion not completed yet'}), 400
    
    if task['type'] == 'playlist':
        if filename == 'all':
            # Download ZIP file
            zip_filename = f"playlist_{task_id}_all.zip"
            zip_path = os.path.join('outputs', zip_filename)
            if os.path.exists(zip_path):
                return send_file(
                    zip_path, 
                    as_attachment=True, 
                    download_name=f"playlist_presentations_{task_id}.zip"
                )
            else:
                return jsonify({'error': 'ZIP file not found'}), 404
        elif filename:
            # Download specific file
            if filename in task['output_files']:
                if filename.endswith('.zip'):
                    file_path = os.path.join('outputs', filename)
                else:
                    file_path = os.path.join('outputs', f"playlist_{task_id}", filename)
                
                if os.path.exists(file_path):
                    return send_file(file_path, as_attachment=True)
                else:
                    return jsonify({'error': 'File not found'}), 404
            else:
                return jsonify({'error': 'File not in task output'}), 404
        else:
            return jsonify({'error': 'No filename specified for playlist download'}), 400
    else:
        # Single video download
        if not task['output_files']:
            return jsonify({'error': 'No output file available'}), 404
        
        file_path = os.path.join('outputs', task['output_files'][0])
        if not os.path.exists(file_path):
            return jsonify({'error': 'Output file not found'}), 404
        
        return send_file(
            file_path, 
            as_attachment=True,
            download_name=f"video_presentation_{task_id}.pptx"
        )

@app.route('/health')
def health():
    active_tasks = len([t for t in task_manager.tasks.values() if t['status'] == 'processing'])
    total_tasks = len(task_manager.tasks)
    
    return jsonify({
        'status': 'healthy', 
        'active_tasks': active_tasks,
        'total_tasks': total_tasks,
        'features': ['single_video', 'unlimited_playlist', 'batch_download'],
        'version': '2.0-unlimited'
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    
    # Get port from environment (Railway provides PORT variable)
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🚀 Starting Video to PowerPoint Converter v2.0")
    print(f"📡 Server starting on port {port}")
    print(f"🌐 Environment: {'Railway' if 'RAILWAY_' in str(os.environ) else 'Local'}")
    print(f"✨ Features:")
    print(f"   📱 Single video conversion")
    print(f"   📋 UNLIMITED playlist conversion")
    print(f"   📦 Batch ZIP downloads")
    print(f"   🎯 Smart quality presets")
    print(f"   📊 Real-time progress tracking")
    
    try:
        # Run the Flask app with Railway-optimized settings
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        print("🔧 Check logs for more details")
        raise
