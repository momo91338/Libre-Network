use serde::{Serialize, Deserialize};

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct User {
    pub address: [u8; 32],
    pub balance: u64,
    pub nonce: u64,
    pub account_age: u64,
    pub mining_age: u64,
    pub validity_age: u64,
}

impl User {
    pub fn new(address: [u8; 32]) -> Self {
        User {
            address,
            balance: 0,
            nonce: 0,
            account_age: 0,
            mining_age: 0,
            validity_age: 200_000_000,
        }
    }
}
