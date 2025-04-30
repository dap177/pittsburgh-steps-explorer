# Pittsburgh Steps Explorer

An interactive web application for exploring and documenting Pittsburgh's public staircases. This application maps over 700 public steps throughout Pittsburgh, allowing users to explore, filter, and contribute to the database.

## Live Demo

Visit the live application: [Pittsburgh Steps Explorer](https://annular-ray-445804-r8.nn.r.appspot.com)

## Features

- Interactive Google Maps interface showing all steps locations
- Detailed information about each set of steps (count, length, neighborhood, etc.)
- Photo uploads for existing steps
- Add new steps to the database with location information
- Mobile-friendly responsive design
- Find steps nearest to your current location
- Filter steps by various criteria

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Maps**: Google Maps API
- **Storage**: Google Cloud Storage
- **Hosting**: Google App Engine
- **Database**: JSON-based with GeoJSON for steps data

## Local Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/dap177/pittsburgh-steps-explorer.git
   cd pittsburgh-steps-explorer
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Google Maps API key:
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Visit `http://localhost:5000` in your browser

## Deployment

The application is configured for Google App Engine deployment with CI/CD pipeline via GitHub Actions.

### Automatic Deployment

Push to the master branch to trigger automatic deployment via GitHub Actions.

### Manual Deployment

```
gcloud app deploy
```

See `custom_domain_setup.md` for instructions on setting up a custom domain.

## Monitoring and Maintenance

- Cloud Monitoring dashboard is available in the GCP Console
- Check logs with: `gcloud app logs read`
- Performance monitoring with Cloud Monitoring metrics

## Security Features

- Rate limiting on API endpoints to prevent abuse
- Secure file uploads with type checking and size limits
- Cloud Storage bucket policy for secure access control

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- City of Pittsburgh for the original steps data
- Bob Regan's "The Steps of Pittsburgh: Portrait of a City" for inspiration
- All contributors who have uploaded photos and added steps
