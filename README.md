
# Video Clipper Pro

A powerful GPU-accelerated video processing application that combines two videos into vertically stacked clips with precise duration control. Built with Python and optimized for NVIDIA GPUs.

![Video Clipper Pro Interface](assets/screenshots/VideoClipperPro.png "Video Clipper Pro Interface")

## Features

- 🎥 Combine two videos into vertically stacked clips (9:16 aspect ratio)
- ⚡ GPU-accelerated processing using NVIDIA CUDA
- 🎯 Precise duration control for output clips
- 🔄 Automatic aspect ratio adjustment and cropping
- 🎨 Modern, dark-themed user interface
- 📊 Real-time progress tracking
- 💪 Multi-threaded processing for optimal performance

## Requirements

### Hardware

- NVIDIA GPU (required for GPU acceleration)
- Minimum 8GB RAM recommended
- Sufficient storage space for video processing

### Software

- Python 3.8 or higher
- FFmpeg with NVIDIA GPU support
- NVIDIA CUDA Toolkit
- NVIDIA Video Codec SDK

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/video-clipper-pro.git
   cd video-clipper-pro
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/MacOS
   source venv/bin/activate
   ```

3. **Install required Python packages**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg with NVIDIA support**
   - Download FFmpeg builds with NVIDIA support from [here](https://www.gyan.dev/ffmpeg/builds/)
   - Extract the files
   - Add FFmpeg to your system PATH or update paths in the code:

     ```python
     FFMPEG_PATH = "C:/path_to/ffmpeg.exe"
     FFPROBE_PATH = "C:/path_to/ffprobe.exe"
     ```

5. **Install NVIDIA components**
   - Install [NVIDIA GPU Drivers](https://www.nvidia.com/Download/index.aspx)
   - Install [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
   - Install [NVIDIA Video Codec SDK](https://developer.nvidia.com/nvidia-video-codec-sdk)

## Usage

1. **Start the application**

   ```bash
   python FINAL_short_creation.py
   ```

2. **Select input files**
   - Click "BROWSE" to select your main video
   - Select an overlay video
   - Choose an output directory for the processed clips

3. **Configure settings**
   - Enter a project name
   - Set the desired clip duration (in seconds)
   - Adjust the number of workers (recommended: number of CPU cores - 3 or 4 to maximize GPU usage)

4. **Process videos**
   - Click "CREATE CLIPS" to start processing
   - Monitor progress in the progress bar
   - Output files will be created in the selected directory with timestamps

## Project Structure

```bash
video-clipper-pro/
├── FINAL_short_creation.py     # Main application file
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── assets/                     # Application assets
    └── screenshots/            # Application screenshots
```

## Configuration

### Video Processing Settings

Default settings in `create_segment()`:

- Output Resolution: 1080x1920 (9:16)
- Video Codec: H.264 (NVIDIA NVENC)
- Preset: p7 (highest quality)
- Bitrate: 5Mbps (target) / 10Mbps (max)
- Profile: High
- Pixel Format: YUV420P

These settings can be modified in the code to fit specific requirements.

## Troubleshooting

### Common Issues

1. **FFmpeg GPU Error**
   - Ensure NVIDIA drivers are up-to-date
   - Verify CUDA installation
   - Check that the FFmpeg build includes NVIDIA support

2. **Processing Performance**
   - Reduce the number of workers if experiencing stability issues
   - Ensure there is sufficient disk space for temporary files
   - Close other GPU-intensive applications

3. **Video Format Issues**
   - Ensure input videos are in supported formats (mp4, mkv, avi)
   - Check video codec compatibility
   - Verify video file integrity

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FFmpeg team for the powerful video processing library
- NVIDIA for CUDA and video processing capabilities
- CustomTkinter for the modern UI components

## Support

For support, questions, or feature requests:

- Open an issue in the GitHub repository
- Contact the development team at [trpcrocsrouges@gmail.com]

## Version History

- 1.0.0
  - Initial release
  - Basic video processing functionality
  - GPU acceleration support

## Future Improvements

- [ ] Add support for AMD GPUs
- [ ] Implement custom video filters
- [ ] Add batch processing capabilities
- [ ] Create preset configurations
- [ ] Add video preview functionality
- [ ] Implement audio processing options

---

**Note**: This project requires an NVIDIA GPU and proper CUDA setup for optimal performance. CPU-only processing is currently not supported.
