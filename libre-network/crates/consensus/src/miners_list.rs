use std::collections::HashSet;

pub type MinerId = [u8; 32];

pub struct MinersList {
    miners: HashSet<MinerId>,
}

impl MinersList {
    pub fn new() -> Self {
        Self {
            miners: HashSet::new(),
        }
    }

    pub fn add(&mut self, pk: &MinerId) {
        self.miners.insert(*pk);
    }

    pub fn remove(&mut self, pk: &MinerId) {
        self.miners.remove(pk);
    }

    pub fn contains(&self, pk: &MinerId) -> bool {
        self.miners.contains(pk)
    }

    pub fn select_active_miners(
        &self,
        seed: &[u8],
        count: usize,
    ) -> Vec<MinerId> {
        use sha2::{Digest, Sha256};

        let mut miners: Vec<MinerId> = self.miners.iter().cloned().collect();

        miners.sort_by_key(|pk| {
            let mut hasher = Sha256::new();
            hasher.update(seed);
            hasher.update(pk);
            hasher.finalize().to_vec()
        });

        miners.into_iter().take(count).collect()
    }
}
