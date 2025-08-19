# Polish TTS (Text-to-Speech) Project

Advanced text processing and voice cloning system for high-quality Polish speech synthesis using Coqui TTS (XTTS_v2).

## Features

- **XTTS-v2 Hallucination Fix**: Eliminates sentence-ending artifacts using semicolon replacement
- **Smart Chunking**: Handles unlimited text length with 220-character chunking for Polish
- **Auto-Concatenation**: Seamlessly joins audio chunks into single output files
- **Voice Cloning**: Custom voice characteristics using Coqui TTS
- **AI-Powered Corrections**: OpenAI GPT integration for text preprocessing
- **Batch Processing**: Automated processing of multiple text files
- **Polish Optimization**: Specialized handling of Polish text patterns and abbreviations

## Project Structure

```
TTS/
├── MAIN_MANU_SCRIPT.sh                 # Main batch processing script with interactive menu
├── main.py                             # Simple TTS script with hallucination fix
├── text_preprocessor.py                # Text cleaning and preprocessing
├── utils.py                            # Shared utility functions
├── config.py                           # Configuration management
├── BOOKS/                              # Book collections
│   └── [BOOK_NAME]/                   # Individual book directories
│       └── chapters/                   # Chapter files (user fills manually)
│           ├── chapter1.txt           # Original text files
│           └── chapter1_clean.txt     # Processed text files
├── sound_sources/                      # Voice samples for cloning
├── results/                            # Generated audio files
└── requirements.txt                    # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended for faster processing)
- FFmpeg (for audio processing)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TTS
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Note**: If you encounter compatibility issues, install these specific versions:
   ```bash
   pip install torch==2.1.0 torchaudio==2.1.0 transformers==4.33.0
   ```



4. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DEVICE=auto  # auto, cpu, cuda
   OUTPUT_DIR=./results
   SPEAKER_AUDIO_PATH=./sound_sources/bartosz2.wav
   LANGUAGE=pl
   ```

## Usage

### Main Batch Processing Script

The **MAIN_MANU_SCRIPT.sh** provides an interactive menu for complete book processing:

```bash
./MAIN_MANU_SCRIPT.sh [book_directory] [--direct|-d]
```

**Examples:**
```bash
# Interactive book selection menu
./MAIN_MANU_SCRIPT.sh

# Process specific book with menu
./MAIN_MANU_SCRIPT.sh BOOKS/MY_BOOK

# Direct processing (no menu)
./MAIN_MANU_SCRIPT.sh BOOKS/MY_BOOK --direct
```

**Menu Options:**
1. **Text Preprocessing**: Clean all chapter files for TTS
2. **TTS Generation**: Generate audio from cleaned files  
3. **Full Pipeline**: Run preprocessing + TTS generation automatically
4. **Exit**: Close the script

**Features:**
- **Book Selection**: If no book is specified, shows interactive menu of available books in BOOKS/ folder
- **Automatic Discovery**: Only shows books that have a valid `chapters/` directory
- **Direct Mode**: Use `--direct` flag to skip all menus and run full pipeline

### Text Preparation

**For Batch Processing:**
1. Create a book directory: `BOOKS/[BOOK_NAME]/`
2. Create a chapters subdirectory: `BOOKS/[BOOK_NAME]/chapters/`
3. Place your `.txt` files in the chapters directory
4. Run the script to process all files at once

### Manual Processing

**Single Text File:**
```bash
python main.py path/to/text_file.txt
```

**Text Preprocessing Only:**
```bash
python text_preprocessor.py path/to/text_file.txt
```

## Configuration

### Environment Setup
Configure the system via `.env` file:
- **AI Models**: OpenAI GPT for text preprocessing
- **Voice Settings**: Choose speaker from `sound_sources/`
- **Output Settings**: Customize result directory and audio quality

### Text Processing
- **Abbreviation Expansion**: Polish abbreviations (św. → święty, r. → roku)
- **Number Conversion**: Digits to Polish words
- **Sentence Optimization**: Splits long sentences for better TTS quality



## Useful Commands

### Audio Format Conversion
```bash
# Convert WAV to 64k MP3
for file in *.wav; do ffmpeg -i "$file" -b:a 64k "${file%.wav}.mp3"; done

# Convert MP3 to WAV
ffmpeg -i input.mp3 output.wav

# Truncate audio
ffmpeg -i input.wav -t 00:01:25 -c copy output.wav
```



## Contributing

1. Follow Python coding standards
2. Test changes with sample data  
3. Update documentation for new features
4. Ensure API keys are not committed to version control

## References

- [Coqui TTS Documentation](https://docs.coqui.ai/en/latest/models/xtts.html)
- OpenAI API for text processing
- Hugging Face Transformers for local AI models

## License

This project is for educational and research purposes. Please respect the source material and follow appropriate usage guidelines for AI services and voice cloning technology.
