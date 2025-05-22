# AI Background Remover Pro

AI Background Remover Pro is a modern, full-stack web application that uses advanced AI models to remove backgrounds from images with studio-quality precision. It features a beautiful, user-friendly interface, real-time feedback, and a wide range of customization options for both professionals and casual users.

---

## 🚀 Features

### ✨ Studio-Quality AI Background Removal
- Utilizes state-of-the-art AI models (U2Net, U2Net Human Segmentation, U2Netp) for highly accurate background removal.
- Supports both general and human-specific segmentation.

### 🖼️ Image Upload & Comparison
- Drag & drop or browse to upload your image.
- Instantly see a side-by-side comparison of the original and processed images.
- **Image dimension validation:** Only allows images between 500x300 and 1000x800 pixels (inclusive). Shows a clear error if the image is too small or too large.

### 🛠️ Quality & Model Settings
- **AI Model Selection:** Choose between highest quality, human segmentation, or fast processing.
- **Quality Levels:** Ultra HD, High, Good, Draft.
- **Advanced Processing:**
  - HD Edge Refinement
  - Preserve Details
  - Upscale Small Images
  - Enhance Details
  - Super Resolution

### 🎨 Custom Backgrounds
- **Transparent:** Output with no background.
- **Solid Color:** Pick any color as the new background.
- **Gradient:** Choose start and end colors for a smooth gradient background.
- **Custom Image:** Upload your own background image.

### ⚙️ Advanced Controls
- **Foreground Threshold:** Fine-tune the AI's sensitivity to the subject.
- **Background Threshold:** Adjust how much background is removed.
- **Edge Refinement Size:** Control the smoothness and precision of edges.

### 📥 Download Options
- Download your processed image in **PNG (lossless)**, **JPG (high quality)**, or **TIFF (maximum quality)** formats.

### 💡 Modern UI/UX
- Responsive, clean, and intuitive interface.
- Real-time loader/spinner in the processed image panel during processing.
- Progress bar for additional feedback.
- Works great on desktop and mobile.

---

## 🖥️ Screenshots

| Upload & Settings | Comparison & Download |
|-------------------|----------------------|
| ![Upload](https://imgur.com/your-upload.png) | ![Compare](https://imgur.com/your-compare.png) |

---

## ⚡ Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/ai-background-remover-pro.git
cd ai-background-remover-pro
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app (FastAPI)
```bash
uvicorn app:app --reload
```
The app will be available at [http://localhost:8000](http://localhost:8000).

---

## 🧩 Project Structure

```
.
├── app.py                # FastAPI backend with AI processing
├── requirements.txt      # Python dependencies
├── static/
│   ├── css/style.css     # App styles
│   └── js/main.js        # Frontend logic
├── templates/
│   └── index.html        # Main HTML template
└── uploads/              # Uploaded images (if needed)
```

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, rembg, OpenCV, Pillow
- **Frontend:** HTML5, CSS3, JavaScript (vanilla)
- **AI Models:** U2Net, U2Net Human Segmentation, U2Netp

---

## 🌟 How It Works

1. **Upload an image** via drag & drop or file picker.
2. **Image is validated** (must be between 500x300 and 1000x800 pixels).
3. **Configure your settings** (model, quality, background, advanced options).
4. **Process the image** — the app removes the background using AI and applies your chosen background.
5. **Compare** the original and processed images side by side.
6. **Download** the result in your preferred format.

---

## 📝 API Endpoints

- `GET /`  
  Returns the main web interface.

- `POST /api/process`  
  Accepts a base64 image and settings, returns a processed image (base64 PNG).

- `POST /api/download`  
  Accepts a base64 image and format, returns the image as a downloadable file (PNG, JPG, or TIFF).

---

## 🧑‍💻 Customization

- You can easily add new background types, models, or processing steps by editing `app.py` and the frontend files.
- The UI is fully responsive and can be themed via `static/css/style.css`.
- **Image validation** can be adjusted in `static/js/main.js` to allow different size ranges.

---

## 📦 Deployment

- **Local:** See "Getting Started" above.
- **Cloud:** Deploy on Render, Railway, Fly.io, or any Python-friendly PaaS.  
  *(Vercel is supported for FastAPI apps with the right configuration.)*

---

## ❓ FAQ

**Q: What image formats are supported?**  
A: Upload: Any common image format. Download: PNG, JPG, TIFF.

**Q: Is GPU required?**  
A: No, but a CPU with AVX support is recommended for faster processing.

**Q: Can I change the allowed image size range?**  
A: Yes! Edit the validation logic in `static/js/main.js`.

---

## 🤝 Contributing

Pull requests and issues are welcome! Please open an issue to discuss your idea or bug before submitting a PR.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [rembg](https://github.com/danielgatis/rembg)
- [U2Net](https://github.com/xuebinqin/U-2-Net)
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenCV](https://opencv.org/)

---

> **AI Background Remover Pro** — Remove backgrounds like a pro, with the power of AI!
