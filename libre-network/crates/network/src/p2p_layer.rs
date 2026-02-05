use crate::peer::Peer;
use std::collections::HashMap;
use tokio::sync::RwLock;
use std::sync::Arc;

pub struct P2PLayer {
    pub peers: Arc<RwLock<HashMap<String, Peer>>>,
}

impl P2PLayer {
    pub fn new() -> Self {
        Self {
            peers: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn discover_peer(&self, peer: Peer) {
        let mut peers = self.peers.write().await;
        peers.insert(peer.id.clone(), peer);
    }

    pub async fn get_peers(&self) -> Vec<Peer> {
        let peers = self.peers.read().await;
        peers.values().cloned().collect()
    }

    // تابع لبث تحديث جديد إلى كل الأقران
    pub async fn broadcast_update(&self, update_data: Vec<u8>) {
        // تنفيذ عملية البث (مثال تجريبي فقط)
        let peers = self.peers.read().await;
        for (_id, peer) in peers.iter() {
            println!("Broadcasting update to peer: {}", peer.id);
            // هنا ترسل عبر الشبكة فعلياً
        }
    }
}
