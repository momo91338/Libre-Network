import hashlib
import time
import json
from storage import Storage

class Blockchain:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.ensure_genesis()

    def ensure_genesis(self):
        if self.storage.get_block_count() == 0:
            genesis_block = {
                "block_number": 0,
                "prev_hash": "0" * 64,
                "state_hash": "0" * 64, # Initial state hash
                "combined_hash": "0" * 64,
                "group_id": 0,
                "miner": "GENESIS",
                "timestamp": int(time.time()),
                "executed_tx_count": 0,
                "signatures": []
            }
            # Create initial group
            self.storage.save_group(0, {}, int(time.time()))
            self.storage.save_block(genesis_block)

    def create_block(self, state, miner, signatures, group_id):
        latest = self.storage.get_latest_block()
        block_number = latest["block_number"] + 1
        
        # State hash from deterministic state
        state_hash = self.storage.compute_state_hash()
        
        # Combined hash for chaining (hash of block content)
        block_content = {
            "block_number": block_number,
            "prev_hash": latest["state_hash"],
            "state_hash": state_hash,
            "group_id": group_id,
            "miner": miner,
            "timestamp": int(time.time())
        }
        combined_hash = hashlib.sha256(json.dumps(block_content, sort_keys=True).encode()).hexdigest()
        
        block_data = {
            "block_number": block_number,
            "prev_hash": latest["state_hash"],
            "state_hash": state_hash,
            "combined_hash": combined_hash,
            "group_id": group_id,
            "miner": miner,
            "timestamp": block_content["timestamp"],
            "executed_tx_count": len(state.get("tx_executed", {})),
            "signatures": signatures
        }
        
        self.storage.save_block(block_data)
        return block_data

    def verify_chain(self):
        count = self.storage.get_block_count()
        if count <= 1: return True
        
        for i in range(1, count):
            prev = self.storage.get_block(i-1)
            curr = self.storage.get_block(i)
            
            if curr["prev_hash"] != prev["state_hash"]:
                return False
            
            # Verify combined hash
            block_content = {
                "block_number": curr["block_number"],
                "prev_hash": curr["prev_hash"],
                "state_hash": curr["state_hash"],
                "group_id": curr["group_id"],
                "miner": curr["miner"],
                "timestamp": curr["timestamp"]
            }
            computed_combined = hashlib.sha256(json.dumps(block_content, sort_keys=True).encode()).hexdigest()
            if computed_combined != curr["combined_hash"]:
                return False
                
        return True

    def get_latest_block(self):
        return self.storage.get_latest_block()

    def get_height(self):
        return self.storage.get_block_count() - 1
