import os
import time
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
import streamlit as st
from rembg import remove, new_session
import cv2
from io import BytesIO
import tempfile
from streamlit_image_comparison import image_comparison
import base64

# Configure for ultra-high-quality processing
Image.MAX_IMAGE_PIXELS = None  # Remove image size limit

# --- 🎨 STREAMLIT UI SETUP ---
st.set_page_config(
    page_title="✨ AI Background Remover Pro",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 20px;
        padding: 10px 25px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .upload-section {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .processing-status {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .feature-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    .quality-badge {
        background-color: #2196F3;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- 🏗️ SESSION STATE INIT ---
if 'original_image' not in st.session_state:
    st.session_state.original_image = None
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'bg_image' not in st.session_state:
    st.session_state.bg_image = None
if 'processing_done' not in st.session_state:
    st.session_state.processing_done = False
if 'session' not in st.session_state:
    st.session_state.session = new_session("u2net_human_seg")
if 'processing_progress' not in st.session_state:
    st.session_state.processing_progress = 0

# --- 🎚️ SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h2>⚙️ Settings</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Model Selection with improved UI
    model_options = {
        "Highest Quality (u2net)": "u2net",
        "Human Segmentation (u2net_human_seg)": "u2net_human_seg",
        "Fast Processing (u2netp)": "u2netp"
    }
    selected_model = st.selectbox("AI Model", list(model_options.keys()), index=0)

    # Quality Settings with visual feedback
    with st.expander("🔍 Quality Settings", expanded=True):
        st.markdown("<div class='quality-badge'>Ultra HD Processing</div>", unsafe_allow_html=True)
        
        processing_quality = st.select_slider(
            "Processing Quality",
            options=["Draft", "Good", "High", "Ultra HD"],
            value="Ultra HD",
            help="Higher quality takes longer but produces better results"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            edge_refinement = st.checkbox("HD Edge Refinement", True)
            preserve_details = st.checkbox("Preserve Details", True)
        with col2:
            upscale_small = st.checkbox("Upscale Small", False)
            enhance_details = st.checkbox("Enhance Details", True)
        
        super_resolution = st.checkbox("Super Resolution", False, help="Enables AI upscaling for better quality")

    # Background Options with preview
    with st.expander("🌄 Background Options"):
        bg_options = ["Transparent", "White", "Black", "Custom Color", "Upload Image", "Gradient"]
        bg_choice = st.selectbox("Background Type", bg_options, index=0)
        
        if bg_choice == "Custom Color":
            bg_color = st.color_picker("Choose Color", "#FFFFFF")
        elif bg_choice == "Upload Image":
            bg_upload = st.file_uploader("Upload Background", type=["jpg", "jpeg", "png"])
            if bg_upload:
                st.session_state.bg_image = Image.open(bg_upload)
                st.image(st.session_state.bg_image, caption="Background Preview", use_column_width=True)
        elif bg_choice == "Gradient":
            col1, col2 = st.columns(2)
            with col1:
                gradient_start = st.color_picker("Start Color", "#4CAF50")
            with col2:
                gradient_end = st.color_picker("End Color", "#2196F3")
        else:
            bg_color = {
                "Transparent": None,
                "White": "#FFFFFF",
                "Black": "#000000"
            }[bg_choice]

    # Advanced Settings with tooltips
    with st.expander("⚡ Advanced Settings"):
        st.markdown("### Fine-tuning Options")
        matting_foreground = st.slider("Foreground Threshold", 100, 300, 240,
                                     help="Adjust how much of the foreground to keep")
        matting_background = st.slider("Background Threshold", 0, 100, 10,
                                     help="Adjust how much of the background to remove")
        matting_erode = st.slider("Edge Refinement", 0, 50, 15,
                                help="Fine-tune edge detection")
        
        st.markdown("### Enhancement Options")
        feather_edges = st.checkbox("Feather Edges", True)
        feather_amount = st.slider("Feather Amount", 0, 20, 7) if feather_edges else 0
        contrast_boost = st.slider("Contrast", 0.0, 2.0, 1.0)
        sharpness_boost = st.slider("Sharpness", 0.0, 2.0, 0.5)

    # Batch Processing Option
    st.markdown("---")
    batch_processing = st.checkbox("Enable Batch Processing", False)
    if batch_processing:
        st.file_uploader("Upload Multiple Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# --- 🖼️ MAIN APP UI ---
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1>✨ AI Background Remover Pro</h1>
    <p style='color: #666;'>Remove backgrounds with studio-quality precision using advanced AI</p>
</div>
""", unsafe_allow_html=True)

# Upload Section with improved UI
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "📤 Upload Image (PNG/JPG)", 
    type=["jpg", "jpeg", "png"],
    key="main_uploader",
    help="Upload a high-resolution image for best results"
)
st.markdown('</div>', unsafe_allow_html=True)

# --- 🖥️ IMAGE DISPLAY (BEFORE/AFTER) ---
if uploaded_file:
    col1, col2 = st.columns(2)
    
    # Original Image (Left Panel)
    with col1:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("Original Image")
        st.session_state.original_image = Image.open(uploaded_file)
        st.image(
            st.session_state.original_image,
            caption=f"Original ({st.session_state.original_image.size[0]}x{st.session_state.original_image.size[1]})",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Processed Image (Right Panel)
    with col2:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("Processed Image")
        if st.session_state.processing_done and st.session_state.processed_image:
            st.image(
                st.session_state.processed_image,
                caption=f"Processed ({st.session_state.processed_image.size[0]}x{st.session_state.processed_image.size[1]})",
                use_container_width=True
            )

            # Side-by-Side Comparison with slider
            st.markdown("**🔄 Before/After Comparison**")
            image_comparison(
                img1=st.session_state.original_image,
                img2=st.session_state.processed_image,
                label1="Original",
                label2="Processed",
                width=700
            )

            # Download Options with improved UI
            st.markdown("**💾 Download Options**")
            col1, col2 = st.columns(2)
            with col1:
                export_format = st.radio("Format", ["PNG (Lossless)", "JPG (High Quality)", "TIFF (Maximum Quality)"], index=0)
            with col2:
                if st.button("⬇️ Download", use_container_width=True):
                    download_processed_image(export_format)
        else:
            st.info("Processed image will appear here")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 🛠️ ULTRA HD PROCESSING FUNCTIONS ---
def process_ultra_hd(image, model_name="u2net"):
    """Process image with ultra HD quality settings"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Convert to RGB if needed
        img = image.convert('RGB') if image.mode != 'RGB' else image
        
        # Update progress
        progress_bar.progress(10)
        status_text.text("🔍 Analyzing image...")
        
        if processing_quality == "Ultra HD":
            # Stage 1: Initial background removal
            progress_bar.progress(20)
            status_text.text("🎯 Removing background...")
            result = remove(
                img,
                session=new_session(model_name),
                alpha_matting=True,
                alpha_matting_foreground_threshold=matting_foreground,
                alpha_matting_background_threshold=matting_background,
                alpha_matting_erode_size=matting_erode,
                post_process_mask=preserve_details
            )
            
            # Stage 2: Create high-precision mask
            progress_bar.progress(40)
            status_text.text("📐 Creating precision mask...")
            mask = remove(img, session=new_session(model_name), only_mask=True)
            
            # Stage 3: Edge refinement
            if edge_refinement:
                progress_bar.progress(60)
                status_text.text("✨ Refining edges...")
                result = ultra_hd_edge_refinement(result, mask)
            
            # Stage 4: Detail enhancement
            if enhance_details:
                progress_bar.progress(80)
                status_text.text("🎨 Enhancing details...")
                result = ultra_hd_detail_enhancement(result)
            
            # Stage 5: Super Resolution
            if super_resolution and max(img.size) < 4000:
                progress_bar.progress(90)
                status_text.text("🚀 Applying super resolution...")
                result = apply_super_resolution(result)
            
            # Stage 6: Upscale if needed
            if upscale_small and max(img.size) < 2000:
                result = result.resize((img.size[0]*2, img.size[1]*2), Image.LANCZOS)
        else:
            # Standard quality processing
            result = remove(img, session=new_session(model_name))

        # Final quality adjustments
        progress_bar.progress(95)
        status_text.text("✨ Applying final touches...")
        result = apply_ultra_hd_finishing(result)
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        time.sleep(1)  # Show completion briefly
        progress_bar.empty()
        status_text.empty()
        
        return result
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Error during processing: {str(e)}")
        return None

def ultra_hd_edge_refinement(image, mask):
    """AI-enhanced ultra HD edge refinement with proper type handling"""
    img_array = np.array(image)
    mask_array = np.array(mask)
    
    if len(mask_array.shape) == 3:
        mask_array = cv2.cvtColor(mask_array, cv2.COLOR_RGB2GRAY)
    
    # Convert to float32 for high precision operations
    mask_array = mask_array.astype(np.float32) / 255.0
    
    # Ultra HD multi-stage refinement
    for i in range(3 if processing_quality == "Ultra HD" else 1):
        # Bilateral filtering for edge-aware smoothing
        mask_array = cv2.bilateralFilter(mask_array, 9, 75, 75)
        
        # Morphological operations for clean edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        mask_array = cv2.morphologyEx(mask_array, cv2.MORPH_CLOSE, kernel)
        mask_array = cv2.morphologyEx(mask_array, cv2.MORPH_OPEN, kernel)
        
        # Edge sharpening with proper type conversion
        if i == 1:
            laplacian = cv2.Laplacian(mask_array, cv2.CV_32F)
            # Ensure both arrays have same type before operation
            mask_array = cv2.addWeighted(
                mask_array.astype(np.float32), 1.5, 
                laplacian.astype(np.float32), -0.5, 
                0, dtype=cv2.CV_32F
            )
    
    # Advanced edge feathering
    if feather_edges:
        mask_array = cv2.GaussianBlur(mask_array, (feather_amount*2+1, feather_amount*2+1), 0)
        mask_array = cv2.normalize(mask_array, None, 0, 1, cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    
    # Convert back to 8-bit
    mask_array = (mask_array * 255).clip(0, 255).astype(np.uint8)
    
    # Handle RGBA vs RGB images
    if image.mode == 'RGBA':
        rgb = img_array[:, :, :3]
        alpha = mask_array
        result = np.dstack((rgb, alpha))
    else:
        result = np.dstack((img_array, mask_array))
    
    return Image.fromarray(result)

def ultra_hd_detail_enhancement(image):
    """Ultra HD detail enhancement with proper type handling"""
    img_array = np.array(image)
    
    # Convert to LAB color space for better detail preservation
    if image.mode == 'RGBA':
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3]
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    else:
        lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    
    # Split channels and ensure proper types
    l, a, b = cv2.split(lab)
    l = l.astype(np.float32)
    
    # Apply CLAHE to L channel for local contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l.astype(np.uint8)).astype(np.float32)
    
    # Merge channels and convert back
    lab = cv2.merge((l.astype(np.uint8), a, b))
    rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    # Convert back to RGBA if needed
    if image.mode == 'RGBA':
        result = np.dstack((rgb, alpha))
    else:
        result = rgb
    
    # Apply sharpening if enabled
    if sharpness_boost > 0:
        enhanced_img = Image.fromarray(result)
        enhancer = ImageEnhance.Sharpness(enhanced_img)
        result = np.array(enhancer.enhance(1.0 + sharpness_boost))
    
    return Image.fromarray(result)

def apply_super_resolution(image):
    """Apply super resolution to enhance details"""
    # Note: In production, you would integrate with a real SR model like ESRGAN
    # This is a placeholder implementation using high-quality upscaling
    if processing_quality == "Ultra HD":
        return image.resize((image.size[0]*2, image.size[1]*2), Image.LANCZOS)
    return image

def apply_ultra_hd_finishing(image):
    """Apply final ultra HD quality adjustments"""
    # Contrast boost
    if contrast_boost != 1.0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast_boost)
    
    # Sharpness boost
    if sharpness_boost > 0:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.0 + sharpness_boost)
    
    return image

def apply_custom_background(foreground, bg_image=None, bg_color=None):
    """Apply custom background with ultra HD blending"""
    if bg_color:
        bg = Image.new("RGB", foreground.size, bg_color)
        if foreground.mode == 'RGBA':
            alpha = foreground.split()[3]
            # Ultra HD blending with improved alpha compositing
            bg.paste(foreground, mask=alpha)
        else:
            bg.paste(foreground)
        return bg
    elif bg_image:
        bg = bg_image.resize(foreground.size, Image.LANCZOS)
        if foreground.mode == 'RGBA':
            alpha = foreground.split()[3]
            bg.paste(foreground, mask=alpha)
        else:
            bg.paste(foreground)
        return bg
    return foreground  # Transparent

def apply_gradient_background(image, start_color, end_color):
    """Apply a gradient background to the image"""
    width, height = image.size
    gradient_image = Image.new('RGB', (width, height), start_color)
    gradient_image.putpixel((0, 0), start_color)
    gradient_image.putpixel((width-1, 0), end_color)
    gradient_image.putpixel((0, height-1), start_color)
    gradient_image.putpixel((width-1, height-1), end_color)
    
    # Create a mask based on the image's alpha channel
    mask = Image.new('L', image.size, 0)
    mask.putdata(image.convert('L').getdata())
    
    # Apply the gradient to the image
    result = Image.composite(gradient_image, image, mask)
    
    return result

def download_processed_image(format_type):
    """Generate ultra HD download link with maximum quality options"""
    buffered = BytesIO()
    
    if format_type == "PNG (Lossless)":
        st.session_state.processed_image.save(buffered, format="PNG", compress_level=0)
        mime_type = "image/png"
        file_ext = "png"
    elif format_type == "JPG (High Quality)":
        st.session_state.processed_image.convert("RGB").save(buffered, format="JPEG", quality=100, subsampling=0)
        mime_type = "image/jpeg"
        file_ext = "jpg"
    else:  # TIFF
        st.session_state.processed_image.save(buffered, format="TIFF", compression="tiff_deflate")
        mime_type = "image/tiff"
        file_ext = "tif"
    
    st.download_button(
        label="⬇️ Download Ultra HD Image",
        data=buffered.getvalue(),
        file_name=f"ultra_hd_processed.{file_ext}",
        mime=mime_type
    )

# --- 🎛️ PROCESS BUTTON ---
if uploaded_file:
    st.markdown('<div class="processing-status">', unsafe_allow_html=True)
    if st.button("✨ Process Image", type="primary", use_container_width=True):
        with st.spinner("Processing image..."):
            try:
                st.session_state.processed_image = process_ultra_hd(
                    st.session_state.original_image,
                    model_options[selected_model]
                )
                
                # Apply background
                if bg_choice == "Upload Image" and st.session_state.bg_image:
                    st.session_state.processed_image = apply_custom_background(
                        st.session_state.processed_image,
                        st.session_state.bg_image
                    )
                elif bg_choice == "Gradient":
                    st.session_state.processed_image = apply_gradient_background(
                        st.session_state.processed_image,
                        gradient_start,
                        gradient_end
                    )
                elif bg_choice != "Transparent":
                    st.session_state.processed_image = apply_custom_background(
                        st.session_state.processed_image,
                        bg_color=bg_color
                    )
                
                st.session_state.processing_done = True
                st.rerun()
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
                st.stop()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 📜 FOOTER ---
st.markdown("""
<style>
.footer {
    font-size: 0.8rem;
    color: #666;
    text-align: center;
    margin-top: 2rem;
    padding: 1rem;
    background-color: white;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.ultra-hd-badge {
    background-color: #2196F3;
    color: white;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.7rem;
}
</style>
<div class="footer">
    <p><span class="ultra-hd-badge">ULTRA HD</span> Background Remover Pro • Powered by Advanced AI</p>
    <p style='font-size: 0.7rem; color: #999;'>For best results, use high-resolution images (3000px+) with clear subject boundaries</p>
</div>
""", unsafe_allow_html=True)