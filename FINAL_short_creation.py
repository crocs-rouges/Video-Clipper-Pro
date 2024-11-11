# !!!!
# carreful this code only works with NVIDIA GPU
# !!!!


"""
Video Clipper Pro - A GPU-accelerated video processing application
that combines two videos into vertical stack clips with precise duration control.

This application requires:
- NVIDIA GPU
- FFmpeg with CUDA support
- customtkinter library for modern UI
"""

# all importations required for the programme 
import os
import subprocess
from multiprocessing import Pool
import customtkinter as ctk
from tkinter import filedialog, messagebox
from functools import partial
import webbrowser
from datetime import datetime
import threading
import queue
import time

class ModernTheme:
    """
    Defines the visual theme constants for the application UI.
    These colors and measurements create a modern, dark theme appearance.
    """
    # Main colors
    BG_COLOR = "#1a1a1a"        # Dark background
    FG_COLOR = "#ffffff"        # White text
    ACCENT_COLOR = "#00ff9d"    # Bright green accent
    BUTTON_BG = "#2d2d2d"       # Darker button background
    ENTRY_BG = "#333333"        # Dark input field background
    HOVER_COLOR = "#404040"     # Light hover effect
    
    # Widget settings
    CORNER_RADIUS = 8           # Rounded corners
    PADDING = 20               # Consistent spacing
    BORDER_WIDTH = 1           # Thin borders
    
    # Widget settings
    CORNER_RADIUS = 8
    PADDING = 20
    BORDER_WIDTH = 1

