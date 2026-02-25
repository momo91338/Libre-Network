import os
import sys
import time
import json
import threading
import hashlib
import secrets
from config import Config
from storage import Storage
from blockchain import Blockchain
from consensus import Consensus
from network import P2PNode

class LibreNode:
    def __init__(self):
        self.config = Config()
        self.storage = Storage(os.path.join(self.config.data_dir, "libre_network.db"))
        self.blockchain = Blockchain(self.storage)
        self.consensus = Consensus()
        
        self.node_id = self.config.node_id
        self.port = self.config.port
        self.host = "127.0.0.1"
        
        self.p2p = P2PNode(self.host, self.port, self.node_id, self.handle_message)
        
        # State locks
        self.state_lock = threading.Lock()
        
        # In-memory pools (not persistent)
        self.tx_pool = {}
        self.pending_updates = {} # hash -> data
        self.collected_signatures = {} # hash -> list
        
        self.mining_active = False

    def start(self):
        success, msg = self.p2p.start()
        if not success:
            print(f"Failed to start network: {msg}")
            return False
            
        # Connect to known peers
        for peer in self.config.known_peers:
            self.p2p.connect_to_peer(peer["ip"], peer["port"])
            
        # Initial sync logic
        threading.Thread(target=self._initial_sync, daemon=True).start()
        return True

    def _initial_sync(self):
        print("Starting initial sync...")
        time.sleep(2) # Wait for connections
        self.request_state_from_peers()

    def handle_message(self, message, addr):
        msg_type = message.get("type")
        
        if msg_type == "HELLO":
            self.p2p.add_peer(message["node_id"], addr[0], message["port"])
            # Record in config for persistence
            self.config.add_peer(addr[0], message["port"])
            
        elif msg_type == "PING":
            self.p2p.send_to_peer(addr[0], addr[1], {"type": "PONG", "node_id": self.node_id})
            
        elif msg_type == "STATE_REQUEST":
            self.send_state(addr[0], addr[1])
            
        elif msg_type == "STATE_UPDATE":
            self.on_receive_state_update(message)
            
        elif msg_type == "SIGNATURE_REQUEST":
            self.on_receive_signature_request(message)
            
        elif msg_type == "SIGNATURE_RESPONSE":
            self.on_receive_signature_response(message)
            
        elif msg_type == "BLOCK_ANNOUNCE":
            self.on_receive_block(message)

    def request_state_from_peers(self):
        msg = {"type": "STATE_REQUEST", "node_id": self.node_id}
        self.p2p.broadcast(msg)

    def send_state(self, ip, port):
        latest_block = self.storage.get_latest_block()
        latest_group = self.storage.get_latest_group()
        state_data = {
            "type": "STATE_UPDATE",
            "node_id": self.node_id,
            "block": latest_block,
            "group": latest_group,
            "users": self.storage.get_all_users()
        }
        self.p2p.send_to_peer(ip, port, state_data)

    def on_receive_state_update(self, msg):
        remote_block = msg.get("block")
        if not remote_block: return
        
        local_latest = self.storage.get_latest_block()
        if remote_block["block_number"] > local_latest["block_number"]:
            print(f"Found longer chain (height {remote_block['block_number']}). Syncing...")
            # In a real system, we'd request missing blocks one by one.
            # Here we replace if valid.
            self._apply_remote_state(msg)

    def _apply_remote_state(self, msg):
        with self.state_lock:
            # Simple replacement for this upgrade
            # In production, verify signatures and chain integrity
            remote_users = msg["users"]
            for addr, u in remote_users.items():
                self.storage.upsert_user(addr, u["balance"], u.get("nonce", 0), u.get("life", 20000000))
            
            self.storage.save_group(msg["group"]["group_id"], msg["group"]["miners"], msg["group"]["created_at"])
            self.storage.save_block(msg["block"])
            print("State synchronized.")

    def on_receive_signature_request(self, msg):
        state_hash = msg["state_hash"]
        proposed_state = msg["proposed_state"]
        
        # Verify state
        is_valid, reason = self.consensus.validate_proposed_state(msg["miner"], proposed_state, None, None)
        if not is_valid: return
        
        # Check if we are a selected signer
        group = self.storage.get_latest_group()
        selected = self.consensus.get_selected_miners(state_hash, group["miners"])
        
        # For simulation, we always sign if we are in the selected group
        # In real app, check if self.wallet_address in selected
        # sig = self.wallet.sign(state_hash)
        
        sig_response = {
            "type": "SIGNATURE_RESPONSE",
            "state_hash": state_hash,
            "signer": "DEMO_SIGNER", # In reality, use actual address
            "signature": "DEMO_SIG_" + secrets.token_hex(8)
        }
        self.p2p.send_to_peer(msg["miner_ip"], msg["miner_port"], sig_response)

    def on_receive_signature_response(self, msg):
        state_hash = msg["state_hash"]
        if state_hash in self.collected_signatures:
            self.collected_signatures[state_hash].append(msg)
            if len(self.collected_signatures[state_hash]) >= 100:
                self.finalize_block(state_hash)

    def finalize_block(self, state_hash):
        update = self.pending_updates.get(state_hash)
        if not update: return
        
        signatures = self.collected_signatures[state_hash]
        
        # Logic to commit to storage
        new_block = self.blockchain.create_block(
            update["state"], 
            update["miner"], 
            signatures, 
            update["group_id"]
        )
        
        # Broadcast block
        self.p2p.broadcast({"type": "BLOCK_ANNOUNCE", "block": new_block})
        del self.pending_updates[state_hash]
        del self.collected_signatures[state_hash]
        print(f"Block {new_block['block_number']} finalized and broadcasted.")

    def on_receive_block(self, msg):
        # Verify and apply block if higher than current
        pass

if __name__ == "__main__":
    node = LibreNode()
    if node.start():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            node.p2p.stop()
