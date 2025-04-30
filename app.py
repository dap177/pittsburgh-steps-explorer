from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for
import os
import json
import logging
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'images', 'user_uploads')
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}
app.config['GCS_BUCKET'] = 'pittsburgh-steps-uploads'
app.config['USE_CLOUD_STORAGE'] = os.environ.get('GAE_ENV', '').startswith('standard')

# Create upload folder if it doesn't exist (for local development)
if not app.config['USE_CLOUD_STORAGE']:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
GEOJSON_FILE = 'Pittsburgh_Steps.geojson'
USER_CONTRIBUTIONS_FILE = 'user_contributions.json'

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize GCS client for cloud storage
storage_client = None
if app.config['USE_CLOUD_STORAGE']:
    try:
        storage_client = storage.Client()
    except Exception as e:
        logger.error(f"Error initializing Google Cloud Storage client: {e}")

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to get available image filenames
def get_available_images():
    image_dir = os.path.join(app.static_folder, 'images')
    available_images = {}
    
    if os.path.exists(image_dir):
        for filename in os.listdir(image_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                # Try to extract step ID from filename
                try:
                    # Check for numeric prefixes (like "020", "042", etc.)
                    parts = filename.split(' ')[0]
                    if parts.isdigit():
                        step_id = parts.lstrip('0')  # Remove leading zeros
                        available_images[step_id] = filename
                except:
                    # If we can't extract an ID, just continue
                    pass
        
        # For local development, check user uploads folder
        if not app.config['USE_CLOUD_STORAGE']:
            uploads_dir = os.path.join(image_dir, 'user_uploads')
            if os.path.exists(uploads_dir):
                for filename in os.listdir(uploads_dir):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        # User uploaded images follow format: step_id_timestamp.jpg
                        try:
                            parts = filename.split('_')
                            if len(parts) >= 2:
                                step_id = parts[0]
                                if step_id.isdigit():
                                    available_images[step_id] = f'user_uploads/{filename}'
                        except:
                            # If we can't extract an ID, just continue
                            pass
        
        # For GAE deployment, check Cloud Storage for user uploads
        elif app.config['USE_CLOUD_STORAGE'] and storage_client:
            try:
                bucket = storage_client.bucket(app.config['GCS_BUCKET'])
                blobs = bucket.list_blobs()
                
                for blob in blobs:
                    if blob.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        # User uploaded images follow format: step_id_timestamp.jpg
                        try:
                            parts = blob.name.split('_')
                            if len(parts) >= 2:
                                step_id = parts[0]
                                if step_id.isdigit():
                                    # Store with GCS URL
                                    available_images[step_id] = f"gcs:{blob.name}"
                        except:
                            # If we can't extract an ID, just continue
                            pass
            except Exception as e:
                logger.error(f"Error listing GCS blobs: {e}")
    
    logger.debug(f"Found {len(available_images)} images with step IDs")
    return available_images

# Function to load all steps data
def load_steps_data():
    steps_data = []
    available_images = get_available_images()
    
    # Read GeoJSON file
    try:
        with open(GEOJSON_FILE, 'r') as f:
            geojson_data = json.load(f)
        
        if 'features' in geojson_data:
            logger.info(f"Found {len(geojson_data['features'])} features in GeoJSON")
            
            for feature in geojson_data['features']:
                try:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    
                    # Skip features without geometry
                    if not geometry or 'coordinates' not in geometry:
                        continue
                    
                    # Get coordinates (GeoJSON uses [longitude, latitude] format)
                    coordinates = geometry['coordinates']
                    if geometry['type'] == 'Point':
                        longitude, latitude = coordinates
                    elif geometry['type'] == 'LineString' and len(coordinates) > 0:
                        # Use the first point of the line
                        longitude, latitude = coordinates[0]
                    else:
                        # Skip features with unsupported geometry types
                        continue
                    
                    # Check if this step has a picture
                    has_picture = str(properties.get('pix', '')).lower() == 'y'
                    step_id = str(properties.get('id', ''))
                    
                    # Check if we have a matching image for this step
                    if step_id in available_images:
                        image_path = available_images[step_id]
                        if image_path.startswith('gcs:'):
                            # For Cloud Storage images, create a signed URL or use a serving URL
                            blob_name = image_path.replace('gcs:', '')
                            image_url = f"/api/images/{blob_name}"
                        else:
                            image_url = f'/static/images/{image_path}'
                        has_picture = True
                    else:
                        image_url = '/static/images/no_image.jpg'
                    
                    step = {
                        'id': step_id,
                        'location': str(properties.get('location', '')),
                        'from_street': str(properties.get('from_stree', '')),
                        'to_street': str(properties.get('to_street', '')),
                        'steps_count': int(properties.get('steps', 0) or 0),
                        'length_feet': float(properties.get('l_feet', 0) or 0),
                        'width': float(properties.get('width', 0) or 0),
                        'year_built': str(properties.get('year', '')),
                        'comment': str(properties.get('comment', '')).strip(),
                        'style': int(properties.get('style', 0) or 0),
                        'segments': int(properties.get('segs', 0) or 0),
                        'neighborhood': str(properties.get('hood', '')),
                        'has_picture': has_picture,
                        'image_url': image_url,
                        'latitude': latitude,
                        'longitude': longitude,
                        'user_submitted': False
                    }
                    steps_data.append(step)
                except Exception as e:
                    logger.exception(f"Error processing feature: {e}", exc_info=True)
                    continue
    except Exception as e:
        logger.exception(f"Error reading GeoJSON file: {e}", exc_info=True)
    
    # Load user-contributed steps
    try:
        if os.path.exists(USER_CONTRIBUTIONS_FILE):
            with open(USER_CONTRIBUTIONS_FILE, 'r') as f:
                user_steps = json.load(f)
                
            for step in user_steps:
                # Mark as user submitted
                step['user_submitted'] = True
                steps_data.append(step)
                
            logger.info(f"Loaded {len(user_steps)} user-contributed steps")
    except Exception as e:
        logger.exception(f"Error reading user contributions file: {e}", exc_info=True)
    
    return steps_data

@app.route('/')
def index():
    return render_template('index.html', api_key=GOOGLE_MAPS_API_KEY)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/images/<path:filename>')
def serve_gcs_image(filename):
    """Serve images from Google Cloud Storage"""
    if app.config['USE_CLOUD_STORAGE'] and storage_client:
        try:
            bucket = storage_client.bucket(app.config['GCS_BUCKET'])
            blob = bucket.blob(filename)
            
            # Generate a signed URL for the blob
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=15),
                method="GET"
            )
            return redirect(url)
        except Exception as e:
            logger.exception(f"Error serving image from GCS: {e}", exc_info=True)
            return "", 404
    
    # Fallback to local file for development
    return send_from_directory(os.path.join(app.static_folder, 'images', 'user_uploads'), filename)

