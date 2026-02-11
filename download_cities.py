import osmnx as ox
import os
import subprocess
import sys

# Configuration
CITIES = {
    "berlin": "Berlin, Germany",
    "los_angeles": "Los Angeles, California, USA",
    "madrid": "Madrid, Spain",
    "paris": "Paris, France",
    "hanoi": "Hanoi, Vietnam"
}

# Updates path to 'data/networks'
NETWORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "networks")
os.makedirs(NETWORK_DIR, exist_ok=True)

def download_and_convert(city_key, place_name):
    print(f"Processing {place_name}...")
    
    # 1. Download Graph from OSM
    # We download a simplified graph (drive network)
    try:
        print(f"  Downloading OSM data for {place_name}...")
        # Use a central point and radius to avoid huge downloads
        # Coordinates are approximate centers - Updated for consistency
        centers = {
            "berlin": (52.5200, 13.4050),
            "los_angeles": (34.0522, -118.2437),
            "madrid": (40.4168, -3.7038),
            "paris": (48.8566, 2.3522),
            "hanoi": (21.0285, 105.8542)
        }
        
        if city_key in centers:
            point = centers[city_key]
            # Increased radius for better sampling
            G = ox.graph_from_point(point, dist=3000, network_type='drive', simplify=False)
        else:
            G = ox.graph_from_place(place_name, network_type='drive', simplify=False)
        
        # Save as OSM XML (temp)
        osm_file = os.path.join(NETWORK_DIR, f"{city_key}.osm.xml")
        ox.save_graph_xml(G, filepath=osm_file)
        print(f"  Saved OSM data to {osm_file}")
        
        # 2. Convert to SUMO .net.xml using netconvert
        net_file = os.path.join(NETWORK_DIR, f"{city_key}.net.xml")
        print(f"  Converting to SUMO network: {net_file}")
        
        # Check for netconvert
        cmd = [
            "netconvert",
            "--osm-files", osm_file,
            "-o", net_file,
            "--geometry.remove", "true",
            "--roundabouts.guess", "true",
            "--ramps.guess", "true",
            "--junctions.join", "true",
            "--tls.guess", "true",
            "--tls.discard-simple", "true",
            "--tls.join", "true",
            "--no-turnarounds", "true"
        ]
        
        subprocess.run(cmd, check=True)
        print(f"  Successfully created {net_file}")
        
        # Cleanup OSM file
        os.remove(osm_file)
        
    except Exception as e:
        print(f"  ERROR processing {city_key}: {e}")

if __name__ == "__main__":
    print(f"Starting map download to {NETWORK_DIR}...")
    
    # Check if netconvert is available
    try:
        subprocess.run(["netconvert", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: 'netconvert' not found in PATH. Please ensure SUMO is installed and added to PATH.")
        sys.exit(1)

    for key, place in CITIES.items():
        target_file = os.path.join(NETWORK_DIR, f"{key}.net.xml")
        if os.path.exists(target_file):
            print(f"Skipping {key} (already exists)")
            continue
            
        download_and_convert(key, place)
        
    print("Done!")
