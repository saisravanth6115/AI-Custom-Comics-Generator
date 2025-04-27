import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io
import base64
import requests
import json

# Load environment variables
load_dotenv()

PIXELBIN_API_TOKEN = "14fca6a3-9cae-4ec6-bcdd-d9aabe6f8ddd"
PIXELBIN_ACCESS_KEY = "78102380-baf6-4b3f-9d04-32b374a3b09f"
PIXELBIN_API_ENDPOINT = "https://api.pixelbin.io/service/platform/v1/assets/upload"

# Get API key from environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Flask App Setup ---
app = Flask(__name__)

# Configuration (Keep these)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['SECRET_KEY'] = os.urandom(24)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Helper Functions (Keep these) ---

def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def enhance_image_pil(image_path):
    """
    Enhances an image using PIL based on your provided logic.
    Saves the enhanced image and returns its path.
    """
    try:
        img_pil = Image.open(image_path).convert('RGB')
        enhancer = ImageEnhance.Color(img_pil); img_pil = enhancer.enhance(1.4)
        enhancer = ImageEnhance.Sharpness(img_pil); img_pil = enhancer.enhance(1.8)
        enhancer = ImageEnhance.Contrast(img_pil); img_pil = enhancer.enhance(1.15)
        enhancer = ImageEnhance.Brightness(img_pil); img_pil = enhancer.enhance(1.05)

        base, ext = os.path.splitext(os.path.basename(image_path))
        enhanced_filename = f"enhanced_{base}{ext}"
        enhanced_path = os.path.join(app.config['UPLOAD_FOLDER'], enhanced_filename)
        img_pil.save(enhanced_path, quality=90)
        return enhanced_path
    except Exception as e:
        print(f"!!! Enhancement Error ({image_path}): {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# --- Flask Routes ---

@app.route('/')
def home():
    """Serves the main HTML page WITHOUT injecting the API Key."""
    # Render the single HTML file from the 'templates' folder
    return render_template('index.html') # No key passed here

@app.route('/upload', methods=['POST'])
def upload_and_enhance_file():
    """Handles file upload, validation, enhancement, and returns results."""
    # --- This route remains the same as before ---
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected for upload.'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(original_filepath)
            enhanced_filepath = enhance_image_pil(original_filepath)
            if enhanced_filepath:
                original_url = f'/static/uploads/{filename}'
                enhanced_url = f'/static/uploads/{os.path.basename(enhanced_filepath)}'
                return jsonify({
                    'status': 'success',
                    'original': original_url,
                    'enhanced': enhanced_url
                })
            else:
                return jsonify({'status': 'error', 'message': 'Image enhancement failed on the server.'}), 500
        except Exception as e:
            print(f"!!! Server Error during upload/enhance: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'status': 'error', 'message': 'An unexpected server error occurred.'}), 500
    else:
        return jsonify({'status': 'error', 'message': 'File type not allowed. Please upload PNG, JPG, JPEG, or WebP.'}), 400


@app.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    """Serves files from the upload directory securely."""
    # --- This route remains the same ---
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- Run the App ---
if __name__ == '__main__':
    print("--- Starting Flask App (API Key NOT loaded from .env) ---")
    if not os.path.exists('templates'): os.makedirs('templates')
    if not os.path.exists('templates/index.html'): print("!!! WARNING: 'templates/index.html' not found.")
    print(f"Upload folder: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
    print("Flask server running on http://127.0.0.1:5000 (Press CTRL+C to quit)")
    app.run(host='0.0.0.0', port=5000, debug=True)