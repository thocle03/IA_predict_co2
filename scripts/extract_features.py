import os
import traceback
import glob
import pandas as pd
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigs
import sumolib
import xml.etree.ElementTree as ET

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET_DIR = os.path.join(BASE_DIR, "data", "networks")
SIM_DIR = os.path.join(BASE_DIR, "data", "simulations")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "dataset_ia_complet.csv")

# Import the advanced analyzer
sys.path.append(os.path.join(BASE_DIR, "scripts"))
import analyze_city_structure as analyzer

def get_spectral_properties(net_file):
    """
    Leverages the advanced analyzer to get high-fidelity spectral features.
    """
    m = analyzer.analyze_topology(net_file)
    if not m: return None
    
    return {
        "n_nodes": m['node_count'],
        "n_edges": m['edge_count'],
        "density": m['edge_count'] / (m['node_count'] * (m['node_count']-1)),
        "spectral_radius": m['spectral_radius'],
        "kreiss_constant": m['kreiss_constant'],
        "h2_norm": m['h2_norm'],
        "h_inf_norm": m['h_inf_norm'],
        "avg_degree": m['avg_degree']
    }

def process_simulations():
    print("Starting Feature Extraction...")
    data_points = []
    
    sim_files = glob.glob(os.path.join(SIM_DIR, "*.csv"))
    
    for sim_file in sim_files:
        filename = os.path.basename(sim_file).lower()
        print(f"Processing Simulation: {filename}")
        
        # Identify City
        city = "unknown"
        for c in ["paris", "berlin", "madrid", "los-angeles", "hanoi"]: 
            if c in filename:
                city = c.replace("-", "_") 
                break
        
        if city == "unknown":
            print("  Skipping: Could not identify city name in filename.")
            continue
            
        # 1. Get Graph Features
        net_path = os.path.join(NET_DIR, f"{city}.net.xml")
        if not os.path.exists(net_path):
            print(f"  Warning: Network file {net_path} not found. Skipping graph features.")
            graph_features = {}
        else:
            graph_features = get_spectral_properties(net_path)
            
        if not graph_features:
            continue
            
        # 2. Get Pollution/Traffic Targets
        try:
            chunk_size = 100000
            total_co2 = 0
            total_nox = 0
            total_fuel = 0
            weighted_speed_sum = 0
            total_records = 0
            
            chunk_iter = pd.read_csv(sim_file, usecols=['CO2_g_s', 'NOx_g_s', 'speed', 'fuel_l_s'], chunksize=chunk_size, on_bad_lines='skip')
            
            for chunk in chunk_iter:
                chunk = chunk.apply(pd.to_numeric, errors='coerce').fillna(0)
                
                total_co2 += chunk['CO2_g_s'].sum()
                total_nox += chunk['NOx_g_s'].sum()
                total_fuel += chunk['fuel_l_s'].sum()
                weighted_speed_sum += chunk['speed'].sum()
                total_records += len(chunk)
            
            avg_speed = weighted_speed_sum / total_records if total_records > 0 else 0
            
            row = {
                "city": city,
                "simulation_file": filename,
                "total_vehicles": 10000, 
                "total_co2_kg": total_co2 / 1000.0,
                "total_nox_kg": total_nox / 1000.0,
                "avg_speed_mps": avg_speed,
                **graph_features
            }
            
            data_points.append(row)
            print(f"  Stats: {row['total_co2_kg']:.2f} kg CO2, Rho={row.get('spectral_radius', 0):.2f}")
            
        except Exception as e:
            print(f"  Error reading CSV {sim_file}: {e}")
            traceback.print_exc()
            
    # Save Dataset
    if data_points:
        df = pd.DataFrame(data_points)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Dataset saved to {OUTPUT_FILE}")
        print(df)
    else:
        print("No data points generated.")

if __name__ == "__main__":
    process_simulations()
