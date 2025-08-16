# simple_web_app.py - Web interface for video to PowerPoint converter
from flask import Flask, request, jsonify, render_template_string, send_file
import os
import uuid
import threading
from video_to_ppt_converter import VideoToPPTConverter
import time

app = Flask(__name__)

# In-memory task storage
tasks = {}

# HTML template
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
            max-width: 600px; 
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
        .form-section { padding: 30px; }
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
            margin-top: 15px;
            font-weight: 600;
        }
        .help-text { 
            font-size: 14px; 
            color: #6c757d; 
            margin-top: 5px; 
        }
        @media (max-width: 768px) {
            .settings { grid-template-columns: 1fr; }
            .header h1 { font-size: 1.8rem; }
            .form-section { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 Video to PowerPoint</h1>
            <p>Convert YouTube videos to presentation slides</p>
        </div>
        
        <div class="form-section">
            <form id="convertForm">
                <div class="form-group">
                    <label for="videoUrl">YouTube Video URL</label>
                    <input type="text" id="videoUrl" placeholder="https://www.youtube.com/watch?v=..." required>
                    <div class="help-text">Paste any YouTube video URL here</div>
                </div>
                
                <div class="settings">
                    <div class="form-group">
                        <label for="threshold">Similarity Threshold</label>
                        <input type="number" id="threshold" min="0.80" max="0.99" step="0.01" value="0.90">
                        <div class="help-text">Lower = more slides</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="interval">Frame Interval</label>
                        <input type="number" id="interval" min="15" max="120" value="30">
                        <div class="help-text">Higher = fewer slides</div>
                    </div>
                </div>
                
                <button type="submit" id="convertBtn">🚀 Convert to PowerPoint</button>
            </form>
            
            <div id="status" class="status">
                <h4 id="statusTitle">Processing...</h4>
                <p id="statusText">Starting conversion...</p>
                <div class="progress">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                <div id="downloadSection"></div>
            </div>
        </div>
    </div>

    <script>
        let currentTaskId = null;
        let statusInterval = null;
        
        document.getElementById('convertForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const videoUrl = document.getElementById('videoUrl').value.trim();
            const threshold = parseFloat(document.getElementById('threshold').value);
            const interval = parseInt(document.getElementById('interval').value);
            
            if (!videoUrl) {
                alert('Please enter a YouTube video URL');
                return;
            }
            
            if (!videoUrl.includes('youtube.com') && !videoUrl.includes('youtu.be')) {
                alert('Please enter a valid YouTube URL');
                return;
            }
            
            try {
                // Disable form
                const btn = document.getElementById('convertBtn');
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
                    body: JSON.stringify({ 
                        video_url: videoUrl, 
                        threshold: threshold,
                        interval: interval
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Conversion failed');
                }
                
                const data = await response.json();
                currentTaskId = data.task_id;
                
                // Start status checking
                checkStatus();
                statusInterval = setInterval(checkStatus, 2000);
                
            } catch (error) {
                showError('Failed to start conversion: ' + error.message);
                resetForm();
            }
        };
        
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
                    titleEl.textContent = 'Converting Video';
                    textEl.textContent = 'Extracting frames and creating slides...';
                    break;
                case 'completed':
                    titleEl.textContent = '✅ Conversion Complete!';
                    textEl.textContent = 'Your PowerPoint is ready for download.';
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
            downloadSection.innerHTML = `
                <a href="/download/${task.id}" class="download">📥 Download PowerPoint</a>
                <div class="help-text" style="margin-top: 10px;">
                    Task ID: ${task.id}<br>
                    Right-click download link and "Save As" if needed
                </div>
            `;
        }
        
        function showError(message) {
            const statusDiv = document.getElementById('status');
            statusDiv.style.display = 'block';
            statusDiv.className = 'status failed';
            document.getElementById('statusTitle').textContent = '❌ Error';
            document.getElementById('statusText').textContent = message;
        }
        
        function resetForm() {
            const btn = document.getElementById('convertBtn');
            btn.disabled = false;
            btn.textContent = '🚀 Convert to PowerPoint';
        }
    </script>
</body>
</html>
'''

class SimpleTaskManager:
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, task_id, video_url, threshold, interval):
        self.tasks[task_id] = {
            'id': task_id,
            'status': 'pending',
            'progress': 0,
            'video_url': video_url,
            'threshold': threshold,
            'interval': interval,
            'output_file': None,
            'error': None
        }
        return task_id
    
    def update_task(self, task_id, **kwargs):
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
    
    def get_task(self, task_id):
        return self.tasks.get(task_id)

task_manager = SimpleTaskManager()

def process_video_background(task_id, video_url, threshold, interval):
    """Background video processing with progress updates"""
    try:
        print(f"Starting task {task_id}: {video_url}")
        task_manager.update_task(task_id, status='processing', progress=10)
        
        # Initialize converter with user settings
        converter = VideoToPPTConverter(
            similarity_threshold=threshold,
            min_frame_interval=interval
        )
        
        task_manager.update_task(task_id, progress=25)
        print(f"Task {task_id}: Converter initialized")
        
        # Process video
        output_filename = f"presentation_{task_id}.pptx"
        output_path = os.path.join('outputs', output_filename)
        
        task_manager.update_task(task_id, progress=50)
        print(f"Task {task_id}: Starting video processing")
        
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
                output_file=output_filename
            )
            print(f"Task {task_id}: Completed successfully")
        else:
            raise Exception("Failed to create PowerPoint file")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Task {task_id}: Failed with error: {error_msg}")
        task_manager.update_task(
            task_id,
            status='failed',
            error=error_msg
        )

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        video_url = data.get('video_url', '').strip()
        threshold = float(data.get('threshold', 0.90))
        interval = int(data.get('interval', 30))
        
        if not video_url:
            return jsonify({'error': 'No video URL provided'}), 400
        
        if not ('youtube.com' in video_url or 'youtu.be' in video_url):
            return jsonify({'error': 'Please provide a valid YouTube URL'}), 400
        
        # Validate parameters
        if not (0.8 <= threshold <= 0.99):
            threshold = 0.90
        if not (15 <= interval <= 120):
            interval = 30
        
        # Create unique task ID
        task_id = str(uuid.uuid4())[:8]
        task_manager.create_task(task_id, video_url, threshold, interval)
        
        # Start background processing
        thread = threading.Thread(
            target=process_video_background,
            args=(task_id, video_url, threshold, interval),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'task_id': task_id, 
            'status': 'started',
            'message': 'Conversion started successfully'
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
def download(task_id):
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Conversion not completed yet'}), 400
    
    if not task['output_file']:
        return jsonify({'error': 'No output file available'}), 404
    
    file_path = os.path.join('outputs', task['output_file'])
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
    
    print(f"🚀 Starting Video to PowerPoint Converter")
    print(f"📡 Server starting on port {port}")
    print(f"🌐 Environment: {'Railway' if 'RAILWAY_' in str(os.environ) else 'Local'}")
    
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
    
    # Run the Flask app

    app.run(host='0.0.0.0', port=port, debug=False)
