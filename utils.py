"""
Utility functions for Polish TTS Project
Shared functions for audio processing and text chunking
"""

import wave
import os


def concatenate_audio_files(input_files, output_file):
    """
    Concatenate multiple WAV files into a single WAV file.
    
    Args:
        input_files: List of input WAV file paths
        output_file: Output WAV file path
    """
    if not input_files:
        raise ValueError("No input files provided")
    
    # Read the first file to get audio parameters
    with wave.open(input_files[0], 'rb') as first_wave:
        params = first_wave.getparams()
        frames = first_wave.readframes(params.nframes)
    
    # Create output file with same parameters
    with wave.open(output_file, 'wb') as output_wave:
        output_wave.setparams(params)
        output_wave.writeframes(frames)
        
        # Append remaining files
        for input_file in input_files[1:]:
            with wave.open(input_file, 'rb') as input_wave:
                frames = input_wave.readframes(input_wave.getnframes())
                output_wave.writeframes(frames)


def chunk_text_intelligently(text, max_size=224, hard_limit=400, punctuation_fix=True):
    """
    Intelligently chunk text for XTTS-v2 processing with paragraph-aware strategy.
    
    Strategy:
    1. First split by paragraphs (respect natural speech boundaries)
    2. Within paragraphs: keep complete sentences under max_size
    3. If sentence > max_size, split by natural pauses (commas, colons, etc.)
    4. If still > hard_limit, reluctantly split by words (last resort)
    
    Args:
        text: Input text to chunk
        max_size: Quality threshold (224 chars - best audio quality)
        hard_limit: Absolute max size (400 chars - model breaks beyond this)
        punctuation_fix: Apply hallucination fix (periods → semicolons)
    
    Returns:
        List of text chunks
    """
    # Apply hallucination fix if requested
    if punctuation_fix:
        text = text.replace('.', ';')
    
    # First split by paragraphs (double newlines or single newlines that look like paragraph breaks)
    paragraphs = []
    current_para = ""
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:  # Empty line - paragraph break
            if current_para.strip():
                paragraphs.append(current_para.strip())
                current_para = ""
        else:
            if current_para:
                current_para += ' ' + line
            else:
                current_para = line
    
    # Add final paragraph
    if current_para.strip():
        paragraphs.append(current_para.strip())
    
    # Process each paragraph separately
    chunks = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If paragraph is small enough, keep it as one chunk
        if len(paragraph) <= max_size:
            chunks.append(paragraph)
            continue
        
        # Paragraph too large - apply sentence-level chunking within the paragraph
        para_chunks = _chunk_paragraph(paragraph, max_size, hard_limit)
        chunks.extend(para_chunks)
    
    return chunks


def _chunk_paragraph(paragraph, max_size, hard_limit):
    """Chunk a single paragraph using sentence-level strategy."""
    # Split by semicolons (our sentence markers)
    sentences = paragraph.split(';')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Handle oversized individual sentences
        if len(sentence) > max_size:
            # Save current chunk if exists
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Try splitting by natural pauses first
            natural_chunks = _split_by_natural_pauses(sentence, max_size)
            
            for chunk in natural_chunks:
                if len(chunk) <= max_size:
                    chunks.append(chunk.strip())
                elif len(chunk) <= hard_limit:
                    # Accept chunks up to hard_limit if natural pauses didn't help enough
                    chunks.append(chunk.strip())
                else:
                    # Last resort: split by words
                    word_chunks = _split_by_words(chunk, max_size)
                    chunks.extend(word_chunks)
            continue
        
        # Normal sentence grouping within paragraph
        if len(current_chunk + '; ' + sentence) > max_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += '; ' + sentence
            else:
                current_chunk = sentence
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def _split_by_natural_pauses(text, max_size):
    """Split text by natural pauses: commas, colons, em-dashes, etc."""
    import re
    
    # Natural pause markers (in order of preference)
    pause_patterns = [
        r'(,\s+)',      # Comma + space
        r'(:\s+)',      # Colon + space  
        r'(—\s+)',      # Em-dash + space
        r'(-\s+)',      # Hyphen + space
        r'(\s+i\s+)',   # " i " (Polish "and")
        r'(\s+ale\s+)', # " ale " (Polish "but")
        r'(\s+oraz\s+)',# " oraz " (Polish "and")
    ]
    
    for pattern in pause_patterns:
        segments = re.split(pattern, text)
        if len(segments) > 1:  # Found natural breaks
            chunks = []
            current = ""
            
            for segment in segments:
                if len(current + segment) <= max_size:
                    current += segment
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    current = segment
            
            if current.strip():
                chunks.append(current.strip())
            
            # Check if splitting helped
            if all(len(chunk) <= max_size for chunk in chunks):
                return chunks
    
    # No natural breaks found or didn't help
    return [text]


def _split_by_words(text, max_size):
    """Last resort: split by words (aiming for max_size for better quality)."""
    words = text.split()
    chunks = []
    current_chunk = ""
    
    for word in words:
        if len(current_chunk + ' ' + word) > max_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = word
        else:
            if current_chunk:
                current_chunk += ' ' + word
            else:
                current_chunk = word
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def cleanup_temp_files(file_list):
    """
    Clean up temporary files safely.
    
    Args:
        file_list: List of file paths to remove
    """
    for file_path in file_list:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not remove {file_path}: {e}")


def get_output_filename(input_file, output_dir="./results"):
    """
    Generate output filename based on input filename.
    
    Args:
        input_file: Path to input text file
        output_dir: Output directory
    
    Returns:
        Full path to output WAV file
    """
    input_basename = os.path.splitext(os.path.basename(input_file))[0]
    return f"{output_dir}/{input_basename}.wav"