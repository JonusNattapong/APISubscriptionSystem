use anyhow::{Context, Result};
use clap::Parser;
use log::{error, info};
use notify::{Config, Event, RecommendedWatcher, RecursiveMode, Watcher};
use std::path::{Path, PathBuf};
use std::sync::mpsc::{channel, Receiver};
use std::time::Duration;

mod cloud;
mod encryption;
mod compression;
mod config;

use cloud::{CloudProvider, GoogleDriveProvider, S3Provider};
use encryption::AesEncryption;
use compression::compress_file;
use config::AppConfig;

#[derive(Parser, Debug)]
#[clap(author, version, about)]
struct Args {
    /// Path to watch for changes
    #[clap(short, long)]
    watch_path: PathBuf,

    /// Cloud provider to use (s3 or gdrive)
    #[clap(short, long, default_value = "gdrive")]
    provider: String,

    /// Configuration file path
    #[clap(short, long, default_value = "config.toml")]
    config: PathBuf,
}

fn main() -> Result<()> {
    // Initialize logger
    env_logger::init();
    info!("Starting AI Model File Synchronization Tool");

    // Load environment variables
    dotenv::dotenv().ok();

    // Parse command line arguments
    let args = Args::parse();
    
    // Load configuration
    let config = config::load_config(&args.config)
        .context("Failed to load configuration")?;
    
    // Create cloud provider
    let provider: Box<dyn CloudProvider> = match args.provider.as_str() {
        "s3" => Box::new(S3Provider::new(&config.s3)?),
        "gdrive" => Box::new(GoogleDriveProvider::new(&config.google_drive)?),
        _ => anyhow::bail!("Unsupported cloud provider: {}", args.provider),
    };
    
    // Create encryption service
    let encryption = AesEncryption::new(&config.encryption.key)?;
    
    // Start file watcher
    let (tx, rx) = channel();
    let mut watcher = RecommendedWatcher::new(
        move |res| {
            if let Ok(event) = res {
                tx.send(event).unwrap_or_else(|e| error!("Error sending event: {}", e));
            }
        },
        Config::default(),
    )?;

    // Watch the directory recursively
    watcher.watch(args.watch_path.as_path(), RecursiveMode::Recursive)?;
    info!("Watching directory: {:?}", args.watch_path);

    // Process events
    handle_events(rx, &provider, &encryption, &config)?;

    Ok(())
}

fn handle_events(
    rx: Receiver<Event>,
    provider: &Box<dyn CloudProvider>,
    encryption: &AesEncryption,
    config: &AppConfig,
) -> Result<()> {
    for event in rx {
        match event.kind {
            notify::EventKind::Create(_) | notify::EventKind::Modify(_) => {
                for path in event.paths {
                    if path.is_file() {
                        info!("File changed: {:?}", path);
                        
                        // Process and upload the file
                        match process_and_upload_file(&path, provider, encryption, config) {
                            Ok(_) => info!("Successfully processed and uploaded: {:?}", path),
                            Err(e) => error!("Failed to process file {:?}: {}", path, e),
                        }
                    }
                }
            }
            notify::EventKind::Remove(_) => {
                for path in event.paths {
                    info!("File removed: {:?}", path);
                    // Handle file deletion if needed
                }
            }
            _ => {}
        }
    }
    Ok(())
}

fn process_and_upload_file(
    path: &Path,
    provider: &Box<dyn CloudProvider>,
    encryption: &AesEncryption,
    config: &AppConfig,
) -> Result<()> {
    // Create a temporary file for processing
    let temp_dir = std::env::temp_dir();
    let file_name = path.file_name().context("Invalid file name")?;
    let temp_path = temp_dir.join(file_name);
    
    // Compress the file
    let compressed_path = temp_dir.join(format!("{}.gz", file_name.to_string_lossy()));
    compress_file(path, &compressed_path)?;
    
    // Encrypt the compressed file
    let encrypted_path = temp_dir.join(format!("{}.enc", file_name.to_string_lossy()));
    encryption.encrypt_file(&compressed_path, &encrypted_path)?;
    
    // Upload to cloud
    let remote_path = format!("{}/{}", config.remote_base_path, file_name.to_string_lossy());
    provider.upload_file(&encrypted_path, &remote_path)?;
    
    // Clean up temporary files
    std::fs::remove_file(&compressed_path)?;
    std::fs::remove_file(&encrypted_path)?;
    
    Ok(())
}
