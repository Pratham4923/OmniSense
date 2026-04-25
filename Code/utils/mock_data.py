import os
import random
import glob
from datetime import datetime

# Paths to the datasets
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AMBULANCE_DIR = os.path.join(BASE_DIR, "Ambulance")
FIRETRUCK_DIR = os.path.join(BASE_DIR, "Firetrucks", "Firetrucks")

def get_random_asset(category, sub_folder):
    """Picks a random file from the dataset folders."""
    if category == "Ambulance":
        search_path = os.path.join(AMBULANCE_DIR, sub_folder)
    else:
        search_path = os.path.join(FIRETRUCK_DIR, sub_folder)
    
    # Handle case mismatch: try title-case if lowercase doesn't exist
    if not os.path.exists(search_path):
        search_path = os.path.join(
            AMBULANCE_DIR if category == "Ambulance" else FIRETRUCK_DIR,
            sub_folder.capitalize(),
        )

    if sub_folder in ("images", "Images"):
        test_path = os.path.join(search_path, "Test")
        if os.path.exists(test_path):
            search_path = test_path
            
    files = glob.glob(os.path.join(search_path, "*.*"))
    if not files:
        return None
    return random.choice(files)

def get_rfid_data(emergency_type=None):
    if emergency_type:
        return {
            "vehicle_id": f"EMRG-{emergency_type[:3].upper()}-911",
            "authenticated": True,
            "type": f"Emergency ({emergency_type})",
            "last_active": datetime.now().strftime("%H:%M:%S")
        }
    return {
        "vehicle_id": f"PVT-{random.randint(1000, 9999)}",
        "authenticated": False,
        "type": "Private Vehicle",
        "last_active": "N/A"
    }

def get_acoustic_data(emergency_type=None):
    if emergency_type:
        sound_file = get_random_asset(emergency_type, "sounds")
        return {
            "confidence": random.uniform(0.92, 0.99),
            "siren_detected": True,
            "label": f"{emergency_type} Siren",
            "audio_path": sound_file,
            "decibel": random.uniform(85, 110)
        }
    return {
        "confidence": random.uniform(0.05, 0.2),
        "siren_detected": False,
        "label": "Ambient Noise",
        "audio_path": None,
        "decibel": random.uniform(40, 60)
    }

def get_vision_data(emergency_type=None):
    if emergency_type:
        image_file = get_random_asset(emergency_type, "images")
        return {
            "detected": True,
            "confidence": random.uniform(0.9, 0.98),
            "distance_m": random.uniform(15.0, 40.0),
            "label": emergency_type,
            "image_path": image_file,
            "frame_rate": random.uniform(28, 32)
        }
    return {
        "detected": False,
        "confidence": random.uniform(0.1, 0.25),
        "distance_m": random.uniform(50.0, 150.0),
        "label": "Road Normal",
        "image_path": None,
        "frame_rate": 30.0
    }

def get_green_wave_path():
    """Returns a list of junctions for the Green Wave simulation."""
    # Bengaluru south-to-central emergency corridor
    path = [
        {"id": "BLR-01", "name": "Silk Board Junction", "coords": [12.9177, 77.6238]},
        {"id": "BLR-02", "name": "Madiwala Check Post", "coords": [12.9266, 77.6204]},
        {"id": "BLR-03", "name": "Adugodi Signal", "coords": [12.9416, 77.6145]},
        {"id": "BLR-04", "name": "Shantinagar Junction", "coords": [12.9567, 77.5937]},
        {"id": "BLR-05", "name": "Richmond Circle", "coords": [12.9666, 77.5997]},
    ]
    return path

def get_system_history():
    """Simulates preemption history for charts."""
    # Last 10 seconds of preemption events
    return [random.randint(0, 1) for _ in range(20)]

def get_traffic_metrics():
    return {
        "eta_reduction": random.uniform(38, 45),
        "detection_accuracy": random.uniform(99.1, 99.9),
        "false_trigger_rate": random.uniform(0.005, 0.02),
        "latency_ms": random.uniform(85, 110)
    }
