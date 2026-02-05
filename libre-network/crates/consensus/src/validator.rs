use ed25519_dalek::{PublicKey, Signature, Verifier};

#[derive(Clone)]
pub struct Validator {
    pub public_key: PublicKey,
}

impl Validator {
    /// تحقق من توقيع رسالة معينة
    pub fn verify_signature(&self, message: &[u8], signature: &Signature) -> bool {
        self.public_key.verify(message, signature).is_ok()
    }
}
