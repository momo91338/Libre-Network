use ed25519_dalek::{Keypair, Signer};

use rand::rngs::OsRng;

pub struct Wallet {
    keypair: Keypair,
}

impl Wallet {
    pub fn new() -> Self {
        let mut csprng = OsRng {};
        let keypair = Keypair::generate(&mut csprng);

        Self { keypair }
    }

    pub fn public_key_bytes(&self) -> [u8; 32] {
        self.keypair.public.to_bytes()
    }

    pub fn sign(&self, data: &[u8]) -> Vec<u8> {
        self.keypair.sign(data).to_bytes().to_vec()
    }
}
