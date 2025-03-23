use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs::File;
use std::io::Read;
use std::path::Path;

/// Application configuration
#[derive(Debug, Serialize, Deserialize)]
pub struct AppConfig {
    /// Base path for remote storage
    pub remote_base_path: String,
    
    /// Google Drive configuration
    pub google_drive: GoogleDriveConfig,
    
    /// AWS S3 configuration
    pub s3: S3Config,
    
    /// Encryption configuration
    pub encryption: EncryptionConfig,
}

/// Google Drive configuration
#[derive(Debug, Serialize, Deserialize)]
pub struct GoogleDriveConfig {
    /// Google Drive folder ID
    pub folder_id: String,
    
    /// OAuth credentials file path
    pub credentials_file: String,
}

/// AWS S3 configuration
#[derive(Debug, Serialize, Deserialize)]
pub struct S3Config {
    /// S3 bucket name
    pub bucket: String,
    
    /// AWS region
    pub region: String,
    
    /// AWS access key
    pub access_key: String,
    
    /// AWS secret key
    pub secret_key: String,
}

/// Encryption configuration
#[derive(Debug, Serialize, Deserialize)]
pub struct EncryptionConfig {
    /// Encryption key (hex-encoded or raw)
    pub key: String,
}

/// Load configuration from a file
pub fn load_config(path: &Path) -> Result<AppConfig> {
    // Read configuration file
    let mut file = File::open(path)
        .context("Failed to open configuration file")?;
    let mut contents = String::new();
    file.read_to_string(&mut contents)
        .context("Failed to read configuration file")?;
    
    // Parse configuration
    let config: AppConfig = toml::from_str(&contents)
        .context("Failed to parse configuration file")?;
    
    Ok(config)
}

/// Create a default configuration
pub fn create_default_config() -> AppConfig {
    AppConfig {
        remote_base_path: "ai-models".to_string(),
        google_drive: GoogleDriveConfig {
            folder_id: "your-folder-id".to_string(),
            credentials_file: "credentials.json".to_string(),
        },
        s3: S3Config {
            bucket: "your-bucket".to_string(),
            region: "us-east-1".to_string(),
            access_key: "your-access-key".to_string(),
            secret_key: "your-secret-key".to_string(),
        },
        encryption: EncryptionConfig {
            key: "your-encryption-key".to_string(),
        },
    }
}

/// Save configuration to a file
pub fn save_config(config: &AppConfig, path: &Path) -> Result<()> {
    let contents = toml::to_string_pretty(config)
        .context("Failed to serialize configuration")?;
    
    std::fs::write(path, contents)
        .context("Failed to write configuration file")?;
    
    Ok(())
}
