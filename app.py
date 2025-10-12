import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS 

# --- Configuration ---
app = Flask(__name__)
# Enable CORS for all routes (important for front-end access)
CORS(app)

# Define the folder where uploads will be stored
UPLOAD_FOLDER = 'uploads'
# Define the file to store post metadata
METADATA_FILE = 'posts_metadata.json'

# Create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ensure the metadata file exists and is a valid JSON list
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, 'w') as f:
        json.dump([], f)

# --- Utility Functions ---

def load_metadata():
    """Loads all post metadata from the JSON file."""
    # Ensure the file is not empty before attempting to load
    if os.path.getsize(METADATA_FILE) == 0:
        return []
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def save_metadata(metadata_list):
    """Saves the updated post metadata list to the JSON file."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata_list, f, indent=4)

def generate_unique_id():
    """Generates a simple unique ID based on the current timestamp."""
    return str(int(time.time() * 1000))

# --- API Routes ---

@app.route('/api/post', methods=['POST'])
def upload_post():
    """Handles file upload and saves post metadata."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files['file']
    author = request.form.get('author', 'Anonymous')
    caption = request.form.get('caption', '(no caption)')
    
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    allowed_extensions = {'mp4', 'mov', 'webm', 'mp3', 'wav'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({"error": "Invalid file type. Only video/audio files are allowed."}), 400

    try:
        extension = file.filename.rsplit('.', 1)[1].lower()
        post_id = generate_unique_id()
        filename = secure_filename(f"{post_id}.{extension}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the file to the uploads folder
        file.save(filepath)

        # 4. Save Metadata
        new_post = {
            "id": post_id,
            "filename": filename,
            "author": author,
            "caption": caption,
            "is_audio": extension in ['mp3', 'wav'],
            "timestamp": datetime.now().isoformat(),
            "views": 0,
            "likes": 0,
        }
        
        metadata = load_metadata()
        metadata.insert(0, new_post)
        save_metadata(metadata)

        return jsonify({"message": "Upload successful!", "id": post_id}), 200

    except Exception as e:
        print(f"Error during upload: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/feed', methods=['GET'])
def get_feed():
    """Returns the list of all posts to populate the main feed."""
    try:
        metadata = load_metadata()
        # In a real app, you would transform the data to include media URLs
        # For deployment, the media URL structure will be:
        # f"/api/media/{post['filename']}" (on the Render server)
        return jsonify(metadata), 200
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return jsonify({"error": "Could not retrieve feed data."}), 500

@app.route('/api/post/<post_id>', methods=['GET'])
def get_single_post(post_id):
    """Retrieves the metadata for a single post by its ID and increments the 'views' count."""
    try:
        metadata = load_metadata()
        
        for post in metadata:
            if post['id'] == post_id:
                # Increment views
                post['views'] = post.get('views', 0) + 1
                save_metadata(metadata)
                
                return jsonify(post), 200
        
        return jsonify({"error": "Post not found."}), 404

    except Exception as e:
        print(f"Error fetching single post: {e}")
        return jsonify({"error": "Could not retrieve post data."}), 500


@app.route('/api/like/<post_id>', methods=['POST'])
def like_post(post_id):
    """Increments the 'likes' count for a specific post ID."""
    try:
        metadata = load_metadata()
        found = False
        
        for post in metadata:
            if post['id'] == post_id:
                post['likes'] = post.get('likes', 0) + 1
                found = True
                break
        
        if found:
            save_metadata(metadata)
            return jsonify({"message": "Like registered successfully."}), 200
        else:
            return jsonify({"error": "Post not found."}), 404
            
    except Exception as e:
        print(f"Error during like operation: {e}")
        return jsonify({"error": "An internal server error occurred during like update."}), 500


@app.route('/api/media/<filename>')
def serve_media(filename):
    """Serves the actual audio/video file from the 'uploads' directory."""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({"error": "Media file not found."}), 404

# --- Run the application ---
if __name__ == '__main__':
    # When deployed with gunicorn (on Render), this section is ignored.
    app.run(debug=True, host='0.0.0.0', port=5000)
