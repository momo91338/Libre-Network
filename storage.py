import sqlite3
import json
import os
import threading

class Storage:
    def __init__(self, db_path="libre_data/libre_network.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.lock = threading.Lock()
        self.init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    address TEXT PRIMARY KEY,
                    balance REAL DEFAULT 0,
                    nonce INTEGER DEFAULT 0,
                    life INTEGER DEFAULT 20000000
                )
            ''')
            
            # Miner pool table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS miner_pool (
                    address TEXT PRIMARY KEY,
                    joined_at INTEGER
                )
            ''')
            
            # Groups table
            # miners is stored as a JSON string
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY,
                    miners TEXT,
                    created_at INTEGER
                )
            ''')
            
            # Blocks table
            # signatures is stored as a JSON string
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocks (
                    block_number INTEGER PRIMARY KEY,
                    prev_hash TEXT,
                    state_hash TEXT,
                    combined_hash TEXT,
                    group_id INTEGER,
                    miner TEXT,
                    timestamp INTEGER,
                    executed_tx_count INTEGER,
                    signatures TEXT
                )
            ''')
            
            # Peers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS peers (
                    node_id TEXT PRIMARY KEY,
                    ip TEXT,
                    port INTEGER,
                    last_seen INTEGER
                )
            ''')
            
            # Config table (generic key-value)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            # Wallet Session table (persistent login)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallet_session (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    private_key TEXT,
                    public_key TEXT,
                    address TEXT
                )
            ''')

            # Generated Keys table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    private_key TEXT,
                    public_key TEXT,
                    address TEXT,
                    created_at INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()

    # --- User Management ---
    def get_user(self, address):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE address = ?", (address,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {"address": row[0], "balance": row[1], "nonce": row[2], "life": row[3]}
            return None

    def upsert_user(self, address, balance, nonce, life):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (address, balance, nonce, life)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    balance=excluded.balance,
                    nonce=excluded.nonce,
                    life=excluded.life
            ''', (address, balance, nonce, life))
            conn.commit()
            conn.close()

    def get_all_users(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            conn.close()
            return {row[0]: {"address": row[0], "balance": row[1], "nonce": row[2], "life": row[3]} for row in rows}

    # --- Miner Pool ---
    def add_to_miner_pool(self, address, joined_at):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO miner_pool (address, joined_at) VALUES (?, ?)", (address, joined_at))
            conn.commit()
            conn.close()

    def get_miner_pool(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM miner_pool")
            rows = cursor.fetchall()
            conn.close()
            return {row[0]: row[1] for row in rows}

    def clear_miner_pool(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM miner_pool")
            conn.commit()
            conn.close()

    # --- Groups ---
    def save_group(self, group_id, miners_dict, created_at):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            miners_json = json.dumps(miners_dict)
            cursor.execute("INSERT OR REPLACE INTO groups (group_id, miners, created_at) VALUES (?, ?, ?)", 
                           (group_id, miners_json, created_at))
            conn.commit()
            conn.close()

    def get_group(self, group_id):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {"group_id": row[0], "miners": json.loads(row[1]), "created_at": row[2]}
            return None

    def get_latest_group(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groups ORDER BY group_id DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return {"group_id": row[0], "miners": json.loads(row[1]), "created_at": row[2]}
            return None

    # --- Blocks ---
    def save_block(self, block_data):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO blocks (
                    block_number, prev_hash, state_hash, combined_hash, 
                    group_id, miner, timestamp, executed_tx_count, signatures
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                block_data["block_number"],
                block_data["prev_hash"],
                block_data["state_hash"],
                block_data.get("combined_hash", ""),
                block_data["group_id"],
                block_data["miner"],
                block_data["timestamp"],
                block_data.get("executed_tx_count", 0),
                json.dumps(block_data.get("signatures", []))
            ))
            conn.commit()
            conn.close()

    def get_block(self, block_number):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blocks WHERE block_number = ?", (block_number,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "block_number": row[0], "prev_hash": row[1], "state_hash": row[2],
                    "combined_hash": row[3], "group_id": row[4], "miner": row[5],
                    "timestamp": row[6], "executed_tx_count": row[7], "signatures": json.loads(row[8])
                }
            return None

    def get_latest_block(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blocks ORDER BY block_number DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "block_number": row[0], "prev_hash": row[1], "state_hash": row[2],
                    "combined_hash": row[3], "group_id": row[4], "miner": row[5],
                    "timestamp": row[6], "executed_tx_count": row[7], "signatures": json.loads(row[8])
                }
            return None

    def get_block_count(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM blocks")
            count = cursor.fetchone()[0]
            conn.close()
            return count

    # --- Peers ---
    def save_peer(self, node_id, ip, port, last_seen):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO peers (node_id, ip, port, last_seen) VALUES (?, ?, ?, ?)", 
                           (node_id, ip, port, last_seen))
            conn.commit()
            conn.close()

    def get_all_peers(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM peers")
            rows = cursor.fetchall()
            conn.close()
            return {row[0]: {"ip": row[1], "port": row[2], "last_seen": row[3]} for row in rows}

    def remove_peer(self, node_id):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM peers WHERE node_id = ?", (node_id,))
            conn.commit()
            conn.close()

    # --- State Hash Helper ---
    def compute_state_hash(self):
        # We need a deterministic way to hash the state
        # State includes users, miner_pool, latest_group, latest_block (for chaining)
        # But per requirements: users, miner_pool, groups, blocks
        users = self.get_all_users()
        miner_pool = self.get_miner_pool()
        latest_group = self.get_latest_group()
        latest_block = self.get_latest_block()
        
        state = {
            "users": users,
            "miner_pool": miner_pool,
            "latest_group": latest_group,
            "latest_block_hash": latest_block["state_hash"] if latest_block else "0"*64
        }
        state_json = json.dumps(state, sort_keys=True)
        import hashlib
        return hashlib.sha256(state_json.encode()).hexdigest()

    # --- Wallet Session Management ---
    def save_wallet_session(self, private_key, public_key, address):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            # We only ever want one session
            cursor.execute("DELETE FROM wallet_session")
            cursor.execute('''
                INSERT INTO wallet_session (id, private_key, public_key, address)
                VALUES (1, ?, ?, ?)
            ''', (private_key, public_key, address))
            conn.commit()
            conn.close()

    def get_wallet_session(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT private_key, public_key, address FROM wallet_session WHERE id = 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return {"private_key": row[0], "public_key": row[1], "address": row[2]}
            return None

    def delete_wallet_session(self):
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM wallet_session")
            conn.commit()
            conn.close()

    # --- Generated Keys (Persistent in keys.json) ---
    def _get_keys_file_path(self):
        # We assume the directory exists since Storage manages libre_data
        return "libre_data/keys.json"

    def _load_keys_from_json(self):
        path = self._get_keys_file_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_keys_to_json(self, keys):
        path = self._get_keys_file_path()
        try:
            with open(path, "w") as f:
                json.dump(keys, f, indent=4)
        except Exception as e:
            print(f"Error saving keys.json: {e}")

    def save_generated_key(self, private_key, public_key, address):
        import time
        with self.lock:
            keys = self._load_keys_from_json()
            new_key = {
                "private_key": private_key,
                "public_key": public_key,
                "address": address,
                "created_at": int(time.time())
            }
            keys.insert(0, new_key) # Add to front
            self._save_keys_to_json(keys)

    def get_all_generated_keys(self):
        with self.lock:
            return self._load_keys_from_json()

    def delete_generated_key(self, address):
        with self.lock:
            keys = self._load_keys_from_json()
            updated_keys = [k for k in keys if k["address"] != address]
            if len(keys) != len(updated_keys):
                self._save_keys_to_json(updated_keys)
                return True
            return False
