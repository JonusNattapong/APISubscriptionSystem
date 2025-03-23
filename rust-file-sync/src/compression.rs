use anyhow::{Context, Result};
use flate2::{write::GzEncoder, Compression};
use std::fs::File;
use std::io::{Read, Write};
use std::path::Path;

/// Compress a file using gzip
pub fn compress_file(input_path: &Path, output_path: &Path) -> Result<()> {
    // Open input file
    let mut input_file = File::open(input_path)
        .context("Failed to open input file for compression")?;
    
    // Create output file with gzip encoder
    let output_file = File::create(output_path)
        .context("Failed to create output file for compression")?;
    let mut encoder = GzEncoder::new(output_file, Compression::best());
    
    // Read input file and write to encoder
    let mut buffer = Vec::new();
    input_file.read_to_end(&mut buffer)
        .context("Failed to read input file for compression")?;
    encoder.write_all(&buffer)
        .context("Failed to write compressed data")?;
    encoder.finish()
        .context("Failed to finish compression")?;
    
    log::info!("Compressed file: {:?} -> {:?}", input_path, output_path);
    Ok(())
}

/// Decompress a gzip file
pub fn decompress_file(input_path: &Path, output_path: &Path) -> Result<()> {
    // Open input file
    let input_file = File::open(input_path)
        .context("Failed to open input file for decompression")?;
    let mut decoder = flate2::read::GzDecoder::new(input_file);
    
    // Create output file
    let mut output_file = File::create(output_path)
        .context("Failed to create output file for decompression")?;
    
    // Read from decoder and write to output file
    let mut buffer = Vec::new();
    decoder.read_to_end(&mut buffer)
        .context("Failed to read compressed data")?;
    output_file.write_all(&buffer)
        .context("Failed to write decompressed data")?;
    
    log::info!("Decompressed file: {:?} -> {:?}", input_path, output_path);
    Ok(())
}
