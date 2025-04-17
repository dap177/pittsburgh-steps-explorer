from flask import Flask, render_template, jsonify, send_from_directory
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    
    logger.debug(f"Found {len(available_images)} images with step IDs")
    return available_images

@app.route('/')
def index():
    return render_template('index.html', api_key=GOOGLE_MAPS_API_KEY)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/steps')
def get_steps():
    try:
        logger.info("Loading steps data from GeoJSON...")
        steps_data = []
        available_images = get_available_images()
        
        # Read GeoJSON file
        with open('Pittsburgh_Steps.geojson', 'r') as f:
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
                        image_url = f'/static/images/{available_images[step_id]}'
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
                        'longitude': longitude
                    }
                    steps_data.append(step)
                except Exception as e:
                    logger.exception(f"Error processing feature: {e}", exc_info=True)
                    continue
        
        logger.info(f"Successfully loaded {len(steps_data)} steps")
        if steps_data:
            logger.debug("First step: %s", steps_data[0])
        return jsonify(steps_data)
        
    except Exception as e:
        logger.exception(f"Error reading GeoJSON file: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Gunicorn will run the app, so this is only for local development
    # When running locally, ensure the PORT environment variable isn't set if you want port 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False)