"""
Simple TTS script for single text files.

This script demonstrates basic text-to-speech functionality using Coqui TTS
with voice cloning for Polish language processing.
"""

import os
from utils import chunk_text_intelligently, get_output_filename, cleanup_temp_files
# Heavy imports moved inside main() to avoid delay on --help
from config import Config

# Audio processing functions moved to utils.py

def main():
    """Main TTS processing function."""
    import sys
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="🎯 Polish TTS with Smart Chunking")
    parser.add_argument("input_file", nargs='?', help="Input text file to process")
    parser.add_argument("--test-chunks", action="store_true", 
                       help="Save chunks to file for review (no TTS processing)")
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # Check if input file was provided
    if not args.input_file:
        print("❌ Error: Input file is required")
        parser.print_help()
        return
    
    # If no path specified, assume text_sources directory
    input_file = args.input_file
    if not os.path.dirname(input_file):
        input_file = os.path.join("text_sources", input_file)
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    if args.test_chunks:
        print("🔍 TEST MODE: Saving chunks for review (no TTS processing)")
    else:
        print("🎵 TTS MODE: Generating audio with smart chunking")
    
    print(f"📖 Processing file: {input_file}")
    
    # Validate configuration
    Config.validate()
    Config.ensure_output_dir()
    # Read input text
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            text_content = file.read()
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found.")
        return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    # Preprocess text to avoid XTTS-v2 sentence ending hallucinations
    print("Original text preview:", text_content[:100] + "...")
    
    # Use intelligent chunking with cascading strategy (prioritize 224 chars for best quality)
    text_chunks = chunk_text_intelligently(text_content, max_size=224, hard_limit=400, punctuation_fix=True)
    
    print("Processed text preview:", text_content.replace('.', ';')[:100] + "...")
    print("Applied fix: periods (.) → semicolons (;) to avoid XTTS-v2 hallucinations")
    print(f"Split text into {len(text_chunks)} chunks for processing")
    for i, chunk in enumerate(text_chunks):
        chunk_len = len(chunk)
        status = "✅ SAFE" if chunk_len <= 224 else ("⚠️ WARN" if chunk_len <= 400 else "❌ TOO LONG")
        preview = chunk[:50] + "..." if len(chunk) > 50 else chunk
        print(f"Chunk {i+1}: {preview} ({chunk_len} chars - {status})")
    
    # If test mode, save chunks and exit
    if args.test_chunks:
        chunks_file = input_file.replace('.txt', '_chunks.txt')
        try:
            with open(chunks_file, 'w', encoding='utf-8') as f:
                f.write(f"=== PROCESSED CHUNKS FOR TTS ===\n")
                f.write(f"Source file: {input_file}\n")
                f.write(f"Total chunks: {len(text_chunks)}\n")
                f.write(f"Chunking strategy: max_size=224, hard_limit=400\n\n")
                
                for i, chunk in enumerate(text_chunks):
                    chunk_len = len(chunk)
                    status = "✅ SAFE" if chunk_len <= 224 else ("⚠️ WARN" if chunk_len <= 400 else "❌ TOO LONG")
                    f.write(f"=== CHUNK {i+1}/{len(text_chunks)} ({chunk_len} chars - {status}) ===\n")
                    f.write(f"{chunk}\n\n")
                
                f.write(f"=== END OF CHUNKS ===\n")
            
            print(f"\n💾 Test mode: Chunks saved to {chunks_file}")
            print(f"📊 Summary:")
            safe_count = sum(1 for chunk in text_chunks if len(chunk) <= 224)
            warn_count = sum(1 for chunk in text_chunks if 224 < len(chunk) <= 400)
            error_count = sum(1 for chunk in text_chunks if len(chunk) > 400)
            print(f"  • ✅ SAFE chunks (≤224 chars): {safe_count}")
            print(f"  • ⚠️ WARN chunks (225-400 chars): {warn_count}")
            print(f"  • ❌ ERROR chunks (>400 chars): {error_count}")
            return
            
        except Exception as e:
            print(f"❌ Error saving chunks file: {e}")
            return
    
    # Import heavy dependencies only when needed for actual TTS processing
    print("🔄 Loading TTS dependencies...")
    try:
        import torch
        from TTS.api import TTS
        from utils import concatenate_audio_files  # Add this import here too
    except ImportError as e:
        print(f"❌ Error importing TTS dependencies: {e}")
        print("💡 Make sure you have installed: pip install TTS torch")
        return
    
    # Setup device
    device = Config.get_device()
    print(f"Using device: {device}")
    
    # Initialize TTS model
    try:
        print("🔄 Initializing TTS model...")
        tts = TTS(Config.TTS_MODEL).to(device)
        print("✅ TTS model loaded successfully")
    except Exception as e:
        print(f"❌ Error initializing TTS model: {e}")
        return
    
    # Ensure output directory exists
    Config.ensure_output_dir()
    
    # Generate speech for each chunk
    chunk_files = []
    
    for i, chunk in enumerate(text_chunks):
        chunk_output_path = f"{Config.OUTPUT_DIR}/temp_chunk_{i+1:03d}.wav"
        
        try:
            print(f"Processing chunk {i+1}/{len(text_chunks)}... ({len(chunk)} chars)")
            tts.tts_to_file(
                text=chunk,
                file_path=chunk_output_path,
                speaker_wav=[Config.DEFAULT_SPEAKER_PATH],
                language=Config.LANGUAGE,
                split_sentences=Config.SPLIT_SENTENCES
            )
            chunk_files.append(chunk_output_path)
            print(f"✅ Chunk {i+1} generated: {chunk_output_path}")
            
        except Exception as e:
            print(f"❌ Error generating chunk {i+1}: {e}")
    
    # Concatenate all chunks into a single audio file
    if chunk_files:
        final_output_path = get_output_filename(input_file, Config.OUTPUT_DIR)
        
        print(f"\n🔗 Joining {len(chunk_files)} audio chunks...")
        try:
            concatenate_audio_files(chunk_files, final_output_path)
            print(f"✅ Final audio created: {final_output_path}")
            
            # Clean up temporary chunk files
            print(f"🧹 Cleaning up temporary files...")
            cleanup_temp_files(chunk_files)
            
        except Exception as e:
            print(f"❌ Error concatenating audio: {e}")
            print(f"Individual chunks are available in: {chunk_files}")
    
    print(f"\n📝 Applied XTTS-v2 optimizations:")
    print(f"  • Replaced periods (.) with semicolons (;) - prevents hallucinations")
    print(f"  • Disabled automatic sentence splitting")
    print(f"  • Smart chunking: complete sentences → natural pauses → words (if needed)")
    print(f"  • Split into {len(text_chunks)} chunks (max 400 chars, prefer ≤224 for best quality)")
    print(f"  • Concatenated chunks into single audio file")

if __name__ == "__main__":
    main()
