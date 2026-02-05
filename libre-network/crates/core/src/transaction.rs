use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum TransactionType {
    Transfer { to: [u8; 32], amount: u64 },
    MiningAgeTopUp { amount: u64 },
    AccountCreation,
    OwnershipTransfer { new_public_key: [u8; 32] },
    MinerPoolEntry,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Transaction {
    pub from: [u8; 32],
    pub tx_type: TransactionType,
    pub fee: u64,
    pub nonce: u64,
    pub signature: Vec<u8>,
}
