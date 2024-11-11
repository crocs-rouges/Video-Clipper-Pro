import os
import subprocess
from multiprocessing import Pool
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from functools import partial
import webbrowser
from datetime import datetime

class ModernTheme:
    BG_COLOR = "#1a1a1a"
    FG_COLOR = "#ffffff"
    ACCENT_COLOR = "#00ff9d"
    BUTTON_BG = "#2d2d2d"
    ENTRY_BG = "#333333"
    HOVER_COLOR = "#404040"

    @staticmethod
    def apply_theme():
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure main theme colors
        style.configure('Modern.TFrame', background=ModernTheme.BG_COLOR)
        style.configure('Modern.TLabel', 
                       background=ModernTheme.BG_COLOR, 
                       foreground=ModernTheme.FG_COLOR)
        
        # Configure modern buttons
        style.configure('Modern.TButton',
                       background=ModernTheme.BUTTON_BG,
                       foreground=ModernTheme.FG_COLOR,
                       borderwidth=0,
                       focuscolor=ModernTheme.ACCENT_COLOR,
                       padding=10)
        
        style.map('Modern.TButton',
                  background=[('active', ModernTheme.HOVER_COLOR)],
                  foreground=[('active', ModernTheme.ACCENT_COLOR)])
        
        # Configure modern entries
        style.configure('Modern.TEntry',
                       fieldbackground=ModernTheme.ENTRY_BG,
                       foreground=ModernTheme.FG_COLOR,
                       insertcolor=ModernTheme.FG_COLOR,
                       borderwidth=0,
                       padding=8)
        
        # Configure modern progress bar
        style.configure('Modern.Horizontal.TProgressbar',
                       background=ModernTheme.ACCENT_COLOR,
                       troughcolor=ModernTheme.ENTRY_BG,
                       borderwidth=0)

def get_video_resolution(ffprobe_path, video_path):
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

def create_segment(ffmpeg_path, ffprobe_path, args):
    try:
        start_time, input_video_path, overlay_video_path, segment_duration, output_dir, segment_index, name_vid = args

        main_width, main_height = get_video_resolution(ffprobe_path, input_video_path)
        overlay_width, overlay_height = get_video_resolution(ffprobe_path, overlay_video_path)

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
            ffmpeg_path,
            '-hwaccel', 'cuda',
            '-ss', str(start_time),
            '-t', str(segment_duration),
            '-i', input_video_path,
            '-ss', '65',
            '-t', str(segment_duration),
            '-i', overlay_video_path,
            '-filter_complex',
            f"[0:v]{crop_main_filter},scale=1080:1280[v0]; [1:v]{crop_overlay_filter},scale=1080:640[v1]; [v0][v1]vstack=inputs=2",
            '-s', '1080x1920',
            '-c:v', 'h264_nvenc',
            '-b:v', '5M',
            '-pix_fmt', 'yuv420p',
            output_path
        ]

        subprocess.run(command, check=True)
        return True

    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la création du segment {segment_index} :", str(e))
        return False