def check_ffmpeg_gpu() -> bool:
    """
    Verifies if FFmpeg is properly configured for GPU encoding using NVIDIA CUDA.
    
    Returns:
        bool: True if GPU encoding is available, False otherwise
    """
    try:
        # Test FFmpeg GPU capabilities with a minimal encoding task
        test_cmd = [
            FFMPEG_PATH,
            '-hide_banner',
            '-hwaccel', 'cuda',
            '-hwaccel_output_format', 'cuda',
            '-f', 'lavfi',
            '-i', 'nullsrc=s=256x256:d=1',
            '-c:v', 'h264_nvenc',
            '-f', 'null',
            '-'
        ]
        subprocess.run(test_cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def get_video_resolution(ffprobe_path, video_path) -> tuple:
    """
    Gets the resolution of a video file using ffprobe.
    
    Args:
        ffprobe_path (str): Path to ffprobe executable
        video_path (str): Path to video file
    
    Returns:
        tuple: Width and height of the video as integers
    """
    command = [
        ffprobe_path, '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=s=x:p=0',
        video_path
    ]
    resolution = subprocess.check_output(command).decode('utf-8').strip()
    width, height = map(int, resolution.split('x'))
    return width, height

def create_segment(ffmpeg_path, ffprobe_path, args) -> bool:
    """
    Creates a video segment by combining main and overlay videos with specific parameters.
    
    Args:
        ffmpeg_path (str): Path to ffmpeg executable
        ffprobe_path (str): Path to ffprobe executable
        args (tuple): Contains (start_time, input_video_path, overlay_video_path,
                              segment_duration, output_dir, segment_index, name_vid)
    
    Returns:
        bool: True if segment creation was successful, False otherwise
    """
    try:
        start_time, input_video_path, overlay_video_path, segment_duration, output_dir, segment_index, name_vid = args
        
        # Get video resolutions
        main_width, main_height = get_video_resolution(ffprobe_path, input_video_path)
        overlay_width, overlay_height = get_video_resolution(ffprobe_path, overlay_video_path)

        # Calculate aspect ratios
        main_aspect_ratio = main_width / main_height
        overlay_aspect_ratio = overlay_width / overlay_height
        target_aspect_ratio = 9 / 16

        # Calculate crop filters
        if main_aspect_ratio > target_aspect_ratio:
            new_main_width = int(main_height * target_aspect_ratio)
            crop_main_filter = f"crop={new_main_width}:{main_height}:(in_w-{new_main_width})/2:0"
        else:
            new_main_height = int(main_width / target_aspect_ratio)
            crop_main_filter = f"crop={main_width}:{new_main_height}:0:(in_h-{new_main_height})/2"

        if overlay_aspect_ratio > target_aspect_ratio:
            new_overlay_width = int(overlay_height * target_aspect_ratio)
            crop_overlay_filter = f"crop={new_overlay_width}:{overlay_height}:(in_w-{new_overlay_width})/2:0"
        else:
            new_overlay_height = int(overlay_width / target_aspect_ratio)
            crop_overlay_filter = f"crop={overlay_width}:{new_overlay_height}:0:(in_h-{new_overlay_height})/2"

        output_path = os.path.join(output_dir, f"{name_vid}_{segment_index}.mp4")

        # FFmpeg command with optimized GPU encoding settings
        command = [
            ffmpeg_path,
            '-hwaccel', 'cuda',                # Enable CUDA acceleration
            '-hwaccel_output_format', 'cuda',  # Keep processing on GPU
            '-ss', str(start_time),
            '-t', str(segment_duration),
            '-i', input_video_path,
            '-ss', '65',                       # Start overlay video at 65 seconds
            '-t', str(segment_duration),
            '-i', overlay_video_path,
            '-filter_complex',
            f"[0:v]{crop_main_filter},scale=1080:1280[v0]; [1:v]{crop_overlay_filter},scale=1080:640[v1]; [v0][v1]vstack=inputs=2",
            '-c:v', 'h264_nvenc',             # NVIDIA encoder
            '-preset', 'p7',                   # Highest quality
            '-rc', 'vbr',                      # Variable bitrate
            '-cq', '19',                       # Quality level
            '-b:v', '5M',                      # Target bitrate
            '-maxrate', '10M',                 # Maximum bitrate
            '-bufsize', '10M',                 # Buffer size
            '-profile:v', 'high',              # High profile
            '-pix_fmt', 'yuv420p',            # Standard format
            '-movflags', '+faststart',        # Web playback optimization
            output_path
        ]

        
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error output: {result.stderr}")
            return False

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error creating segment {segment_index}: {str(e)}")
        return False



class ModernVideoClipper:
    """
    Main application class for the Video Clipper Pro.
    Provides a modern UI for combining and processing videos using GPU acceleration.
    """
    def __init__(self):
        # customtkinter Configuration 
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # main window creation
        self.root = ctk.CTk()
        self.root.title("Video Clipper Pro")
        self.root.geometry("900x800")
        self.processing = False
        self.progress_queue = queue.Queue()
        
        # path variables
        self.paths = {
            'input_video': "",
            'overlay_video': "",
            'output_dir': ""
        }
        
        self.path_labels = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main UI layout and components."""
        self.main_frame = ctk.CTkFrame(
            self.root,
            corner_radius=ModernTheme.CORNER_RADIUS,
            fg_color="transparent"
        )
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Titre
        self.title = ctk.CTkLabel(
            self.main_frame,
            text="VIDEO CLIPPER PRO",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.title.pack(pady=20)
        
        # Sections
        self.create_file_selection_ui()
        self.create_parameters_ui()
        self.create_progress_ui()
        self.create_action_buttons()
        
    def create_file_selection_ui(self):
        """Create the file selection section of the UI."""
        file_frame = ctk.CTkFrame(self.main_frame)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        for label_text, path_type in [
            ("MAIN VIDEO", 'input_video'),
            ("OVERLAY VIDEO", 'overlay_video'),
            ("OUTPUT FOLDER", 'output_dir')
        ]:
            section_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
            section_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                section_frame,
                text=label_text,
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor="w")
            
            path_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            path_frame.pack(fill="x", pady=(5, 0))
            
            self.path_labels[path_type] = ctk.CTkLabel(
                path_frame,
                text="Any file selected",
                font=ctk.CTkFont(size=12)
            )
            self.path_labels[path_type].pack(side="left", expand=True, anchor="w")
            
            ctk.CTkButton(
                path_frame,
                text="PARCOURIR",
                command=lambda pt=path_type: self.select_file(pt),
                width=120,
                height=32
            ).pack(side="right", padx=5)
            
    def create_parameters_ui(self):
        """Create the parameter input section of the UI."""
        param_frame = ctk.CTkFrame(self.main_frame)
        param_frame.pack(fill="x", padx=20, pady=10)
        
        # Name of the project
        name_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            name_frame,
            text="NAME OF THE PROJECT",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Enter the name of the project",
            height=35
        )
        self.name_entry.pack(fill="x", pady=(5, 0))
        
        # Parameters of numworkers
        settings_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        settings_frame.pack(fill="x", pady=10)
        
        duration_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        duration_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            duration_frame,
            text="DURÉE (s)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        self.duration_entry = ctk.CTkEntry(
            duration_frame,
            placeholder_text="59",
            width=100,
            height=35
        )
        self.duration_entry.pack(pady=(5, 0))
        self.duration_entry.insert(0, "59")
        
        workers_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        workers_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            workers_frame,
            text="WORKERS",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        self.workers_entry = ctk.CTkEntry(
            workers_frame,
            placeholder_text="4",
            width=100,
            height=35
        )
        self.workers_entry.pack(pady=(5, 0))
        self.workers_entry.insert(0, "4")
        
    def create_progress_ui(self):
        """Create the progress tracking section of the UI."""
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress = ctk.CTkProgressBar(
            progress_frame,
            mode="determinate",
            height=15
        )
        self.progress.pack(fill="x", pady=10)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="En attente...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
    def create_action_buttons(self):
        """Create the main action buttons section of the UI."""
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="CREATE CLIPS",
            command=self.create_clips,
            width=160,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="OPEN FOLDER",
            command=self.open_output_folder,
            width=160,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)

    def select_file(self, path_type):
        """
        Open a file dialog for selecting input files or output directory.
        
        Args:
            path_type (str): Type of path to select ('input_video', 'overlay_video', or 'output_dir')
        """
        if path_type == 'output_dir':
            filename = filedialog.askdirectory(title="select output folder")
        else:
            filename = filedialog.askopenfilename(
                title=f"Sélectionnez la {path_type.replace('_', ' ')}",
                filetypes=[("video file", "*.mkv *.mp4 *.avi"), ("all the files", "*.*")]
            )
            
        if filename:
            self.paths[path_type] = filename
            self.path_labels[path_type].configure(
                text=os.path.basename(filename) if path_type != 'output_dir' else filename
            )

    def update_progress(self):
        """Update the progress bar and status label from the progress queue."""
        if self.processing:
            try:
                while True:  # empty the queu for all the messages
                    progress, message = self.progress_queue.get_nowait()
                    self.progress.set(progress)
                    self.status_label.configure(text=message)
            except queue.Empty:
                pass
            
            self.root.after(100, self.update_progress)  # verified in 100ms

    def process_videos(self):
        """
        Process videos in a separate thread.
        Handles the main video processing workflow including:
        - Creating output directory
        - Calculating segments
        - Managing worker pool
        - Updating progress
        """
        try:
            base_dir = self.paths['output_dir']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = self.name_entry.get()
            final_output_dir = os.path.join(base_dir, f"{project_name}_{timestamp}")
            os.makedirs(final_output_dir, exist_ok=True)

            input_video_path = self.paths['input_video']
            overlay_video_path = self.paths['overlay_video']
            segment_duration = int(self.duration_entry.get())
            num_workers = int(self.workers_entry.get())

            # Get video duration
            command = [
                FFPROBE_PATH, '-v', 'error', '-show_entries',
                'format=duration', '-of',
                'default=noprint_wrappers=1:nokey=1', input_video_path
            ]
            main_video_duration = float(subprocess.check_output(command).strip())
            segment_starts = list(range(0, int(main_video_duration), segment_duration))
            num_segments = len(segment_starts)

            args = [
                (start_time, input_video_path, overlay_video_path, segment_duration, 
                 final_output_dir, i + 1, project_name) 
                for i, start_time in enumerate(segment_starts)
            ]

            segment_creator = partial(create_segment, FFMPEG_PATH, FFPROBE_PATH)
            
            with Pool(num_workers) as p:
                results = []
                for i, result in enumerate(p.imap(segment_creator, args)):
                    results.append(result)
                    progress = (i + 1) / num_segments
                    message = f"GPU Progression : {i+1}/{num_segments} clips created"
                    self.progress_queue.put((progress, message))
                    time.sleep(0.1)  # little delay for avoiding the queu

            
            if all(results):
                self.root.after(0, lambda: [
                    self.status_label.configure(text="clip creation finish with (GPU)!"),
                    messagebox.showinfo("Succès", 
                                      f"ALL the clips was created with succed!\n"
                                      f"output folder: {final_output_dir}"),
                    webbrowser.open(final_output_dir)
                ])
            else:
                self.root.after(0, lambda: [
                    self.status_label.configure(text="Some clips could not be created"),
                    messagebox.showwarning("Warning", "Some segments could not be created.")
                ])

        except Exception as e:
            self.root.after(0, lambda: [
                self.status_label.configure(text="An error has occurred"),
                messagebox.showerror("Error", f"An error has occurred : {str(e)}")
            ])
        finally:
            self.processing = False

    def create_clips(self):
        """
        Initialize and start the video processing operation.
        Validates inputs and GPU availability before starting.
        """
        if not self.validate_inputs():
            return

        if not check_ffmpeg_gpu():
            messagebox.showerror("Error", "FFmpeg is not configured properly for GPU encoding. "
                                "Make sure CUDA and NVIDIA codecs are installed.")
            return

        # Reset progress
        self.progress.set(0)
        self.status_label.configure(text="Starting treatment...")
        
        # start the treatement in separate thread
        self.processing = True
        processing_thread = threading.Thread(target=self.process_videos)
        processing_thread.daemon = True  # the thread will stop at the end of the programm
        processing_thread.start()
        
        # update progressbar
        self.update_progress()

    def validate_inputs(self) -> bool:
        """
        Validate all user inputs before processing.
        
        Returns:
            bool: True if all inputs are valid, False otherwise
        """
        if not self.paths['input_video']:
            messagebox.showerror("Error", "you need to select a main video")
            return False
        if not self.paths['overlay_video']:
            messagebox.showerror("Error", "select an overlay video")
            return False
        if not self.paths['output_dir']:
            messagebox.showerror("Error", "select an output folder")
            return False
        if not self.name_entry.get():
            messagebox.showerror("Error", "Veuillez entrer un nom pour le projet")
            return False
        try:
            duration = int(self.duration_entry.get())
            workers = int(self.workers_entry.get())
            if duration <= 0 or workers <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Duration and number of workers must be positive numbers")
            return False
        return True
    
    def open_output_folder(self):
        """Open the output folder in the system's file explorer."""
        output_dir = self.paths['output_dir']
        if output_dir and os.path.exists(output_dir):
            webbrowser.open(output_dir)
        else:
            messagebox.showwarning("carreful", "any output folder selected")
            
    def run(self):
        """Start the application main loop."""
        self.root.mainloop()

def main():
    """
    Main entry point for the application.
    Initializes FFmpeg paths and starts the application.
    """
    global FFMPEG_PATH, FFPROBE_PATH
    FFMPEG_PATH = "C:/path_programms/ffmpeg.exe"  # Adjust for your installation
    FFPROBE_PATH = "C:/path_programms/ffprobe.exe"  # Adjust for your installation

    app = ModernVideoClipper()
    app.run()

if __name__ == "__main__":
    main()