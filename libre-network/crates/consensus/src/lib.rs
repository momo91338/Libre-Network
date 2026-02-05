pub mod miners_list;
pub mod nonce_manager;
pub mod update;

pub use miners_list::MinersList;
pub use nonce_manager::NonceManager;
pub struct Update {
    pub update_id: u64,
    pub miner: [u8; 32],
    pub timestamp: u64,
    pub nonce: u64,
    pub prev_hash: [u8; 32],
}

pub type ProofOfActivity = Update;



use async_trait::async_trait;

#[async_trait]
pub trait Consensus {
    async fn validate_update(&self, update: &Update, miners: &MinersList) -> bool;
    async fn sign_update(&self, update: &Update) -> Vec<u8>;
    async fn aggregate_signatures(signatures: &[Vec<u8>]) -> Vec<u8>;
}



#[async_trait]
impl Consensus for ProofOfActivity {
    async fn validate_update(&self, update: &Update, miners: &MinersList) -> bool {
        self.validate_update_signature(update, miners).await
    }

    async fn sign_update(&self, _update: &Update) -> Vec<u8> {
        vec![] // تطبيق توقيع حقيقي لاحقاً
    }

    async fn aggregate_signatures(_signatures: &[Vec<u8>]) -> Vec<u8> {
        vec![] // تطبيق دمج التواقيع لاحقاً
    }
}

impl ProofOfActivity {
    pub async fn validate_update_signature(&self, update: &Update, miners: &MinersList) -> bool {
        // تحقق مبسط: تأكد أن المعدنين هم من وقعوا (تحتاج تعويض بتوقيع حقيقي)
        true
    }
}
