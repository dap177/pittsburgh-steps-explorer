#!/usr/bin/env python
"""
Local Environment Setup Script for Pittsburgh Steps Explorer
This script helps set up a local development environment.
"""

import os
import sys
import shutil

def create_env_file():
    """Create a .env file for local development"""
    env_example = '.env.example'
    env_file = '.env'
    
    if not os.path.exists(env_example):
        print("Error: .env.example file not found!")
        return False
    
    # Create new .env file from example (non-interactive)
    with open(env_example, 'r') as example:
        template = example.read()
    
    # Use placeholder or default API key (you can update manually after)
    maps_api_key = "your_google_maps_api_key_here"
    
    # Replace the API key in the template
    env_content = template.replace("your_google_maps_api_key_here", maps_api_key)
    
    # Write the .env file if it doesn't exist
    if not os.path.exists(env_file):
        with open(env_file, 'w') as env:
            env.write(env_content)
        print(f"Created {env_file} file successfully!")
    else:
        print(f"{env_file} already exists. Using existing file.")
    
    return True

def create_uploads_directory():
    """Create directory for user uploads in local development"""
    uploads_dir = os.path.join('static', 'images', 'user_uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"Created {uploads_dir} directory for local file uploads")
    else:
        print(f"{uploads_dir} directory already exists")
    return True

def main():
    """Main function to set up local environment"""
    print("Setting up local development environment for Pittsburgh Steps Explorer...")
    
    success = create_env_file()
    if not success:
        print("Failed to set up environment file.")
        return
    
    success = create_uploads_directory()
    if not success:
        print("Failed to create uploads directory.")
        return
    
    print("\n--- Local Environment Setup Complete ---")
    print("\nTo run the application locally:")
    print("1. Activate the virtual environment:")
    print("   - Windows: .\\venv\\Scripts\\activate")
    print("   - macOS/Linux: source venv/bin/activate")
    print("2. Start the Flask development server:")
    print("   python app.py")
    print("\nThe application will be available at: http://localhost:5000")

if __name__ == "__main__":
    main()
