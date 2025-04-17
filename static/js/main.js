let map;
let panorama;

async function initMap() {
    // Center on Pittsburgh
    const pittsburgh = { lat: 40.4406, lng: -79.9959 };
    
    map = new google.maps.Map(document.getElementById("map"), {
        center: pittsburgh,
        zoom: 12,
    });

    panorama = new google.maps.StreetViewPanorama(
        document.getElementById("pano"), {
            position: pittsburgh,
            pov: {
                heading: 0,
                pitch: 0
            }
        }
    );

    map.setStreetView(panorama);

    try {
        const response = await fetch('/api/steps');
        const steps = await response.json();
        
        for (const step of steps) {
            const position = { lat: step.latitude, lng: step.longitude };
            
            // Define the custom icon (blue circle)
            const stepIcon = {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: '#4285F4', // Google Blue
                fillOpacity: 1,
                strokeColor: '#ffffff', // White border
                strokeWeight: 1,
                scale: 8 // Adjust size as needed
            };

            // Use standard Marker with custom icon and label
            const marker = new google.maps.Marker({
                position,
                map,
                title: step.name,
                icon: stepIcon, // Use the custom circle icon
                label: {
                  text: "S", // Add the 'S' label
                  color: "#ffffff", // White text
                  fontSize: "10px",
                  fontWeight: "bold"
                }
            });

            marker.addListener("click", async () => {
                const sv = new google.maps.StreetViewService();
                
                try {
                    const data = await sv.getPanorama({ 
                        location: position,
                        radius: 50,
                        source: google.maps.StreetViewSource.OUTDOOR
                    });
                    
                    const heading = google.maps.geometry.spherical.computeHeading(
                        data.location.latLng,
                        position
                    );
                    
                    panorama.setPosition(data.location.latLng);
                    panorama.setPov({
                        heading: heading,
                        pitch: 0
                    });
                } catch (e) {
                    console.warn("Street View not available for: " + step.name);
                }
            });
        }
    } catch (error) {
        console.error("Error loading steps data:", error);
    }
}

window.onload = initMap;
