use crate::validator::Validator;

pub struct AggregatedSignature {
    pub data: Vec<u8>,
}

pub fn aggregate_signatures(
    miner_sigs: Vec<(Validator, Vec<u8>)>,
) -> Result<AggregatedSignature, String> {
    // هنا نطبق طريقة تجميع التوقيعات التجريبية
    // (للتبسيط يمكن جمع التوقيعات في مصفوفة واحدة)

    if miner_sigs.is_empty() {
        return Err("No signatures to aggregate".to_string());
    }

    let mut combined = Vec::new();
    for (_validator, sig) in miner_sigs {
        combined.extend(sig);
    }

    Ok(AggregatedSignature { data: combined })
}
