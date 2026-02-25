import json
import os
import time
import random
import uuid

DEFAULT_DATA_DIR = "libre_data"
CONFIG_FILE = os.path.join(DEFAULT_DATA_DIR, "config.json")

class Config:
    def __init__(self, data_dir=DEFAULT_DATA_DIR):
        self.data_dir = data_dir
        self.config_path = os.path.join(self.data_dir, "config.json")
        self.ensure_data_dir()
        self.config = self.load_config()

    def ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def load_config(self):
        default_config = {
            "node_id": str(uuid.uuid4()),
            "port": 5000,
            "known_peers": [], # List of {"ip": "...", "port": ...}
            "language": "en",
            "logo_path": ""
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle missing keys
                    for key, value in default_config.items():
                        if key not in loaded:
                            loaded[key] = value
                    return loaded
            except Exception as e:
                print(f"Error loading config: {e}")
        
        self.save_config(default_config)
        return default_config

    def save_config(self, config=None):
        if config:
            self.config = config
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    @property
    def node_id(self):
        return self.config.get("node_id")

    @property
    def port(self):
        return self.config.get("port")

    @port.setter
    def port(self, value):
        self.set("port", value)

    @property
    def known_peers(self):
        return self.config.get("known_peers", [])

    def add_peer(self, ip, port):
        peers = self.known_peers
        if not any(p["ip"] == ip and p["port"] == port for p in peers):
            peers.append({"ip": ip, "port": port})
            self.set("known_peers", peers)
