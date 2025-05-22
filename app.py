from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import os
import time
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
from rembg import remove, new_session
import cv2
from io import BytesIO
import base64
import tempfile
from pydantic import BaseModel
from typing import Optional, Dict, Any
import shutil
import json

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize session
session = new_session("u2net_human_seg")

# Pydantic models for request validation
class ProcessRequest(BaseModel):
    image: str
    settings: Optional[Dict[str, Any]] = {}

class DownloadRequest(BaseModel):
    image: str
    format: str = "PNG"

# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def process_image(image, settings):
    """Process image with specified settings"""
    try:
        # Convert to RGB if needed
        img = image.convert('RGB') if image.mode != 'RGB' else image
        
        if settings.get('quality') == "Ultra HD":
            # Stage 1: Initial background removal
            result = remove(
                img,
                session=session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=settings.get('matting_foreground', 240),
                alpha_matting_background_threshold=settings.get('matting_background', 10),
                alpha_matting_erode_size=settings.get('matting_erode', 15),
                post_process_mask=settings.get('preserve_details', True)
            )
            
            # Stage 2: Create high-precision mask
            mask = remove(img, session=session, only_mask=True)
            
            # Stage 3: Edge refinement
            if settings.get('edge_refinement', True):
                result = edge_refinement(result, mask)
            
            # Stage 4: Detail enhancement
            if settings.get('enhance_details', True):
                result = detail_enhancement(result)
            
            # Stage 5: Super Resolution
            if settings.get('super_resolution', False) and max(img.size) < 4000:
                result = apply_super_resolution(result)
            
            # Stage 6: Upscale if needed
            if settings.get('upscale_small', False) and max(img.size) < 2000:
                result = result.resize((img.size[0]*2, img.size[1]*2), Image.LANCZOS)
        else:
            # Standard quality processing
            result = remove(img, session=session)

        # Apply background if specified
        if settings.get('background_type') != "Transparent":
            result = apply_background(result, settings)

        return result
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")

def edge_refinement(image, mask):
    """Refine edges of the processed image"""
    img_array = np.array(image)
    mask_array = np.array(mask)
    
    if len(mask_array.shape) == 3:
        mask_array = cv2.cvtColor(mask_array, cv2.COLOR_RGB2GRAY)
    
    mask_array = mask_array.astype(np.float32) / 255.0
    
    # Edge refinement
    mask_array = cv2.bilateralFilter(mask_array, 9, 75, 75)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    mask_array = cv2.morphologyEx(mask_array, cv2.MORPH_CLOSE, kernel)
    mask_array = cv2.morphologyEx(mask_array, cv2.MORPH_OPEN, kernel)
    
    mask_array = (mask_array * 255).clip(0, 255).astype(np.uint8)
    
    if image.mode == 'RGBA':
        rgb = img_array[:, :, :3]
        alpha = mask_array
        result = np.dstack((rgb, alpha))
    else:
        result = np.dstack((img_array, mask_array))
    
    return Image.fromarray(result)

def detail_enhancement(image):
    """Enhance details in the processed image"""
    img_array = np.array(image)
    
    if image.mode == 'RGBA':
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3]
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    else:
        lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    
    l, a, b = cv2.split(lab)
    l = l.astype(np.float32)
    
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l.astype(np.uint8)).astype(np.float32)
    
    lab = cv2.merge((l.astype(np.uint8), a, b))
    rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    if image.mode == 'RGBA':
        result = np.dstack((rgb, alpha))
    else:
        result = rgb
    
    return Image.fromarray(result)

def apply_super_resolution(image):
    """Apply super resolution to enhance details"""
    return image.resize((image.size[0]*2, image.size[1]*2), Image.LANCZOS)

