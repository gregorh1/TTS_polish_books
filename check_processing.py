#!/usr/bin/env python3
"""
Script to check if all chapter files were processed correctly.
Compares original and cleaned files to detect missing content.

Usage: 
    python3 check_processing.py [book_directory]

Examples:
    python3 check_processing.py BOOKS/TOTALNA_WOJNA_INFORMACYJNA_XX_WIEKU_A_II_RP
    python3 check_processing.py BOOKS/PODSTAWY_NOWOCZESNEJ_N_P_O_C
    python3 check_processing.py    # Uses current directory
"""

import os
import sys
from pathlib import Path
import glob

def get_file_stats(file_path):
    """Get file statistics: size, lines, characters."""
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        size = os.path.getsize(file_path)
        lines = len(content.splitlines())
        chars = len(content)
        
        return {
            'size': size,
            'lines': lines,
            'chars': chars,
            'first_100': content[:100].replace('\n', ' '),
            'last_100': content[-100:].replace('\n', ' ') if len(content) > 100 else content.replace('\n', ' ')
        }
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def discover_chapter_files(book_dir):
    """Discover all original and cleaned chapter files in the given directory."""
    chapters_dir = os.path.join(book_dir, "chapters")
    
    if not os.path.exists(chapters_dir):
        print(f"❌ Error: Chapters directory '{chapters_dir}' not found")
        return []
    
    # Find all .txt files that are not _clean.txt
    original_files = []
    for file_path in glob.glob(os.path.join(chapters_dir, "*.txt")):
        if not file_path.endswith("_clean.txt"):
            original_files.append(file_path)
    
    # Sort files for consistent output
    original_files.sort()
    
    file_pairs = []
    for original_file in original_files:
        # Generate corresponding clean filename
        base_name = os.path.splitext(original_file)[0]
        cleaned_file = f"{base_name}_clean.txt"
        
        file_pairs.append({
            'original': original_file,
            'cleaned': cleaned_file,
            'name': os.path.basename(original_file)
        })
    
    return file_pairs

def compare_files(book_dir=None):
    """Compare all original and cleaned chapter files."""
    
    # Use provided directory or current directory
    if book_dir is None:
        book_dir = "."
    
    print("🔍 CHAPTER PROCESSING VERIFICATION")
    print("=" * 80)
    print(f"📁 Working with: {book_dir}")
    print()
    
    file_pairs = discover_chapter_files(book_dir)
    
    if not file_pairs:
        print("❌ No chapter files found!")
        return
    
    print(f"📚 Found {len(file_pairs)} chapter files to analyze")
    print()
    
    chapters = []
    for file_pair in file_pairs:
        original_stats = get_file_stats(file_pair['original'])
        cleaned_stats = get_file_stats(file_pair['cleaned'])
        
        if original_stats and cleaned_stats:
            # Calculate ratios
            size_ratio = cleaned_stats['size'] / original_stats['size']
            char_ratio = cleaned_stats['chars'] / original_stats['chars']
            line_ratio = cleaned_stats['lines'] / original_stats['lines']
            
            # Determine status
            if char_ratio < 0.7:  # Less than 70% of original characters
                status = "❌ SUSPICIOUS"
            elif char_ratio < 0.8:
                status = "⚠️  CHECK"
            else:
                status = "✅ OK"
            
            chapters.append({
                'name': file_pair['name'],
                'original': original_stats,
                'cleaned': cleaned_stats,
                'char_ratio': char_ratio,
                'size_ratio': size_ratio,
                'line_ratio': line_ratio,
                'status': status
            })
        elif not cleaned_stats:
            print(f"❌ {file_pair['name']}: No cleaned file found")
        elif not original_stats:
            print(f"❌ {file_pair['name']}: No original file found")
    
    # Print summary table
    print(f"{'File':<35} {'Original':<15} {'Cleaned':<15} {'Char%':<6} {'Size%':<6} {'Status'}")
    print("-" * 100)
    
    for ch in chapters:
        orig_info = f"{ch['original']['chars']:,}c/{ch['original']['lines']}l"
        clean_info = f"{ch['cleaned']['chars']:,}c/{ch['cleaned']['lines']}l"
        char_pct = f"{ch['char_ratio']*100:.1f}%"
        size_pct = f"{ch['size_ratio']*100:.1f}%"
        
        # Truncate filename if too long
        filename = ch['name']
        if len(filename) > 32:
            filename = filename[:29] + "..."
        
        print(f"{filename:<35} {orig_info:<15} {clean_info:<15} {char_pct:<6} {size_pct:<6} {ch['status']}")
    
    print()
    print("🔍 DETAILED CONTENT CHECK")
    print("=" * 80)
    
    # Check suspicious files in detail
    suspicious_files = [ch for ch in chapters if 'SUSPICIOUS' in ch['status'] or 'CHECK' in ch['status']]
    
    if suspicious_files:
        print("⚠️  Files that need inspection:")
        print()
        
        for ch in suspicious_files:
            print(f"📄 {ch['name']} - {ch['status']}")
            print(f"   Character loss: {(1-ch['char_ratio'])*100:.1f}%")
            print(f"   Original first 100 chars: {ch['original']['first_100']}...")
            print(f"   Cleaned first 100 chars:  {ch['cleaned']['first_100']}...")
            print(f"   Original last 100 chars:  ...{ch['original']['last_100']}")
            print(f"   Cleaned last 100 chars:   ...{ch['cleaned']['last_100']}")
            print()
    else:
        print("✅ All files appear to be processed correctly!")
    
    # Overall statistics
    total_original_chars = sum(ch['original']['chars'] for ch in chapters)
    total_cleaned_chars = sum(ch['cleaned']['chars'] for ch in chapters)
    overall_ratio = total_cleaned_chars / total_original_chars
    
    print(f"📊 OVERALL STATISTICS")
    print(f"   Total original characters: {total_original_chars:,}")
    print(f"   Total cleaned characters:  {total_cleaned_chars:,}")
    print(f"   Overall retention ratio:   {overall_ratio*100:.1f}%")
    
    if overall_ratio > 0.95:
        print("   ✅ Excellent retention - minimal content loss")
    elif overall_ratio > 0.85:
        print("   ✅ Good retention - acceptable cleaning")
    elif overall_ratio > 0.75:
        print("   ⚠️  Moderate retention - check suspicious files")
    else:
        print("   ❌ Poor retention - significant content loss detected")

if __name__ == "__main__":
    # Get book directory from command line argument
    book_dir = None
    if len(sys.argv) > 1:
        book_dir = sys.argv[1]
        
        # Validate the directory exists
        if not os.path.exists(book_dir):
            print(f"❌ Error: Directory '{book_dir}' not found")
            print("\nAvailable book directories:")
            if os.path.exists("BOOKS"):
                for item in os.listdir("BOOKS"):
                    if os.path.isdir(os.path.join("BOOKS", item)):
                        print(f"  - BOOKS/{item}")
            else:
                print("  No BOOKS directory found")
            sys.exit(1)
    
    compare_files(book_dir)