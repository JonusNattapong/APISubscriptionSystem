# AI Model File Synchronization Tool

A Rust-based tool for monitoring, encrypting, compressing, and synchronizing AI model files to cloud storage.

## Features

- **File Watching**: Monitors directories for file changes using the `notify` crate
- **Cloud Synchronization**: Uploads files to Google Drive or AWS S3
- **Security**: AES-256 encryption for all stored files
- **Compression**: Reduces file size before upload
- **Configurable**: Easy to configure via TOML configuration file

## Prerequisites

- Rust (latest stable)
- Google Drive API credentials or AWS S3 credentials
- AI model files to synchronize

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/APISubscriptionSystem.git
cd APISubscriptionSystem/rust-file-sync

# Build the project
cargo build --release
```

## Configuration

Edit the `config.toml` file to configure the tool:

```toml
# Base path for remote storage
remote_base_path = "ai-models"

# Google Drive configuration
[google_drive]
folder_id = "your-google-drive-folder-id"
credentials_file = "credentials.json"

# AWS S3 configuration
[s3]
bucket = "your-s3-bucket"
region = "us-east-1"
access_key = "your-aws-access-key"
secret_key = "your-aws-secret-key"

# Encryption configuration
[encryption]
key = "your-encryption-key-must-be-strong-and-secure"
```

## Usage

```bash
# Run with Google Drive as the cloud provider
cargo run -- --watch-path /path/to/ai/models --provider gdrive

# Run with AWS S3 as the cloud provider
cargo run -- --watch-path /path/to/ai/models --provider s3

# Use a custom configuration file
cargo run -- --watch-path /path/to/ai/models --config custom-config.toml
```

## How It Works

1. The tool watches the specified directory for file changes
2. When a file is created or modified, it:
   - Compresses the file using gzip
   - Encrypts the compressed file using AES-256
   - Uploads the encrypted file to the configured cloud provider
3. The file is now securely stored in the cloud and can be accessed by the Python API service

## Security

- All files are encrypted with AES-256 before being uploaded
- Encryption keys are never stored in the cloud
- Files are compressed to reduce storage costs and transfer times
