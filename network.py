import socket
import threading
import json
import time
import uuid

class P2PNode:
    def __init__(self, host, port, node_id, message_handler):
        self.host = host
        self.port = port
        self.node_id = node_id
        self.message_handler = message_handler
        self.peers = {} # node_id -> {"ip": ..., "port": ..., "conn": ..., "last_seen": ...}
        self.peer_lock = threading.Lock()
        self.server_running = False
        self.socket = None

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
            self.server_running = True
            
            self.listener_thread = threading.Thread(target=self._listen, daemon=True)
            self.listener_thread.start()
            
            self.cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
            self.cleanup_thread.start()
            
            print(f"P2P Node started on {self.host}:{self.port} with ID {self.node_id}")
            return True, "Success"
        except Exception as e:
            return False, str(e)

    def stop(self):
        self.server_running = False
        if self.socket:
            self.socket.close()

    def _listen(self):
        while self.server_running:
            try:
                conn, addr = self.socket.accept()
                threading.Thread(target=self._handle_inbound_connection, args=(conn, addr), daemon=True).start()
            except Exception as e:
                if self.server_running:
                    print(f"Listen error: {e}")

    def _handle_inbound_connection(self, conn, addr):
        with conn:
            try:
                data = b""
                while True:
                    chunk = conn.recv(65536) # Large buffer
                    if not chunk: break
                    data += chunk
                
                if data:
                    message = json.loads(data.decode())
                    self.message_handler(message, addr)
            except Exception as e:
                pass # Silently handle connection drops

    def connect_to_peer(self, ip, port):
        """Attempts to connect to a peer and sends a HELLO message."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((ip, port))
                hello_msg = {
                    "type": "HELLO",
                    "node_id": self.node_id,
                    "port": self.port,
                    "timestamp": int(time.time())
                }
                s.sendall(json.dumps(hello_msg).encode())
            return True
        except:
            return False

    def send_to_peer(self, ip, port, message):
        """Sends a message to a specific IP and port."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((ip, port))
                s.sendall(json.dumps(message).encode())
            return True
        except:
            return False

    def broadcast(self, message):
        """Broadcasts a message to all known active peers."""
        with self.peer_lock:
            active_peers = list(self.peers.values())
        
        for peer in active_peers:
            threading.Thread(target=self.send_to_peer, args=(peer["ip"], peer["port"], message), daemon=True).start()

    def add_peer(self, node_id, ip, port):
        if node_id == self.node_id: return
        with self.peer_lock:
            self.peers[node_id] = {
                "ip": ip,
                "port": port,
                "last_seen": int(time.time())
            }

    def _periodic_cleanup(self):
        """Removes peers that haven't been seen for a while."""
        while self.server_running:
            time.sleep(30)
            now = int(time.time())
            with self.peer_lock:
                to_remove = [nid for nid, p in self.peers.items() if now - p["last_seen"] > 120]
                for nid in to_remove:
                    del self.peers[nid]
            
            # Also send periodic PING to all peers
            self.broadcast({"type": "PING", "node_id": self.node_id})

    def get_peer_count(self):
        with self.peer_lock:
            return len(self.peers)

    def get_peer_list(self):
        with self.peer_lock:
            return [{"node_id": nid, "ip": p["ip"], "port": p["port"]} for nid, p in self.peers.items()]
