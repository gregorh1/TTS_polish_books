#!/bin/bash

# Unified script for batch processing Polish text files
# Supports both text preprocessing and TTS generation
# 
# Usage: 
#   ./MAIN_MANU_SCRIPT.sh [book_directory] [--direct|-d]
# 
# Examples:
#   ./MAIN_MANU_SCRIPT.sh BOOKS/MY_BOOK
#   ./MAIN_MANU_SCRIPT.sh BOOKS/MY_BOOK --direct
#   ./MAIN_MANU_SCRIPT.sh    # Shows book selection menu

# Get book directory from command line argument
BOOK_DIR="$1"

show_menu() {
    echo ""
    echo "🎯 Polish Text & TTS Batch Processor"
    echo "======================================"
    echo ""
    echo "📁 Working with: $BOOK_DIR"
    echo ""
    echo "📚 Available operations:"
    echo "  1) 📝 Text Preprocessing - Clean all chapter files for TTS"
    echo "  2) 🎵 TTS Generation - Generate audio from cleaned files"
    echo "  3) 🚀 Full Pipeline - Run preprocessing + TTS generation"
    echo "  4) ❌ Exit"
    echo ""
}

# Check if required scripts exist
if [ ! -f "text_preprocessor.py" ]; then
    echo "❌ Error: text_preprocessor.py not found in the current directory"
    exit 1
fi

if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found in the current directory"
    exit 1
fi

