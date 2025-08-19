"""
Configuration management for Polish TTS Project
"""
import os
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading .env file
    pass

class Config:
    """Central configuration management for the TTS project."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    # "gpt-4.1-mini"
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Cost-effective model - upgrade to gpt-4.1-nano when available
    
    # TTS Configuration
    TTS_MODEL: str = os.getenv("TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
    DEVICE: str = os.getenv("DEVICE", "auto")  # auto, cpu, cuda
    LANGUAGE: str = os.getenv("LANGUAGE", "pl")
    
    # Audio Configuration
    DEFAULT_SPEAKER_PATH: str = os.getenv("SPEAKER_AUDIO_PATH", "./sound_sources/bartosz2.wav")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./results")
    SPLIT_SENTENCES: bool = os.getenv("SPLIT_SENTENCES", "false").lower() == "true"  # False by default to avoid hallucinations
    
    # Text Processing Configuration
    MAX_SENTENCE_LENGTH: int = int(os.getenv("MAX_SENTENCE_LENGTH", "220"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "4"))  # sentences per chunk for AI processing
    
    # Model Configuration
    BIELIK_MODEL: str = os.getenv("BIELIK_MODEL", "speakleash/Bielik-7B-Instruct-v0.1")
    
    # File Paths
    DEFAULT_JSON_PATH: str = os.getenv("DEFAULT_JSON_PATH", "./quaderni/json/quaderni_44.json")
    TEST_JSON_PATH: str = "./quaderni/json/test.json"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration settings."""
        if not cls.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not set. OpenAI features will not work.")
            return False
        return True
    
    @classmethod
    def get_device(cls) -> str:
        """Get the appropriate device for processing."""
        if cls.DEVICE == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return cls.DEVICE
    
    @classmethod
    def ensure_output_dir(cls) -> None:
        """Ensure output directory exists."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)