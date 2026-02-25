import socket
import threading
import json
import time
import os
import random
import hashlib
from collections import deque

class P2PNode:
    def __init__(self, host, port, message_handler, node_id=None, storage=None):
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.node_id = node_id or f"Node_{int(time.time())}_{random.randint(1000, 9999)}"
        self.storage = storage # Storage instance for peer persistence
        self.peers = {} # Dictionary of node_id -> {"ip": ip, "port": port, "last_seen": ts}
        self.server_running = False
        
        # Message Deduplication Cache: (message_id) -> timestamp
        self.seen_messages = {}
        self.seen_messages_lock = threading.Lock()
        self.peers_lock = threading.Lock()
        
        # Load peers from storage if available
        self._load_peers()

    def _load_peers(self):
        if self.storage:
            try:
                stored_peers = self.storage.get_all_peers()
                with self.peers_lock:
                    for nid, info in stored_peers.items():
                        if nid != self.node_id:
                            self.peers[nid] = info
            except Exception as e:
                print(f"Failed to load peers from storage: {e}")

    def _save_peer(self, node_id, ip, port):
        if self.storage:
            try:
                self.storage.save_peer(node_id, ip, port, int(time.time()))
            except Exception as e:
                print(f"Failed to save peer to storage: {e}")

    def start_server(self):
        try:
            # Test if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, self.port))
            
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            # Start cleanup thread for seen messages
            self.cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
            self.cleanup_thread.start()
            
            return True, "Server started"
        except Exception as e:
            return False, str(e)

    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((self.host, self.port))
                s.listen(10)
                self.server_running = True
                print(f"P2P Server listening on {self.host}:{self.port} (ID: {self.node_id})")
                while self.server_running:
                    conn, addr = s.accept()
                    threading.Thread(target=self._handle_connection, args=(conn, addr), daemon=True).start()
            except Exception as e:
                if self.server_running:
                    print(f"Server error: {e}")

    def _handle_connection(self, conn, addr):
        with conn:
            try:
                # Use a buffer to handle potentially fragmented or multiple messages
                buffer = b""
                while self.server_running:
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    
                    buffer += chunk
                    
                    # Attempt to parse json objects from buffer
                    # This is a simplified approach for the demo. 
                    # In a production system, we'd use a more robust framing (e.g., length-prefixed).
                    try:
                        # Attempt to find the end of a JSON object
                        # This assumes messages are NOT pretty-printed or containing nested structures 
                        # that would confuse a simple partition. 
                        # Since we control the sender (json.dumps), we know it's a single line or standard block.
                        # However, JSON objects can have nested braces.
                        
                        # A better way for this simulation is to expect one full JSON per connection if not using a protocol.
                        # But P2P often reuses connections. 
                        # For now, we'll process the data we have as one message if it looks complete.
                        
                        decoded_data = buffer.decode()
                        # Very basic check: does it start with { and end with }?
                        # If multiple messages are sent in one stream, we'd need a real parser.
                        
                        # Let's try to parse the entire buffer. if it fails, maybe it's incomplete.
                        message_env = json.loads(decoded_data)
                        buffer = b"" # Reset buffer after successful parse
                        
                        msg_id = message_env.get("id")
                        if not msg_id: continue

                        # Deduplication check
                        with self.seen_messages_lock:
                            if msg_id in self.seen_messages:
                                continue
                            self.seen_messages[msg_id] = time.time()

                        # Update peer info from message
                        sender_id = message_env.get("sender")
                        sender_port = message_env.get("sender_port")
                        if sender_id and sender_id != self.node_id and sender_port:
                            self.add_peer(sender_id, addr[0], sender_port)

                        # Dispatch to handler
                        if self.message_handler:
                            self.message_handler(message_env, addr)
                        
                        # Relay message (Gossip)
                        if message_env.get("broadcast", False):
                            self.broadcast(message_env, exclude_node_id=sender_id)

                    except json.JSONDecodeError:
                        # Incomplete message, wait for more data
                        continue
                    except Exception as e:
                        # print(f"Error processing P2P message: {e}")
                        break

            except Exception as e:
                # print(f"Connection error from {addr}: {e}")
                pass

    def create_message(self, msg_type, payload, broadcast=False):
        timestamp = time.time()
        msg_body = {
            "type": msg_type,
            "sender": self.node_id,
            "sender_port": self.port,
            "payload": payload,
            "timestamp": timestamp,
            "broadcast": broadcast
        }
        # Compute message ID for deduplication
        msg_id = hashlib.sha256(json.dumps(msg_body, sort_keys=True).encode()).hexdigest()
        msg_body["id"] = msg_id
        return msg_body

    def send_message(self, ip, port, message_env):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((ip, port))
                s.sendall(json.dumps(message_env).encode())
            return True
        except Exception:
            return False

    def broadcast(self, message_env, exclude_node_id=None):
        # Ensure message is marked for broadcast for recipients to relay it
        message_env["broadcast"] = True
        
        # Add to seen messages if not already there (prevents self-relay loops)
        msg_id = message_env.get("id")
        if msg_id:
            with self.seen_messages_lock:
                if msg_id not in self.seen_messages:
                    self.seen_messages[msg_id] = time.time()

        with self.peers_lock:
            active_peers = list(self.peers.items())

        for nid, info in active_peers:
            if nid != exclude_node_id and nid != self.node_id:
                threading.Thread(target=self.send_message, args=(info["ip"], info["port"], message_env), daemon=True).start()

    def add_peer(self, node_id, ip, port):
        if node_id == self.node_id: return
        with self.peers_lock:
            self.peers[node_id] = {"ip": ip, "port": port, "last_seen": int(time.time())}
        self._save_peer(node_id, ip, port)

    def remove_peer(self, node_id):
        with self.peers_lock:
            if node_id in self.peers:
                del self.peers[node_id]
        if self.storage:
            self.storage.remove_peer(node_id)

    def announce_presence(self):
        msg = self.create_message("PRESENCE", {"node_id": self.node_id, "port": self.port}, broadcast=True)
        self.broadcast(msg)

    def _periodic_cleanup(self):
        while True:
            time.sleep(60)
            now = time.time()
            # Cleanup seen messages older than 10 minutes
            with self.seen_messages_lock:
                to_remove = [mid for mid, ts in self.seen_messages.items() if now - ts > 600]
                for mid in to_remove:
                    del self.seen_messages[mid]
            
            # Cleanup stale peers older than 5 minutes
            with self.peers_lock:
                to_remove_peers = [nid for nid, info in self.peers.items() if now - info.get("last_seen", 0) > 300]
                for nid in to_remove_peers:
                    # In a real system, we might ping before removing
                    # For now just remove
                    del self.peers[nid]
                    if self.storage:
                        self.storage.remove_peer(nid)

    def get_peer_list(self):
        with self.peers_lock:
            return [{"node_id": nid, "ip": info["ip"], "port": info["port"]} for nid, info in self.peers.items()]
