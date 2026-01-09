import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import platform
import subprocess
from moviepy.editor import AudioFileClip

# --- CROSS-PLATFORM SETUP ---
SYSTEM_OS = platform.system() 

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if SYSTEM_OS == "Windows":
    os.environ["IMAGEIO_FFMPEG_EXE"] = resource_path("ffmpeg.exe")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Simple Audio Converter")
        self.geometry("500x760") # Taller to fit Quality buttons
        self.resizable(False, False)
        
        self.input_path = ""
        self.output_folder = ""
        self.target_format = "mp3" 
        self.target_bitrate = "320k" # Default High

        # CODEC MAPPING
        self.codec_map = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "flac": "flac",
            "ogg": "libvorbis",
            "m4a": "aac",
            "wma": "wmav2"
        }

        icon_path = resource_path("myicon.ico")
        if os.path.exists(icon_path):
            self.after(200, lambda: self.iconbitmap(icon_path))

        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        ctk.CTkLabel(self, text="Simple Audio Converter", font=("Roboto", 24, "bold")).grid(row=0, column=0, pady=(30, 15))

        # 2. Big Select Button
        self.select_btn = ctk.CTkButton(self, text="📂 Click to Select Audio File", height=90, width=420, 
                                        font=("Roboto", 18, "bold"), fg_color="#2b2b2b", hover_color="#3a3a3a", 
                                        corner_radius=15, border_width=2, border_color="#444",
                                        command=self.browse_file)
        self.select_btn.grid(row=1, column=0, padx=40, pady=(10, 15))

        # 3. File Info Box (New Feature)
        self.file_box = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#333", width=420, height=40)
        self.file_box.grid(row=2, column=0, pady=(0, 20))
        self.file_box.grid_propagate(False) # Stop frame from shrinking

        self.file_label = ctk.CTkLabel(self.file_box, text="No file selected", text_color="gray", font=("Roboto", 13))
        self.file_label.place(relx=0.5, rely=0.5, anchor="center")

        # 4. Format Selection
        ctk.CTkLabel(self, text="Output Format:", font=("Roboto", 14, "bold")).grid(row=3, column=0, pady=(5, 5))
        
        self.fmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.fmt_frame.grid(row=4, column=0, pady=5)
        
        self.btn_mp3 = self.create_btn(self.fmt_frame, "MP3", lambda: self.set_format("mp3"), 0, 0)
        self.btn_wav = self.create_btn(self.fmt_frame, "WAV", lambda: self.set_format("wav"), 0, 1)
        self.btn_flac = self.create_btn(self.fmt_frame, "FLAC", lambda: self.set_format("flac"), 0, 2)
        
        self.btn_ogg = self.create_btn(self.fmt_frame, "OGG", lambda: self.set_format("ogg"), 1, 0)
        self.btn_m4a = self.create_btn(self.fmt_frame, "M4A", lambda: self.set_format("m4a"), 1, 1)
        self.btn_wma = self.create_btn(self.fmt_frame, "WMA", lambda: self.set_format("wma"), 1, 2)

        self.fmt_buttons = [self.btn_mp3, self.btn_wav, self.btn_flac, self.btn_ogg, self.btn_m4a, self.btn_wma]

        # 5. Quality Selection (New Feature)
        ctk.CTkLabel(self, text="Audio Quality:", font=("Roboto", 14, "bold")).grid(row=5, column=0, pady=(20, 5))

        self.qual_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.qual_frame.grid(row=6, column=0, pady=5)

        self.btn_high = self.create_btn(self.qual_frame, "High Quality (320k)", lambda: self.set_quality("320k"), 0, 0, w=140)
        self.btn_low = self.create_btn(self.qual_frame, "Low Quality (128k)", lambda: self.set_quality("128k"), 0, 1, w=140)

        # 6. Output Folder
        self.folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.folder_frame.grid(row=7, column=0, pady=(25, 0))

        self.folder_label = ctk.CTkLabel(self.folder_frame, text="Output: Source Folder (Default)", text_color="gray", font=("Roboto", 12))
        self.folder_label.pack(pady=2)

        self.change_folder_btn = ctk.CTkButton(self.folder_frame, text="Change Folder", width=120, height=24, 
                                               fg_color="#333", hover_color="#444", font=("Roboto", 11),
                                               command=self.select_output_folder)
        self.change_folder_btn.pack(pady=2)

        # 7. Convert Button
        self.convert_btn = ctk.CTkButton(self, text="Convert Now", height=50, width=240, 
                                         font=("Roboto", 18, "bold"), fg_color="#6366f1", hover_color="#4f46e5",
                                         command=self.start_thread)
        self.convert_btn.grid(row=8, column=0, pady=35)

        # 8. Status (Bigger)
        self.status = ctk.CTkLabel(self, text="Ready", text_color="gray", font=("Roboto", 16))
        self.status.grid(row=9, column=0, pady=(0, 20))

        # Initial Updates
        self.update_fmt_colors()
        self.update_qual_colors()

    def create_btn(self, parent, text, cmd, r, c, w=80):
        btn = ctk.CTkButton(parent, text=text, width=w, height=35, corner_radius=8, command=cmd)
        btn.grid(row=r, column=c, padx=5, pady=5)
        return btn

    def set_format(self, value):
        self.target_format = value
        self.update_fmt_colors()

    def set_quality(self, value):
        self.target_bitrate = value
        self.update_qual_colors()

    def update_fmt_colors(self):
        for btn in self.fmt_buttons:
            is_active = (btn.cget("text").lower() == self.target_format)
            btn.configure(fg_color="#10b981" if is_active else "#333333", 
                          hover_color="#059669" if is_active else "#444444")

    def update_qual_colors(self):
        # High button
        high_active = (self.target_bitrate == "320k")
        self.btn_high.configure(fg_color="#3b82f6" if high_active else "#333333", 
                                hover_color="#2563eb" if high_active else "#444444")
        
        # Low button
        low_active = (self.target_bitrate == "128k")
        self.btn_low.configure(fg_color="#f59e0b" if low_active else "#333333", 
                               hover_color="#d97706" if low_active else "#444444")

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            display_text = folder if len(folder) < 45 else "..." + folder[-42:]
            self.folder_label.configure(text=f"Save to: {display_text}", text_color="#10b981")

    def browse_file(self):
        path = filedialog.askopenfilename(title="Select Audio File")
        if path:
            self.input_path = path
            self.file_label.configure(text=os.path.basename(path), text_color="#6366f1") # Highlight color
            self.select_btn.configure(fg_color="#333", border_color="#10b981")
            self.status.configure(text="File Loaded", text_color="white")

    def start_thread(self):
        if not self.input_path:
            self.status.configure(text="Please select a file first", text_color="red")
            return
        
        self.status.configure(text="Converting...", text_color="#6366f1")
        self.convert_btn.configure(state="disabled")
        self.select_btn.configure(state="disabled")
        threading.Thread(target=self.convert, daemon=True).start()

    def convert(self):
        try:
            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
            target_filename = f"{base_name}.{self.target_format}"
            
            dest_folder = self.output_folder if self.output_folder else os.path.dirname(self.input_path)
            output_path = os.path.join(dest_folder, target_filename)
            
            if output_path.lower() == self.input_path.lower():
                output_path = os.path.join(dest_folder, f"{base_name}_converted.{self.target_format}")
            
            # Codec Selection
            selected_codec = self.codec_map.get(self.target_format, None)

            # --- SMART BITRATE LOGIC ---
            # If format is WAV or FLAC (Lossless), ignore bitrate to maintain perfection.
            # Otherwise (MP3, OGG, WMA, M4A), apply the user selected bitrate.
            final_bitrate = self.target_bitrate
            if self.target_format in ["wav", "flac"]:
                final_bitrate = None 
            
            audio = AudioFileClip(self.input_path)
            audio.write_audiofile(output_path, codec=selected_codec, bitrate=final_bitrate, logger=None)
            audio.close()
            
            self.after(0, lambda: self.status.configure(text="Successfully Converted! ✅", text_color="#10b981", font=("Roboto", 20, "bold")))
            self.open_folder(os.path.dirname(output_path))
            
        except Exception as e:
            print(f"Error: {e}")
            self.after(0, lambda: self.status.configure(text="Conversion Failed", text_color="red"))
        finally:
            self.after(0, lambda: self.reset_ui())

    def reset_ui(self):
        self.convert_btn.configure(state="normal")
        self.select_btn.configure(state="normal")

    def open_folder(self, path):
        if SYSTEM_OS == "Windows":
            os.startfile(path)
        elif SYSTEM_OS == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])

if __name__ == "__main__":
    app = AudioApp()
    app.mainloop()