@app.route('/api/steps')
def get_steps():
    try:
        logger.info("Loading steps data...")
        steps_data = load_steps_data()
        
        logger.info(f"Successfully loaded {len(steps_data)} total steps")
        if steps_data:
            logger.debug("First step: %s", steps_data[0])
        return jsonify(steps_data)
        
    except Exception as e:
        logger.exception(f"Error loading steps data: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/steps/upload-photo', methods=['POST'])
def upload_photo():
    try:
        # Check if step_id is provided
        if 'step_id' not in request.form:
            return jsonify({"error": "Step ID is required"}), 400
            
        step_id = request.form['step_id']
        
        # Check if file is provided
        if 'photo' not in request.files:
            return jsonify({"error": "No file part"}), 400
            
        file = request.files['photo']
        
        # If user doesn't select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if file and allowed_file(file.filename):
            # Create a unique filename: step_id_timestamp.extension
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{step_id}_{timestamp}.{extension}"
            
            # Secure the filename
            filename = secure_filename(filename)
            
            # Check if we're running in App Engine (use GCS) or locally
            if app.config['USE_CLOUD_STORAGE'] and storage_client:
                try:
                    # Upload to Google Cloud Storage
                    bucket = storage_client.bucket(app.config['GCS_BUCKET'])
                    blob = bucket.blob(filename)
                    
                    # Upload file content
                    blob.upload_from_file(file)
                    logger.info(f"Photo uploaded to GCS for step {step_id}: {filename}")
                    
                    return jsonify({
                        "success": True,
                        "image_url": f"/api/images/{filename}"
                    })
                except Exception as e:
                    logger.exception(f"Error uploading to GCS: {e}", exc_info=True)
                    return jsonify({"error": f"Error uploading to cloud storage: {str(e)}"}), 500
            else:
                # Save locally (for development)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                logger.info(f"Photo uploaded locally for step {step_id}: {filename}")
                
                return jsonify({
                    "success": True,
                    "image_url": f"/static/images/user_uploads/{filename}"
                })
        else:
            return jsonify({"error": "File type not allowed"}), 400
            
    except Exception as e:
        logger.exception(f"Error uploading photo: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/steps/add', methods=['POST'])
def add_step():
    try:
        # Extract step data from form
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ['location', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        # Generate a unique ID for the new step
        # Use the current max ID + 1, or a uuid if no steps exist
        steps_data = load_steps_data()
        
        try:
            max_id = max([int(step['id']) for step in steps_data if step['id'].isdigit()])
            new_id = str(max_id + 1)
        except (ValueError, TypeError):
            # If no numeric IDs exist, start from 5000 (to avoid conflicts)
            new_id = "5000"
            
        # Create new step object
        new_step = {
            'id': new_id,
            'location': data.get('location', ''),
            'from_street': data.get('from_street', ''),
            'to_street': data.get('to_street', ''),
            'steps_count': int(data.get('steps_count', 0) or 0),
            'length_feet': float(data.get('length_feet', 0) or 0),
            'width': float(data.get('width', 0) or 0),
            'year_built': data.get('year_built', ''),
            'comment': data.get('comment', ''),
            'neighborhood': data.get('neighborhood', ''),
            'has_picture': False,
            'image_url': '/static/images/no_image.jpg',
            'latitude': float(data.get('latitude')),
            'longitude': float(data.get('longitude')),
            'user_submitted': True,
            'submit_date': datetime.now().isoformat()
        }
        
        # Save to user contributions file
        user_steps = []
        if os.path.exists(USER_CONTRIBUTIONS_FILE):
            try:
                with open(USER_CONTRIBUTIONS_FILE, 'r') as f:
                    user_steps = json.load(f)
            except:
                user_steps = []
                
        user_steps.append(new_step)
        
        with open(USER_CONTRIBUTIONS_FILE, 'w') as f:
            json.dump(user_steps, f, indent=2)
            
        logger.info(f"New step added: ID {new_id}, {new_step['location']}")
        
        # Handle photo upload if provided
        if 'photo' in request.files and request.files['photo'].filename != '':
            file = request.files['photo']
            
            if allowed_file(file.filename):
                # Create filename with step ID
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{new_id}_{timestamp}.{extension}"
                
                # Secure the filename
                filename = secure_filename(filename)
                
                # Check if we're running in App Engine (use GCS) or locally
                if app.config['USE_CLOUD_STORAGE'] and storage_client:
                    try:
                        # Upload to Google Cloud Storage
                        bucket = storage_client.bucket(app.config['GCS_BUCKET'])
                        blob = bucket.blob(filename)
                        
                        # Upload file content
                        blob.upload_from_file(file)
                        logger.info(f"Photo uploaded to GCS for new step {new_id}: {filename}")
                        
                        # Update step with image info
                        new_step['has_picture'] = True
                        new_step['image_url'] = f"/api/images/{filename}"
                    except Exception as e:
                        logger.exception(f"Error uploading new step photo to GCS: {e}", exc_info=True)
                else:
                    # Save locally (for development)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    # Update step with image info
                    new_step['has_picture'] = True
                    new_step['image_url'] = f"/static/images/user_uploads/{filename}"
                
                # Update the saved data
                with open(USER_CONTRIBUTIONS_FILE, 'w') as f:
                    json.dump(user_steps, f, indent=2)
                    
                logger.info(f"Photo added for new step {new_id}: {filename}")
        
        return jsonify({
            "success": True,
            "step": new_step
        })
        
    except Exception as e:
        logger.exception(f"Error adding new step: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Gunicorn will run the app, so this is only for local development
    # When running locally, ensure the PORT environment variable isn't set if you want port 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False)