use serde::{Serialize, Deserialize};
use crate::transaction::Transaction;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Update {
    pub update_id: u64,
    pub miner_list_id: u64,
    pub nonce: u64,
    pub transactions: Vec<Transaction>,
    pub previous_hash: [u8; 32],
    pub update_hash: [u8; 32],
    pub aggregated_signature: Vec<u8>,
}
