use tokio::sync::Mutex;
use std::collections::HashMap;

pub struct MinerCoordination {
    pub signatures: Mutex<HashMap<u64, Vec<Vec<u8>>>>, // update_id => list of signatures
}

impl MinerCoordination {
    pub fn new() -> Self {
        Self {
            signatures: Mutex::new(HashMap::new()),
        }
    }

    pub async fn add_signature(&self, update_id: u64, signature: Vec<u8>) {
        let mut sigs = self.signatures.lock().await;
        sigs.entry(update_id).or_insert_with(Vec::new).push(signature);
    }

    pub async fn get_signatures(&self, update_id: u64) -> Option<Vec<Vec<u8>>> {
        let sigs = self.signatures.lock().await;
        sigs.get(&update_id).cloned()
    }
}