def apply_background(image, settings):
    """Apply background to the processed image"""
    bg_type = settings.get('background_type')
    
    if bg_type == "Color":
        bg_color = settings.get('bg_color', "#FFFFFF")
        bg = Image.new("RGB", image.size, bg_color)
        if image.mode == 'RGBA':
            alpha = image.split()[3]
            bg.paste(image, mask=alpha)
        else:
            bg.paste(image)
        return bg
    
    elif bg_type == "Gradient":
        start_color = settings.get('gradient_start', "#4CAF50")
        end_color = settings.get('gradient_end', "#2196F3")
        return apply_gradient_background(image, start_color, end_color)
    
    elif bg_type == "Image":
        try:
            bg_image_data = settings.get('bg_image')
            if not bg_image_data or not bg_image_data.startswith('data:image/'):
                raise ValueError("Invalid background image data")
                
            # Decode base64 background image
            bg_image_bytes = base64.b64decode(bg_image_data.split(',')[1])
            bg_image = Image.open(BytesIO(bg_image_bytes))
            
            # Resize background image to match the main image size
            bg_image = bg_image.resize(image.size, Image.LANCZOS)
            
            # Apply the background
            if image.mode == 'RGBA':
                alpha = image.split()[3]
                bg_image.paste(image, mask=alpha)
            else:
                bg_image.paste(image)
            return bg_image
            
        except Exception as e:
            raise Exception(f"Error applying background image: {str(e)}")
    
    return image

def apply_gradient_background(image, start_color, end_color):
    """Apply gradient background to the image"""
    width, height = image.size
    gradient_image = Image.new('RGB', (width, height), start_color)
    gradient_image.putpixel((0, 0), start_color)
    gradient_image.putpixel((width-1, 0), end_color)
    gradient_image.putpixel((0, height-1), start_color)
    gradient_image.putpixel((width-1, height-1), end_color)
    
    mask = Image.new('L', image.size, 0)
    mask.putdata(image.convert('L').getdata())
    
    result = Image.composite(gradient_image, image, mask)
    return result

@app.post("/api/process")
async def process(request: ProcessRequest):
    try:
        image_data = request.image
        settings = request.settings or {}
        
        # Validate image data format
        if not image_data.startswith('data:image/'):
            raise HTTPException(
                status_code=400,
                detail='Invalid image data format'
            )

        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(BytesIO(image_bytes))
            
            if image is None:
                raise HTTPException(
                    status_code=400,
                    detail='Failed to load image'
                )

            # Process image
            result = process_image(image, settings)
            
            if result is None:
                raise HTTPException(
                    status_code=500,
                    detail='Failed to process image'
                )

            # Convert result to base64
            buffered = BytesIO()
            result.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return JSONResponse({
                'success': True,
                'image': f'data:image/png;base64,{img_str}'
            })
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f'Error processing image: {str(e)}'
            )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Server error: {str(e)}'
        )

@app.post("/api/download")
async def download(request: DownloadRequest):
    try:
        # Get image and format from request
        image_data = request.image
        format_type = request.format
        
        # Validate image data format
        if not image_data.startswith('data:image/'):
            raise HTTPException(
                status_code=400,
                detail='Invalid image data format'
            )
        
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(BytesIO(image_bytes))
            
            if image is None:
                raise HTTPException(
                    status_code=400,
                    detail='Failed to load image'
                )
            
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, f"processed_image.{format_type.lower()}")
            
            try:
                # Save image in specified format
                if format_type == "PNG":
                    image.save(temp_file_path, format="PNG", compress_level=0)
                    mime_type = "image/png"
                elif format_type == "JPG":
                    image.convert("RGB").save(temp_file_path, format="JPEG", quality=100, subsampling=0)
                    mime_type = "image/jpeg"
                else:  # TIFF
                    image.save(temp_file_path, format="TIFF", compression="tiff_deflate")
                    mime_type = "image/tiff"
                
                # Clean up temporary directory after response is sent
                def cleanup():
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                
                return FileResponse(
                    temp_file_path,
                    media_type=mime_type,
                    filename=f"processed_image.{format_type.lower()}",
                    background=cleanup
                )
            
            except Exception as e:
                # Clean up on error
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                raise HTTPException(
                    status_code=500,
                    detail=f'Error saving image: {str(e)}'
                )
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f'Error processing image: {str(e)}'
            )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Server error: {str(e)}'
        )

# For Vercel deployment
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"} 