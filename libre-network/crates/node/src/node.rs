use tokio::sync::Mutex;
use std::sync::Arc;

use crate::tx_pool::TransactionPool;
use core::state::State;

/// تمثل عقدة في شبكة Libre Network.
/// تحتوي على الحالة العامة للسلسلة وحوض المعاملات (المعاملات المعلقة).
pub struct LibreNode {
    /// حالة السلسلة (البلوكشين).
    pub state: State,

    /// حوض المعاملات، مع إدارة تناسق عبر الـ Mutex ومرجع ذكي.
    pub tx_pool: Arc<Mutex<TransactionPool>>,
}

impl LibreNode {
    /// ينشئ عقدة جديدة مع حالة سلسلة ابتدائية وحوض معاملات فارغ.
    pub fn new() -> Self {
        let state = State::new();
        let tx_pool = Arc::new(Mutex::new(TransactionPool::new()));

        LibreNode {
            state,
            tx_pool,
        }
    }
}
