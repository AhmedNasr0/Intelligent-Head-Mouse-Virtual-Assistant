from abc import ABC, abstractmethod
from typing import Optional, Tuple, Callable
import speech_recognition as sr
import pyttsx3

class VoiceService(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Convert text to speech"""
        pass
    
    @abstractmethod
    def listen(self, callback: Callable[[str], None], timeout: int = 5, phrase_time_limit: int = 10) -> bool:
        """Listen for speech and call the callback with the recognized text"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the voice service"""
        pass

    @abstractmethod
    def convert_arabic_to_english(self, text: str) -> str:
        """Convert Arabic text to English for email input"""
        pass

