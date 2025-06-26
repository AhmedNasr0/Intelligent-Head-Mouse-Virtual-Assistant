from transformers import WhisperProcessor, WhisperForConditionalGeneration
import os
from pathlib import Path

def download_model():
    # Create directory
    model_dir = Path(__file__).resolve().parent / "whisper-base"
    model_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Downloading Whisper model...")
    
    # Download and save model locally
    model_name = "openai/whisper-base"  # Using tiny model for faster loading
    print(f"[INFO] Downloading {model_name}...")
    
    try:
        # Download processor
        print("[INFO] Downloading processor...")
        processor = WhisperProcessor.from_pretrained(model_name)
        
        # Download model
        print("[INFO] Downloading model...")
        model = WhisperForConditionalGeneration.from_pretrained(model_name)
        
        # Save locally
        print("[INFO] Saving model locally...")
        processor.save_pretrained(model_dir)
        model.save_pretrained(model_dir)
        
        print(f"[INFO] Model saved successfully to {model_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download model: {str(e)}")
        return False

if __name__ == "__main__":
    download_model()