class ModernVideoClipper:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Clipper Pro")
        self.root.geometry("800x600")
        self.root.configure(bg=ModernTheme.BG_COLOR)
        
        ModernTheme.apply_theme()
        
        self.setup_ui()
        
    def setup_ui(self):
        self.main_frame = ttk.Frame(self.root, style='Modern.TFrame', padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weight
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.paths = {
            'input_video': tk.StringVar(),
            'overlay_video': tk.StringVar(),
            'output_dir': tk.StringVar()
        }
        
        self.path_labels = {}
        
        # Title
        title_label = ttk.Label(self.main_frame, 
                               text="VIDEO CLIPPER PRO", 
                               style='Modern.TLabel',
                               font=('Helvetica', 24, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 30))

        # File selection section
        self.create_file_selection_ui()
        
        # Parameters section
        self.create_parameters_ui()
        
        # Progress section
        self.create_progress_ui()
        
        # Action buttons
        self.create_action_buttons()

    def create_file_selection_ui(self):
        row = 1
        for label_text, path_type in [
            ("VIDÉO PRINCIPALE", 'input_video'),
            ("VIDÉO OVERLAY", 'overlay_video'),
            ("DOSSIER DE SORTIE", 'output_dir')
        ]:
            ttk.Label(self.main_frame, 
                     text=label_text, 
                     style='Modern.TLabel',
                     font=('Helvetica', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10, 0))
            
            self.path_labels[path_type] = ttk.Label(
                self.main_frame, 
                text="Aucun fichier sélectionné",
                style='Modern.TLabel')
            self.path_labels[path_type].grid(row=row+1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
            
            ttk.Button(self.main_frame, 
                      text="PARCOURIR",
                      style='Modern.TButton',
                      command=lambda pt=path_type: self.select_file(pt)).grid(row=row+1, column=2, padx=5)
            
            row += 2

    def create_parameters_ui(self):
        # Nom du fichier
        ttk.Label(self.main_frame, 
                 text="NOM DU PROJET", 
                 style='Modern.TLabel',
                 font=('Helvetica', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(10, 0))
        self.name_entry = ttk.Entry(self.main_frame, 
                                  style='Modern.TEntry',
                                  width=30)
        self.name_entry.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Parameters frame
        params_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        params_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Durée des segments
        ttk.Label(params_frame, 
                 text="DURÉE (s)", 
                 style='Modern.TLabel',
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=0, padx=10)
        self.duration_entry = ttk.Entry(params_frame, 
                                      style='Modern.TEntry',
                                      width=10)
        self.duration_entry.insert(0, "59")
        self.duration_entry.grid(row=1, column=0, padx=10)
        
        # Nombre de workers
        ttk.Label(params_frame, 
                 text="WORKERS", 
                 style='Modern.TLabel',
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=1, padx=10)
        self.workers_entry = ttk.Entry(params_frame, 
                                     style='Modern.TEntry',
                                     width=10)
        self.workers_entry.insert(0, "4")
        self.workers_entry.grid(row=1, column=1, padx=10)

    def create_progress_ui(self):
        self.progress = ttk.Progressbar(self.main_frame, 
                                      style='Modern.Horizontal.TProgressbar',
                                      length=400, 
                                      mode='determinate')
        self.progress.grid(row=10, column=0, columnspan=3, pady=20, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(self.main_frame, 
                                    text="En attente...", 
                                    style='Modern.TLabel')
        self.status_label.grid(row=11, column=0, columnspan=3)

    def create_action_buttons(self):
        button_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        button_frame.grid(row=12, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, 
                  text="CRÉER LES CLIPS",
                  style='Modern.TButton',
                  command=self.create_clips).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, 
                  text="OUVRIR LE DOSSIER",
                  style='Modern.TButton',
                  command=self.open_output_folder).pack(side=tk.LEFT, padx=5)

    def select_file(self, path_type):
        if path_type == 'output_dir':
            filename = filedialog.askdirectory(title="Sélectionnez le dossier de sortie")
        else:
            filename = filedialog.askopenfilename(
                title=f"Sélectionnez la {path_type.replace('_', ' ')}",
                filetypes=[("Fichiers vidéo", "*.mkv *.mp4 *.avi"), ("Tous les fichiers", "*.*")]
            )
            
        if filename:
            self.paths[path_type].set(filename)
            self.path_labels[path_type].config(
                text=os.path.basename(filename) if path_type != 'output_dir' else filename
            )

    def open_output_folder(self):
        output_dir = self.paths['output_dir'].get()
        if output_dir and os.path.exists(output_dir):
            webbrowser.open(output_dir)
        else:
            messagebox.showwarning("Attention", "Aucun dossier de sortie sélectionné ou dossier inexistant")

    def create_clips(self):
        if not self.validate_inputs():
            return

        try:
            # Create output directory with timestamp
            base_dir = self.paths['output_dir'].get()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = self.name_entry.get()
            final_output_dir = os.path.join(base_dir, f"{project_name}_{timestamp}")
            os.makedirs(final_output_dir, exist_ok=True)

            input_video_path = self.paths['input_video'].get()
            overlay_video_path = self.paths['overlay_video'].get()
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

            self.progress['value'] = 0
            self.status_label.config(text="Création des clips en cours...")
            
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
                    self.progress['value'] = ((i + 1) / num_segments) * 100
                    self.status_label.config(text=f"Progression: {i+1}/{num_segments} clips créés")
                    self.root.update_idletasks()

            if all(results):
                self.status_label.config(text="Création des clips terminée avec succès!")
                messagebox.showinfo("Succès", 
                                  f"Tous les clips ont été créés avec succès!\n"
                                  f"Dossier de sortie: {final_output_dir}")
                webbrowser.open(final_output_dir)  # Ouvre automatiquement le dossier
            else:
                self.status_label.config(text="Certains clips n'ont pas pu être créés")
                messagebox.showwarning("Attention", "Certains segments n'ont pas pu être créés.")

        except Exception as e:
            self.status_label.config(text="Une erreur est survenue")
            messagebox.showerror("Erreur", f"Une erreur est survenue : {str(e)}")

    def validate_inputs(self):
        if not self.paths['input_video'].get():
            messagebox.showerror("Erreur", "Veuillez sélectionner une vidéo principale")
            return False
        if not self.paths['overlay_video'].get():
            messagebox.showerror("Erreur", "Veuillez sélectionner une vidéo overlay")
            return False
        if not self.paths['output_dir'].get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de sortie")
            return False
        if not self.name_entry.get():
            messagebox.showerror("Erreur", "Veuillez entrer un nom pour le projet")
            return False
        try:
            duration = int(self.duration_entry.get())
            workers = int(self.workers_entry.get())
            if duration <= 0 or workers <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Erreur", "La durée et le nombre de workers doivent être des nombres positifs")
            return False
        return True

def main():
    global FFMPEG_PATH, FFPROBE_PATH
    FFMPEG_PATH = "C:\path_programms/ffmpeg.exe"  # Ajustez selon votre installation
    FFPROBE_PATH = "C:\path_programms/ffprobe.exe"  # Ajustez selon votre installation

    root = tk.Tk()
    app = ModernVideoClipper(root)
    root.mainloop()

if __name__ == "__main__":
    main()