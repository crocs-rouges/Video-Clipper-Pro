import os
import subprocess
from multiprocessing import Pool
import sys

FFMPEG_PATH = "C:/path_programms/ffmpeg.exe"
FFPROBE_PATH = "C:/path_programms/ffprobe.exe"

def check_ffmpeg_executables():
    try:
        subprocess.run([FFMPEG_PATH, '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run([FFPROBE_PATH, '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise FileNotFoundError("ffmpeg or ffprobe not found. Please ensure the paths are correct and the executables are installed.")
    except subprocess.CalledProcessError as e:
        raise EnvironmentError(f"Error running ffmpeg or ffprobe: {e}")

def get_video_resolution(video_path):
    command = [
        FFPROBE_PATH, '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=s=x:p=0',
        video_path
    ]
    resolution = subprocess.check_output(command).decode('utf-8').strip()
    width, height = map(int, resolution.split('x'))
    return width, height

def create_segment(args):
    try:
        start_time, input_video_path, overlay_video_path, segment_duration, output_dir, num_workers, segment_index, name_vid = args

        main_width, main_height = get_video_resolution(input_video_path)
        overlay_width, overlay_height = get_video_resolution(overlay_video_path)

        main_aspect_ratio = main_width / main_height
        overlay_aspect_ratio = overlay_width / overlay_height

        target_aspect_ratio = 9 / 16

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

        command = [
            FFMPEG_PATH,
            '-hwaccel', 'cuda',
            '-ss', str(start_time),
            '-t', str(segment_duration),
            '-i', input_video_path,
            '-ss', '65',  # start overlay video from 65th second
            '-t', str(segment_duration),
            '-i', overlay_video_path,
            '-filter_complex', 
            f"[0:v]{crop_main_filter},scale=1080:1280[v0]; [1:v]{crop_overlay_filter},scale=1080:640[v1]; [v0][v1]vstack=inputs=2",
            '-s', '1080x1920',  # Set the output resolution to 1080x1920
            '-c:v', 'h264_nvenc',
            '-b:v', '5M',  # Adjust bitrate as necessary
            '-pix_fmt', 'yuv420p',
            output_path
        ]

        subprocess.run(command, check=True)
        
        print(f"Segment {segment_index} created successfully at {output_path}.")

    except subprocess.CalledProcessError as e:
        print(f"Error creating segment {segment_index}:", str(e))

def create_clips(input_video_path, overlay_video_path, output_dir, segment_duration, name_vid, num_workers=4):
    check_ffmpeg_executables()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    command = [
        FFPROBE_PATH, '-v', 'error', '-show_entries',
        'format=duration', '-of',
        'default=noprint_wrappers=1:nokey=1', input_video_path
    ]
    main_video_duration = float(subprocess.check_output(command).strip())
    print(f"Main video duration: {main_video_duration} seconds")

    segment_starts = list(range(0, int(main_video_duration), segment_duration))
    print(f"Segment start times: {segment_starts}")

    args = [(start_time, input_video_path, overlay_video_path, segment_duration, output_dir, num_workers, i + 1, name_vid) for i, start_time in enumerate(segment_starts)]
    
    with Pool(num_workers) as p:
        p.map(create_segment, args)

if __name__ == "__main__":
    # Récupérer les arguments depuis la ligne de commande (Electron va les passer en argument)
    input_video_path = sys.argv[1]  # Chemin de la vidéo d'entrée
    name_vid = sys.argv[2]  # Nom de la vidéo finale (sans extension)
    overlay_video_path = sys.argv[3]  # Chemin de la vidéo overlay
    output_dir = sys.argv[4]  # Dossier de sortie
    segment_duration = int(sys.argv[5])  # Durée de chaque segment
    num_workers = int(sys.argv[6])  # Nombre de processus parallèles

    # Générer les segments
    create_clips(input_video_path, overlay_video_path, output_dir, segment_duration, name_vid, num_workers)
