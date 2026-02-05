use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Miner {
    pub address: [u8; 32],
    pub public_key: [u8; 32],
    pub mining_age: u64,
}
