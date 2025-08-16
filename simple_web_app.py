# simple_web_app.py - Web interface with playlist support
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

# Enhanced HTML template with playlist support
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Video to PPT Converter</title>
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
            max-width: 700px; 
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
        .header h1 { font-size: 2.2rem; margin-bottom: 10px; font-weight: 300; }
        .header p { opacity: 0.9; }
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .tab {
            flex: 1;
            padding: 15px;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .tab.active {
            background: white;
            color: #007bff;
            border-bottom: 3px solid #007bff;
        }
        .tab-content {
            display: none;
            padding: 30px;
        }
        .tab-content.active {
            display: block;
        }
        .form-section { padding: 0; }
        .form-group { margin-bottom: 20px; }
        label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: #333; 
        }
        input[type="text"], input[type="number"] { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #e1e5e9; 
            border-radius: 8px; 
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus { 
            outline: none; 
            border-color: #4facfe; 
        }
        .settings { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 15px; 
        }
        button { 
            width: 100%; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 15px; 
            border: none; 
            border-radius: 8px; 
            font-size: 16px; 
            font-weight: 600;
            cursor: pointer; 
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .status { 
            margin-top: 20px; 
            padding: 20px; 
            border-radius: 8px; 
            display: none; 
        }
        .status.pending { background: #fff3cd; color: #856404; }
        .status.processing { background: #cce5ff; color: #004085; }
        .status.completed { background: #d4edda; color: #155724; }
        .status.failed { background: #f8d7da; color: #721c24; }
        .progress { 
            background: #e9ecef; 
            height: 8px; 
            border-radius: 4px; 
            margin: 10px 0; 
            overflow: hidden;
        }
        .progress-bar { 
            background: #007bff; 
            height: 100%; 
            transition: width 0.3s; 
            width: 0%;
        }
        .download { 
            display: inline-block; 
            background: #28a745; 
            color: white; 
            padding: 12px 24px; 
            text-decoration: none; 
            border-radius: 6px; 
            margin: 5px 5px 5px 0;
            font-weight: 600;
        }
        .download.zip { background: #ff6b35; }
        .help-text { 
            font-size: 14px; 
            color: #6c757d; 
            margin-top: 5px; 
        }
        .video-list {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            max-height: 200px;
            overflow-y: auto;
        }
        .video-item {
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
            font-size: 14px;
        }
        .video-item:last-child {
            border-bottom: none;
        }
        .playlist-stats {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        @media (max-width: 768px) {
            .settings { grid-template-columns: 1fr; }
            .header h1 { font-size: 1.8rem; }
            .tab-content { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 Video to PowerPoint</h1>
            <p>Convert YouTube videos or entire playlists to presentation slides</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('single')">📱 Single Video</button>
            <button class="tab" onclick="switchTab('playlist')">📋 Playlist</button>
        </div>
        
        <!-- Single Video Tab -->
        <div id="single-tab" class="tab-content active">
            <form id="singleForm">
                <div class="form-group">
                    <label for="singleVideoUrl">YouTube Video URL</label>
                    <input type="text" id="singleVideoUrl" placeholder="https://www.youtube.com/watch?v=..." required>
                    <div class="help-text">Paste any YouTube video URL here</div>
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
                </div>
                
                <button type="submit" id="singleBtn">🚀 Convert Video</button>
            </form>
        </div>
        
        <!-- Playlist Tab -->
        <div id="playlist-tab" class="tab-content">
            <form id="playlistForm">
                <div class="form-group">
                    <label for="playlistUrl">YouTube Playlist URL</label>
                    <input type="text" id="playlistUrl" placeholder="https://www.youtube.com/playlist?list=..." required>
                    <div class="help-text">Paste YouTube playlist URL here</div>
                </div>
                
                <div class="settings">
                    <div class="form-group">
                        <label for="playlistThreshold">Similarity Threshold</label>
                        <input type="number" id="playlistThreshold" min="0.80" max="0.99" step="0.01" value="0.90">
                        <div class="help-text">Lower = more slides</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="playlistInterval">Frame Interval</label>
                        <input type="number" id="playlistInterval" min="15" max="120" value="30">
                        <div class="help-text">Higher = fewer slides</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="maxVideos">Max Videos to Process</label>
                    <input type="number" id="maxVideos" min="1" max="50" value="10">
                    <div class="help-text">Limit processing to avoid timeouts (recommended: 5-10)</div>
                </div>
                
                <button type="submit" id="playlistBtn">🎬 Convert Playlist</button>
            </form>
            
            <div id="playlistInfo" style="display: none;"></div>
        </div>
        
        <div id="status" class="status">
            <h4 id="statusTitle">Processing...</h4>
            <p id="statusText">Starting conversion...</p>
            <div class="progress">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            <div id="downloadSection"></div>
        </div>
    </div>

    <script>
        let currentTaskId = null;
        let statusInterval = null;
        let activeTab = 'single';
        
        function switchTab(tab) {
            // Update active tab
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
        
        document.getElementById('singleForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const videoUrl = document.getElementById('singleVideoUrl').value.trim();
            const threshold = parseFloat(document.getElementById('singleThreshold').value);
            const interval = parseInt(document.getElementById('singleInterval').value);
            
            if (!videoUrl) {
                alert('Please enter a YouTube video URL');
                return;
            }
            
            await startConversion({
                type: 'single',
                video_url: videoUrl,
                threshold: threshold,
                interval: interval
            }, 'singleBtn');
        };
        
        document.getElementById('playlistForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const playlistUrl = document.getElementById('playlistUrl').value.trim();
            const threshold = parseFloat(document.getElementById('playlistThreshold').value);
            const interval = parseInt(document.getElementById('playlistInterval').value);
            const maxVideos = parseInt(document.getElementById('maxVideos').value);
            
            if (!playlistUrl) {
                alert('Please enter a YouTube playlist URL');
                return;
            }
            
            if (!playlistUrl.includes('playlist') && !playlistUrl.includes('list=')) {
                alert('Please enter a valid YouTube playlist URL');
                return;
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
                    <h4>📋 Playlist: ${info.title}</h4>
                    <p>👤 Channel: ${info.uploader}</p>
                    <p>📹 Videos to process: ${info.video_count}</p>
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
                    titleEl.textContent = 'Queued';
                    textEl.textContent = 'Waiting to start...';
                    break;
                case 'processing':
                    if (task.type === 'playlist') {
                        titleEl.textContent = 'Converting Playlist';
                        textEl.textContent = `Processing videos... (${task.current_video || 0}/${task.total_videos || '?'})`;
                    } else {
                        titleEl.textContent = 'Converting Video';
                        textEl.textContent = 'Extracting frames and creating slides...';
                    }
                    break;
                case 'completed':
                    titleEl.textContent = '✅ Conversion Complete!';
                    if (task.type === 'playlist') {
                        textEl.textContent = `Successfully processed ${task.output_files?.length || 0} videos.`;
                    } else {
                        textEl.textContent = 'Your PowerPoint is ready for download.';
                    }
                    break;
                case 'failed':
                    titleEl.textContent = '❌ Conversion Failed';
                    textEl.textContent = task.error || 'An error occurred';
                    break;
            }
            
            const progress = task.progress || 0;
            progressBar.style.width = progress + '%';
        }
        
        function showSuccess(task) {
            const downloadSection = document.getElementById('downloadSection');
            
            if (task.type === 'playlist' && task.output_files && task.output_files.length > 0) {
                let downloadHtml = `
                    <h4>📥 Download Options:</h4>
                    <a href="/download/${task.id}/all" class="download zip">📦 Download All (ZIP)</a><br><br>
                    <h5>Individual Files:</h5>
                `;
                
                task.output_files.slice(0, 10).forEach((file, index) => {
                    downloadHtml += `
                        <a href="/download/${task.id}/${file}" class="download">📄 ${file}</a>
                    `;
                });
                
                if (task.output_files.length > 10) {
                    downloadHtml += `<p class="help-text">... and ${task.output_files.length - 10} more files</p>`;
                }
                
                downloadSection.innerHTML = downloadHtml;
            } else {
                downloadSection.innerHTML = `
                    <a href="/download/${task.id}" class="download">📥 Download PowerPoint</a>
                    <div class="help-text" style="margin-top: 10px;">
                        Task ID: ${task.id}<br>
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
                    btn.textContent = '🚀 Convert Video';
                } else {
                    btn.textContent = '🎬 Convert Playlist';
                }
            } else {
                // Reset all buttons
                document.getElementById('singleBtn').disabled = false;
                document.getElementById('singleBtn').textContent = '🚀 Convert Video';
                document.getElementById('playlistBtn').disabled = false;
                document.getElementById('playlistBtn').textContent = '🎬 Convert Playlist';
            }
        }
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
            **kwargs
        }
        return task_id
    
    def update_task(self, task_id, **kwargs):
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
    
    def get_task(self, task_id):
        return self.tasks.get(task_id)

task_manager = SimpleTaskManager()

def process_single_video_background(task_id, video_url, threshold, interval):
    """Background single video processing"""
    try:
        print(f"Starting single video task {task_id}: {video_url}")
        task_manager.update_task(task_id, status='processing', progress=10)
        
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

def process_playlist_background(task_id, playlist_url, threshold, interval, max_videos):
    """Background playlist processing"""
    try:
        print(f"Starting playlist task {task_id}: {playlist_url}")
        task_manager.update_task(task_id, status='processing', progress=5)
        
        converter = VideoToPPTConverter(
            similarity_threshold=threshold,
            min_frame_interval=interval
        )
        
        # Create playlist output directory
        playlist_output_dir = os.path.join('outputs', f"playlist_{task_id}")
        os.makedirs(playlist_output_dir, exist_ok=True)
        
        task_manager.update_task(task_id, progress=10)
        
        # Process playlist
        results = converter.process_playlist(
            playlist_url=playlist_url,
            output_dir=playlist_output_dir,
            max_videos=max_videos,
            cleanup_temp=True
        )
        
        # Update task with results
        output_files = []
        if results['processed_videos']:
            for video in results['processed_videos']:
                filename = os.path.basename(video['output_path'])
                output_files.append(filename)
                
                # Update progress during processing
                current_video = len(output_files)
                total_videos = results['total_videos']
                progress = 10 + (current_video / total_videos) * 80
                task_manager.update_task(
                    task_id, 
                    current_video=current_video,
                    total_videos=total_videos,
                    progress=min(90, progress)
                )
        
        # Create ZIP file of all presentations
        if output_files:
            zip_filename = f"playlist_{task_id}_all.zip"
            zip_path = os.path.join('outputs', zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in output_files:
                    file_path = os.path.join(playlist_output_dir, filename)
                    if os.path.exists(file_path):
                        zipf.write(file_path, filename)
            
            output_files.append(zip_filename)
        
        task_manager.update_task(
            task_id,
            status='completed',
            progress=100,
            output_files=output_files,
            processed_count=len(results['processed_videos']),
            failed_count=len(results['failed_videos'])
        )
        
        print(f"Playlist task {task_id}: Completed successfully")
        
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
            interval = int(data.get('interval', 30))
            max_videos = int(data.get('max_videos', 10))
            
            if not playlist_url:
                return jsonify({'error': 'No playlist URL provided'}), 400
            
            if not ('playlist' in playlist_url or 'list=' in playlist_url):
                return jsonify({'error': 'Please provide a valid YouTube playlist URL'}), 400
            
            # Get playlist info first
            try:
                converter = VideoToPPTConverter()
                playlist_info = converter.get_playlist_info(playlist_url)
                
                # Limit videos if requested
                if max_videos and max_videos < playlist_info['video_count']:
                    playlist_info['video_count'] = max_videos
                
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
                interval=interval
            )
            
            # Start background processing
            thread = threading.Thread(
                target=process_single_video_background,
                args=(task_id, video_url, threshold, interval),
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
                return send_file(zip_path, as_attachment=True, download_name=f"playlist_presentations_{task_id}.zip")
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
    return jsonify({
        'status': 'healthy', 
        'active_tasks': len([t for t in task_manager.tasks.values() if t['status'] == 'processing']),
        'total_tasks': len(task_manager.tasks)
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    
    # Get port from environment (Railway provides PORT variable)
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🚀 Starting Video to PowerPoint Converter with Playlist Support")
    print(f"📡 Server starting on port {port}")
    print(f"🌐 Environment: {'Railway' if 'RAILWAY_' in str(os.environ) else 'Local'}")
    print(f"✨ Features: Single videos + Full playlist conversion")
    
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