# Function to select book from available books
select_book() {
    echo ""
    echo "📚 Available Books in BOOKS/ directory:"
    echo "======================================"
    
    # Check if BOOKS directory exists
    if [ ! -d "BOOKS" ]; then
        echo "❌ Error: BOOKS directory not found"
        exit 1
    fi
    
    # Get list of book directories
    books=()
    while IFS= read -r -d '' dir; do
        if [ -d "$dir/chapters" ]; then
            books+=("$(basename "$dir")")
        fi
    done < <(find BOOKS -maxdepth 1 -type d -print0 2>/dev/null | sort -z)
    
    if [ ${#books[@]} -eq 0 ]; then
        echo "❌ No valid book directories found in BOOKS/"
        echo "Each book should have a 'chapters' subdirectory"
        exit 1
    fi
    
    echo ""
    for i in "${!books[@]}"; do
        echo "  $((i+1))) ${books[i]}"
    done
    echo ""
    
    while true; do
        read -p "👉 Select a book (1-${#books[@]}): " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#books[@]}" ]; then
            BOOK_DIR="BOOKS/${books[$((choice-1))]}"
            echo "✅ Selected: $BOOK_DIR"
            break
        else
            echo "❌ Invalid choice. Please enter a number between 1 and ${#books[@]}"
        fi
    done
}

# If no book directory provided, show selection menu
if [ -z "$BOOK_DIR" ]; then
    select_book
fi

# Validate selected book directory
if [ ! -d "$BOOK_DIR" ]; then
    echo "❌ Error: Book directory '$BOOK_DIR' not found"
    echo "Available book directories:"
    ls -la BOOKS/ 2>/dev/null || echo "No BOOKS directory found"
    exit 1
fi

if [ ! -d "$BOOK_DIR/chapters" ]; then
    echo "❌ Error: Chapters directory '$BOOK_DIR/chapters' not found"
    exit 1
fi

# Function to discover all chapter files
discover_chapters() {
    chapters=()
    echo "🔍 Discovering chapter files in $BOOK_DIR/chapters/..."
    
    # Find all .txt files that are not already cleaned (don't end with _clean.txt)
    while IFS= read -r -d '' file; do
        # Skip files that end with _clean.txt
        if [[ ! "$file" =~ _clean\.txt$ ]]; then
            chapters+=("$file")
        fi
    done < <(find "$BOOK_DIR/chapters" -name "*.txt" -type f -print0 2>/dev/null | sort -z)
    
    if [ ${#chapters[@]} -eq 0 ]; then
        echo "❌ No chapter files found in $BOOK_DIR/chapters/"
        return 1
    fi
    
    echo "📚 Found ${#chapters[@]} chapter files:"
    for chapter in "${chapters[@]}"; do
        echo "   - $(basename "$chapter")"
    done
    echo ""
    
    return 0
}

process_text() {
    echo "🚀 Starting text preprocessing for all chapter files..."
    
    # Discover chapters first
    if ! discover_chapters; then
        return 0
    fi
    
    # Counter for processed files
    processed=0
    total=${#chapters[@]}
    
    echo "📚 Processing $total chapter files..."
    echo ""
    
    # Process each chapter file
    for chapter in "${chapters[@]}"; do
        if [ -f "$chapter" ]; then
            echo "📖 Processing: $(basename "$chapter")"
            
            # Run the text preprocessor
            python3 text_preprocessor.py "$chapter"
            
            if [ $? -eq 0 ]; then
                echo "✅ Successfully processed: $(basename "$chapter")"
                ((processed++))
            else
                echo "❌ Failed to process: $(basename "$chapter")"
            fi
            
            echo ""
        else
            echo "⚠️  File not found: $chapter"
            echo ""
        fi
    done
    
    echo "🎉 Text preprocessing complete!"
    echo "📊 Successfully processed: $processed/$total files"
    
    if [ $processed -eq $total ]; then
        echo "✨ All chapter files have been successfully preprocessed!"
    else
        echo "⚠️  Some files failed to process. Please check the output above."
    fi
    
    return $processed
}

generate_tts() {
    echo "🎵 Starting TTS generation for all cleaned chapter files..."
    
    # Counter for processed files
    processed=0
    failed=0
    
    # Build array of cleaned files that exist
    clean_files=()
    
    # Find all _clean.txt files in the chapters directory
    while IFS= read -r -d '' file; do
        if [[ "$file" =~ _clean\.txt$ ]]; then
            clean_files+=("$file")
        fi
    done < <(find "$BOOK_DIR/chapters" -name "*_clean.txt" -type f -print0 2>/dev/null | sort -z)
    
    total=${#clean_files[@]}
    
    if [ $total -eq 0 ]; then
        echo "❌ No cleaned files found! Please run text preprocessing first."
        return 0
    fi
    
    echo "🎧 Found $total cleaned files to process"
    echo ""
    
    # Process each cleaned file
    for clean_file in "${clean_files[@]}"; do
        echo "🎤 Generating TTS for: $(basename "$clean_file")"
        
        # Run the TTS processor
        python3 main.py "$clean_file"
        
        if [ $? -eq 0 ]; then
            echo "✅ Successfully generated TTS: $(basename "$clean_file")"
            ((processed++))
        else
            echo "❌ Failed to generate TTS: $(basename "$clean_file")"
            ((failed++))
        fi
        
        echo ""
    done
    
    echo "🎉 TTS generation complete!"
    echo "📊 Successfully processed: $processed/$total files"
    echo "📊 Failed: $failed/$total files"
    
    if [ $processed -eq $total ]; then
        echo "✨ All TTS files have been successfully generated!"
        echo "🎧 Check the 'results' directory for audio files"
    else
        echo "⚠️  Some TTS generation failed. Please check the output above."
    fi
    
    return $processed
}

# Full pipeline function (direct execution without menu)
full_pipeline_direct() {
    echo "🚀 FULL PIPELINE EXECUTION"
    echo "=================================================="
    echo "📁 Working with: $BOOK_DIR"
    echo ""
    
    # Step 1: Text preprocessing
    echo "🔄 Step 1/2: Text Preprocessing"
    echo "==============================="
    process_text
    processed_text=$?
    
    if [ $processed_text -gt 0 ]; then
        echo ""
        echo "🔄 Step 2/2: TTS Generation"
        echo "==========================="
        generate_tts
        processed_tts=$?
        
        echo ""
        echo "🎉 FULL PIPELINE COMPLETE!"
        echo "📊 Text files processed: $processed_text"
        echo "📊 TTS files generated: $processed_tts"
        
        if [ $processed_tts -gt 0 ]; then
            echo "✨ Pipeline executed successfully!"
            echo "🎧 Check the 'results' directory for audio files"
        else
            echo "⚠️  TTS generation had issues. Check the output above."
        fi
    else
        echo ""
        echo "❌ Text preprocessing failed. Pipeline stopped."
        echo "Please check the files and try again."
    fi
}

# Check if we should run direct pipeline (useful for command line usage)
if [ "$2" = "--direct" ] || [ "$2" = "-d" ]; then
    full_pipeline_direct
    exit 0
fi

# Main script loop
while true; do
    show_menu
    read -p "👉 Choose an option (1-4): " choice
    
    case $choice in
        1)
            echo ""
            process_text
            ;;
        2)
            echo ""
            generate_tts
            ;;
        3)
            echo ""
            full_pipeline_direct
            ;;
        4)
            echo ""
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo ""
            echo "❌ Invalid option. Please choose 1-4."
            ;;
    esac
    
    echo ""
    read -p "⏸️  Press Enter to continue..."
done
