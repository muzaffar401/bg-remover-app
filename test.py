import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import numpy as np
from rembg import remove, new_session
import threading
import time

class BGRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fast HD Background Remover")
        self.root.geometry("1000x700")
        
        # Initialize AI model session (lighter weight model)
        self.session = new_session("u2net")
        
        # Variables
        self.input_path = ""
        self.processing = False
        self.effect_var = tk.StringVar(value="normal")
        
        # UI Setup
        self.setup_ui()
        
    def setup_ui(self):
        # Main frames
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Image display
        self.setup_image_display(main_frame)
        
        # Controls
        self.setup_controls(main_frame)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to load an image")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X)
    
    def setup_image_display(self, parent):
        img_frame = ttk.Frame(parent)
        img_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Original image
        orig_frame = ttk.Frame(img_frame)
        orig_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(orig_frame, text="Original Image").pack()
        self.orig_canvas = tk.Canvas(orig_frame, bg='#f0f0f0', bd=2, relief=tk.SUNKEN)
        self.orig_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Processed image
        proc_frame = ttk.Frame(img_frame)
        proc_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(proc_frame, text="Processed Image").pack()
        self.proc_canvas = tk.Canvas(proc_frame, bg='#f0f0f0', bd=2, relief=tk.SUNKEN)
        self.proc_canvas.pack(fill=tk.BOTH, expand=True)
    
    def setup_controls(self, parent):
        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(fill=tk.X, pady=10)
        
        # Buttons
        ttk.Button(ctrl_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        
        self.process_btn = ttk.Button(ctrl_frame, text="Remove Background", 
                                    command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        self.process_btn.state(['disabled'])
        
        # Effect selection
        effect_frame = ttk.Frame(ctrl_frame)
        effect_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(effect_frame, text="Effect:").pack(side=tk.LEFT)
        ttk.Radiobutton(effect_frame, text="Normal", variable=self.effect_var, 
                       value="normal").pack(side=tk.LEFT)
        ttk.Radiobutton(effect_frame, text="UV", variable=self.effect_var, 
                       value="uv").pack(side=tk.LEFT)
        
        self.save_btn = ttk.Button(ctrl_frame, text="Save Result", 
                                 command=self.save_image)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        self.save_btn.state(['disabled'])
        
        # Progress
        self.progress = ttk.Progressbar(ctrl_frame, mode='indeterminate', length=200)
    
    def load_image(self):
        filepath = filedialog.askopenfilename(filetypes=[
            ('Images', '*.jpg *.jpeg *.png *.bmp'),
            ('All files', '*.*')
        ])
        
        if filepath:
            try:
                self.input_path = filepath
                self.original_image = Image.open(filepath)
                self.display_image(self.original_image, self.orig_canvas)
                self.process_btn.state(['!disabled'])
                self.status_var.set(f"Loaded: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image:\n{str(e)}")
    
    def start_processing(self):
        if not self.input_path:
            return
            
        self.processing = True
        self.process_btn.state(['disabled'])
        self.save_btn.state(['disabled'])
        self.progress.pack(side=tk.LEFT, padx=5)
        self.progress.start()
        self.status_var.set("Processing...")
        
        # Start processing thread
        threading.Thread(target=self.process_image, daemon=True).start()
        
        # Start monitoring progress
        self.monitor_processing()
    
    def monitor_processing(self):
        if self.processing:
            self.root.after(500, self.monitor_processing)
        else:
            self.progress.stop()
            self.progress.pack_forget()
    
    def process_image(self):
        try:
            start_time = time.time()
            
            # Convert to RGB if needed
            img = self.original_image.convert('RGB') if self.original_image.mode != 'RGB' else self.original_image
            
            # Resize for faster processing (maintain aspect ratio)
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Process with rembg (using preloaded session)
            result = remove(img, session=self.session)
            
            # Apply effect if needed
            if self.effect_var.get() == "uv":
                result = self.apply_uv_effect(result)
            
            # Store full resolution result
            if img.size != self.original_image.size:
                result = result.resize(self.original_image.size, Image.LANCZOS)
            
            self.processed_image = result
            
            # Update UI
            self.root.after(0, self.processing_complete)
            
            proc_time = time.time() - start_time
            print(f"Processing completed in {proc_time:.2f} seconds")
            
        except Exception as e:
            self.root.after(0, self.processing_failed, str(e))
        finally:
            self.processing = False
    
    def apply_uv_effect(self, img):
        """Optimized UV effect application"""
        # Create glow layer
        glow = img.filter(ImageFilter.GaussianBlur(3))
        glow = ImageEnhance.Brightness(glow).enhance(1.3)
        
        # Combine with original
        result = Image.blend(img, glow, 0.2)
        
        # Enhance colors
        result = ImageEnhance.Color(result).enhance(1.8)
        return result
    
    def processing_complete(self):
        self.display_image(self.processed_image, self.proc_canvas)
        self.save_btn.state(['!disabled'])
        self.status_var.set("Processing complete - ready to save")
    
    def processing_failed(self, error):
        messagebox.showerror("Processing Error", f"Failed to process image:\n{error}")
        self.status_var.set("Processing failed")
        self.process_btn.state(['!disabled'])
    
    def save_image(self):
        if not self.processed_image:
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ('PNG', '*.png'),
                ('JPEG', '*.jpg *.jpeg'),
                ('All files', '*.*')
            ],
            initialfile=f"processed_{os.path.basename(self.input_path)}"
        )
        
        if filename:
            try:
                if filename.lower().endswith(('.jpg', '.jpeg')):
                    self.processed_image.convert('RGB').save(filename, quality=95)
                else:
                    self.processed_image.save(filename)
                
                self.status_var.set(f"Saved: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save image:\n{str(e)}")
    
    def display_image(self, img, canvas):
        canvas.delete("all")
        if not img:
            return
            
        # Calculate display size
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        img_ratio = img.width / img.height
        canvas_ratio = canvas_width / canvas_height
        
        if img_ratio > canvas_ratio:
            display_width = canvas_width
            display_height = int(canvas_width / img_ratio)
        else:
            display_height = canvas_height
            display_width = int(canvas_height * img_ratio)
        
        # Resize and display
        display_img = img.resize((display_width, display_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(display_img)
        
        canvas.image = photo
        canvas.create_image(
            (canvas_width - display_width) // 2,
            (canvas_height - display_height) // 2,
            anchor=tk.NW, image=photo
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = BGRemoverApp(root)
    root.mainloop()