import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import ImageTk, Image
from mutagen.mp4 import MP4, MP4Cover
import subprocess
import os
import threading

class MP4ToM4AConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("MP4 to M4A Converter")
        self.file_status_list = []
        self.all_converted = False

        # Create GUI elements
        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid to expand with window size
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # MP4 File Selection
        select_files_button = ttk.Button(main_frame, text="Select MP4 Files", command=self.select_mp4_files)
        select_files_button.grid(row=0, column=1, sticky="e")

        # File List
        columns = ("Filename", "Status", "Progress")
        self.file_listbox = ttk.Treeview(main_frame, columns=columns, show="headings")
        for col in columns:
            self.file_listbox.heading(col, text=col)
            self.file_listbox.column(col, stretch=tk.YES)
        self.file_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Add vertical scrollbar to the file list
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))

        # Album Art Selection
        album_art_label = ttk.Label(main_frame, text="Select Album Art:")
        album_art_label.grid(row=2, column=0, sticky="w")
        self.album_art_path = tk.StringVar()
        album_art_entry = ttk.Entry(main_frame, textvariable=self.album_art_path, width=50)
        album_art_entry.grid(row=3, column=0, sticky="w")
        album_art_button = ttk.Button(main_frame, text="Browse", command=self.select_album_art)
        album_art_button.grid(row=3, column=1, sticky="e")

        # Image Preview
        self.album_art_preview = ttk.Label(main_frame)
        self.album_art_preview.grid(row=4, column=0, columnspan=2, pady=10)

        # Buttons
        convert_button = ttk.Button(main_frame, text="Convert to M4A", command=self.convert_files)
        convert_button.grid(row=5, column=0, pady=5, sticky="ew")

        open_output_button = ttk.Button(main_frame, text="Open Output Folder", command=self.open_output_folder)
        open_output_button.grid(row=6, column=0, pady=5, sticky="ew")

        clear_list_button = ttk.Button(main_frame, text="Clear File List", command=self.clear_file_list)
        clear_list_button.grid(row=7, column=0, pady=5, sticky="ew")

    def select_mp4_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("MP4 Files", "*.mp4")])
        if file_paths:
            for file_path in file_paths:
                idx = len(self.file_status_list)
                item_id = self.file_listbox.insert("", "end", values=(file_path, "Pending", "0%"))
                self.file_status_list.append({"path": file_path, "progress_var": tk.IntVar(), "item_id": item_id})

    def select_album_art(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        self.album_art_path.set(file_path)
        self.display_image_preview(file_path)

    def display_image_preview(self, image_path):
        img = Image.open(image_path)
        img = img.resize((100, 100), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)
        self.album_art_preview.config(image=img)
        self.album_art_preview.image = img

    def convert_files(self):
        album_art = self.album_art_path.get()
        if not album_art:
            messagebox.showwarning("Input Missing", "Please select an album art image.")
            return

        for idx, file_info in enumerate(self.file_status_list):
            input_mp4 = file_info["path"]
            output_m4a = os.path.splitext(input_mp4)[0] + ".m4a"
            file_info["progress_var"].set(0)
            treeview_item_id = file_info["item_id"]
            self.file_listbox.item(treeview_item_id, values=(input_mp4, "Converting...", "0%"))
            threading.Thread(target=self.mp4_to_m4a, args=(input_mp4, output_m4a, album_art, file_info["progress_var"], treeview_item_id)).start()

    def mp4_to_m4a(self, input_mp4, output_m4a, album_art_path, progress_var, treeview_item_id):
        try:
            # Convert MP4 to M4A using ffmpeg
            command = f'ffmpeg -i "{input_mp4}" -vn -acodec copy "{output_m4a}"'
            subprocess.run(command, shell=True, check=True)

            # Add album art to M4A
            audio = MP4(output_m4a)
            if album_art_path:
                with open(album_art_path, 'rb') as img_file:
                    audio['covr'] = [MP4Cover(img_file.read(), imageformat=MP4Cover.FORMAT_JPEG if album_art_path.endswith('.jpg') else MP4Cover.FORMAT_PNG)]
                audio.save()
            progress_var.set(100)
            self.file_listbox.item(treeview_item_id, values=(input_mp4, "Completed", "100%"))
            self.check_all_converted()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Conversion Error", f"An error occurred during conversion: {e}")
            progress_var.set(0)
            self.file_listbox.item(treeview_item_id, values=(input_mp4, "Failed", "0%"))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            progress_var.set(0)
            self.file_listbox.item(treeview_item_id, values=(input_mp4, "Failed", "0%"))

    def check_all_converted(self):
        all_converted = True
        for file_info in self.file_status_list:
            if file_info["progress_var"].get() != 100:
                all_converted = False
                break
        if all_converted and not self.all_converted:
            messagebox.showinfo("Conversion Complete", "All files converted successfully.")
            self.all_converted = True

    def open_output_folder(self):
        if self.file_status_list:
            output_folder = os.path.dirname(self.file_status_list[0]["path"])
            if os.name == 'nt':  # For Windows
                os.startfile(output_folder)
            elif os.name == 'posix':  # For MacOS and Linux
                subprocess.Popen(['open', output_folder] if sys.platform == 'darwin' else ['xdg-open', output_folder])
        else:
            messagebox.showwarning("No Files", "No files have been selected.")

    def clear_file_list(self):
        self.file_listbox.delete(*self.file_listbox.get_children())
        self.file_status_list.clear()
        self.all_converted = False
        self.album_art_path.set("")
        self.album_art_preview.config(image='')

if __name__ == "__main__":
    root = tk.Tk()
    app = MP4ToM4AConverter(root)
    root.mainloop()
