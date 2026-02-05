use std::collections::HashMap;

pub type MinerId = [u8; 32];

pub struct NonceManager {
    nonces: HashMap<MinerId, u64>,
}

impl NonceManager {
    pub fn new() -> Self {
        Self {
            nonces: HashMap::new(),
        }
    }

    pub fn get_nonce(&self, pk: &MinerId) -> u64 {
        *self.nonces.get(pk).unwrap_or(&0)
    }

    pub fn increment_nonce(&mut self, pk: &MinerId) {
        let counter = self.nonces.entry(*pk).or_insert(0);
        *counter += 1;
    }

    pub fn verify_nonce(&self, pk: &MinerId, nonce: u64) -> bool {
        nonce > self.get_nonce(pk)
    }
}
