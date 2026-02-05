use crate::validator::Validator;
use crate::signature_aggregation::aggregate_signatures;
use crate::signature_aggregation::AggregatedSignature;

pub struct ProofOfActivity {}

impl ProofOfActivity {
    /// تحقق من صحة التحديث بناءً على توقيعات المعدنين
    pub fn validate_update(
        update_id: u64,
        miner_signatures: Vec<(Validator, Vec<u8>)>, // كل توقيع مع المعدن الذي وقعه
        required_signatures: usize,
    ) -> Result<AggregatedSignature, String> {
        if miner_signatures.len() < required_signatures {
            return Err("Not enough signatures".to_string());
        }
        // تحقق كل توقيع (يجب كتابة وظيفة تحقق منفصلة)
        // ثم دمج التوقيعات
        let agg_sig = aggregate_signatures(miner_signatures)?;
        Ok(agg_sig)
    }
}
