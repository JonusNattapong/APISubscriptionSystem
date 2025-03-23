use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce,
};
use anyhow::{Context, Result};
use rand::{rngs::OsRng, RngCore};
use std::fs::File;
use std::io::{Read, Write};
use std::path::Path;

/// AES-256 encryption implementation
pub struct AesEncryption {
    cipher: Aes256Gcm,
}

impl AesEncryption {
    pub fn new(key: &str) -> Result<Self> {
        // Convert key string to bytes
        let key_bytes = if key.len() == 64 {
            // Assuming key is a hex string
            hex::decode(key).context("Failed to decode hex key")?
        } else {
            // Use key directly and hash it to get 32 bytes
            use sha2::{Digest, Sha256};
            let mut hasher = Sha256::new();
            hasher.update(key.as_bytes());
            hasher.finalize().to_vec()
        };

        // Create AES-GCM cipher
        let cipher = Aes256Gcm::new_from_slice(&key_bytes)
            .context("Failed to create AES-GCM cipher")?;

        Ok(Self { cipher })
    }

    /// Encrypt a file
    pub fn encrypt_file(&self, input_path: &Path, output_path: &Path) -> Result<()> {
        // Read input file
        let mut input_file = File::open(input_path)
            .context("Failed to open input file for encryption")?;
        let mut plaintext = Vec::new();
        input_file
            .read_to_end(&mut plaintext)
            .context("Failed to read input file for encryption")?;

        // Generate random nonce (12 bytes for AES-GCM)
        let mut nonce_bytes = [0u8; 12];
        OsRng.fill_bytes(&mut nonce_bytes);
        let nonce = Nonce::from_slice(&nonce_bytes);

        // Encrypt data
        let ciphertext = self
            .cipher
            .encrypt(nonce, plaintext.as_ref())
            .context("Encryption failed")?;

        // Write nonce and ciphertext to output file
        let mut output_file = File::create(output_path)
            .context("Failed to create output file for encryption")?;
        output_file
            .write_all(&nonce_bytes)
            .context("Failed to write nonce to output file")?;
        output_file
            .write_all(&ciphertext)
            .context("Failed to write ciphertext to output file")?;

        Ok(())
    }

    /// Decrypt a file
    pub fn decrypt_file(&self, input_path: &Path, output_path: &Path) -> Result<()> {
        // Read input file
        let mut input_file = File::open(input_path)
            .context("Failed to open input file for decryption")?;
        
        // Read nonce (first 12 bytes)
        let mut nonce_bytes = [0u8; 12];
        input_file
            .read_exact(&mut nonce_bytes)
            .context("Failed to read nonce from input file")?;
        let nonce = Nonce::from_slice(&nonce_bytes);
        
        // Read ciphertext (rest of the file)
        let mut ciphertext = Vec::new();
        input_file
            .read_to_end(&mut ciphertext)
            .context("Failed to read ciphertext from input file")?;
        
        // Decrypt data
        let plaintext = self
            .cipher
            .decrypt(nonce, ciphertext.as_ref())
            .context("Decryption failed")?;
        
        // Write plaintext to output file
        let mut output_file = File::create(output_path)
            .context("Failed to create output file for decryption")?;
        output_file
            .write_all(&plaintext)
            .context("Failed to write plaintext to output file")?;
        
        Ok(())
    }
}
