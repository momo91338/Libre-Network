use serde::{Serialize, Deserialize};
use std::net::SocketAddr;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Peer {
    pub id: String,
    pub address: SocketAddr,
    pub last_seen: u64,
}
