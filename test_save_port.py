import json
import os

DATA_DIR = "libre_data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

def read_json(path):
    if not os.path.exists(path): return {}
    with open(path, "r") as f:
        return json.load(f)

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def test_save_port(port):
    print(f"Testing port: {port}")
    try:
        if not (1024 <= port <= 65535):
            raise ValueError("Port out of range")
        
        config = read_json(CONFIG_FILE)
        config["network_port"] = port
        write_json(CONFIG_FILE, config)
        
        # Verify
        saved_config = read_json(CONFIG_FILE)
        if saved_config.get("network_port") == port:
            print(f"SUCCESS: Port {port} saved correctly.")
        else:
            print(f"FAILURE: Port {port} not saved correctly.")
    except Exception as e:
        print(f"EXPECTED ERROR: {e}")

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Backup existing config if any
    backup = None
    if os.path.exists(CONFIG_FILE):
        backup = read_json(CONFIG_FILE)
    
    try:
        test_save_port(8080)
        test_save_port(65536)
        test_save_port(1023)
    finally:
        # Restore backup
        if backup:
            write_json(CONFIG_FILE, backup)
        print("Test complete and cleanup done.")
