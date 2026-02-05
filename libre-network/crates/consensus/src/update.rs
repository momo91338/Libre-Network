use sha2::{Digest, Sha256};

pub struct Update {
    pub update_id: u64,
    pub miner: [u8; 32],
    pub timestamp: u64,
    pub nonce: u64,
    pub prev_hash: [u8; 32],
}

impl Update {
    pub fn hash(&self) -> [u8; 32] {
        let mut hasher = Sha256::new();
        hasher.update(&self.update_id.to_le_bytes());
        hasher.update(&self.miner);
        hasher.update(&self.timestamp.to_le_bytes());
        hasher.update(&self.nonce.to_le_bytes());
        hasher.update(&self.prev_hash);
        hasher.finalize().into()
    }
}
