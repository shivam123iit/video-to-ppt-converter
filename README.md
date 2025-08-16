# 🎥 Video to PowerPoint Converter

Convert YouTube videos to PowerPoint presentations automatically using intelligent frame extraction.

## ✨ Features

- 🎯 **YouTube Integration** - Direct video URL input
- 🤖 **Smart Frame Detection** - AI-powered slide extraction
- 🚀 **Cloud Ready** - Deploy to Railway/Render in minutes
- 📱 **Mobile Friendly** - Responsive web interface
- ⚡ **Fast Processing** - Optimized for speed
- 🎛️ **Customizable** - Adjustable similarity thresholds

## 🚀 Quick Deploy

### Option 1: Railway.app (Recommended)
1. Fork this repository
2. Sign up at [railway.app](https://railway.app)
3. Connect your GitHub repo
4. Deploy automatically!
5. **Cost: ~$10/month**

### Option 2: Render.com
1. Fork this repository
2. Sign up at [render.com](https://render.com)
3. Create new "Web Service"
4. Connect your repo
5. **Cost: ~$7/month**

## 💻 Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/video-to-ppt-converter.git
cd video-to-ppt-converter

# Install dependencies
pip install -r requirements.txt

# Run locally
python simple_web_app.py

# Open http://localhost:8000
```

## 📖 How to Use

1. **Enter YouTube URL** - Paste any YouTube video link
2. **Adjust Settings**:
   - **Similarity Threshold** (0.80-0.99): Lower = more slides
   - **Frame Interval** (15-120): Higher = fewer slides
3. **Click Convert** - Processing starts automatically
4. **Download PowerPoint** - Ready in 2-5 minutes!

## ⚙️ Configuration Examples

### Educational Videos
- **Threshold**: 0.92 (conservative)
- **Interval**: 45 (longer pauses)
- **Result**: Clean slides for lectures

### Tutorial Videos  
- **Threshold**: 0.88 (sensitive)
- **Interval**: 20 (quick changes)
- **Result**: Captures step-by-step actions

### Presentation Videos
- **Threshold**: 0.95 (very conservative)
- **Interval**: 60 (slide transitions)
- **Result**: Traditional presentation format

## 🔧 Technical Details

### Architecture
- **Backend**: Flask + OpenCV + scikit-image
- **Frontend**: Vanilla JavaScript + responsive CSS
- **Video Processing**: yt-dlp for downloads
- **Deployment**: Docker containerized

### Performance
- **Local**: 10-15 minutes per video
- **Cloud**: 2-5 minutes per video
- **Parallel**: Multiple videos simultaneously
- **Storage**: Auto-cleanup temporary files

### Supported Formats
- ✅ YouTube videos (all resolutions)
- ✅ YouTube Shorts
- ✅ Unlisted videos (with URL)
- ❌ Private videos
- ❌ Age-restricted content

## 🛠️ Development

### File Structure
```
video-to-ppt-converter/
├── video_to_ppt_converter.py  # Core conversion logic
├── simple_web_app.py          # Web interface
├── Dockerfile                 # Container configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
├── outputs/                   # Generated PowerPoint files
└── temp/                      # Temporary processing files
```

### Environment Variables
```bash
PORT=8000                    # Server port (auto-set by hosting)
PYTHONUNBUFFERED=1          # Real-time logging
```

### API Endpoints
- `GET /` - Web interface
- `POST /convert` - Start conversion
- `GET /status/<task_id>` - Check progress
- `GET /download/<task_id>` - Download result
- `GET /health` - System health

## 🚨 Troubleshooting

### Common Issues

**"Video unavailable"**
- Video might be private or region-restricted
- Try different video URL
- Check if video exists

**"Conversion failed"**
- Video might be too long (>2 hours)
- Poor internet connection
- Server resource limits

**"No slides generated"**
- Lower similarity threshold (0.85-0.88)
- Reduce frame interval (20-30)
- Video might have static content

### Performance Tips

**For faster processing:**
- Use shorter videos (<30 minutes)
- Higher similarity threshold (0.92-0.95)
- Higher frame interval (45-60)

**For more detailed slides:**
- Lower similarity threshold (0.85-0.88)
- Lower frame interval (15-25)
- Educational/tutorial content works best

## 📊 Cost Breakdown

### Hosting Options
| Platform | CPU | RAM | Storage | Cost/Month |
|----------|-----|-----|---------|------------|
| Railway | 1-8 cores | 1-8GB | 100GB | $5-50 |
| Render | 1-4 cores | 1-4GB | 100GB | $7-85 |
| Heroku | 1-8 cores | 512MB-14GB | 10GB-1TB | $7-500 |

### Usage Estimates
- **Light usage** (1-5 videos/day): $7-15/month
- **Medium usage** (10-20 videos/day): $15-35/month  
- **Heavy usage** (50+ videos/day): $35-100/month

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙋‍♂️ Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/video-to-ppt-converter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/video-to-ppt-converter/discussions)
- **Email**: your-email@domain.com

## 🌟 Show Your Support

Give a ⭐️ if this project helped you!

---

**Made with ❤️ for content creators and educators**