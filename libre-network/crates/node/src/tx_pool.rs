use core::transaction::Transaction;
use tokio::sync::Mutex;
use std::collections::VecDeque;
use std::sync::Arc;

pub struct TransactionPool {
    pub pool: Arc<Mutex<VecDeque<Transaction>>>,
}

impl TransactionPool {
    pub fn new() -> Self {
        Self {
            pool: Arc::new(Mutex::new(VecDeque::new())),
        }
    }

    pub async fn add_transaction(&self, tx: Transaction) {
        let mut pool = self.pool.lock().await;
        pool.push_back(tx);
    }

    pub async fn get_transactions(&self, max: usize) -> Vec<Transaction> {
        let mut pool = self.pool.lock().await;
        let mut txs = Vec::new();
        for _ in 0..max {
            if let Some(tx) = pool.pop_front() {
                txs.push(tx);
            } else {
                break;
            }
        }
        txs
    }
}
