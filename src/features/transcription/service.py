"""
Transcription Service
Wraps Faster-Whisper for video transcription.
Extracted from src/core/transcriber.py
"""
from typing import Optional
from pathlib import Path
from faster_whisper import WhisperModel

from src.shared.models import Transcript, TranscriptSegment, Word
from src.shared.exceptions import TranscriptionError, WhisperModelError, NoAudioError


class TranscriptionService:
    """
    Service for transcribing video audio using Faster-Whisper.
    """
    
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Initialize transcription service.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Device to use ('cpu' or 'cuda')
            compute_type: Compute type for quantization
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None
    
    def _load_model(self) -> WhisperModel:
        """Lazy load the Whisper model"""
        if self._model is None:
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
            except Exception as e:
                raise WhisperModelError(f"Failed to load Whisper model: {e}")
        return self._model
    
    def transcribe(self, video_path: str | Path, word_timestamps: bool = True, verbose: bool = False) -> Transcript:
        """
        Transcribe a video file.
        
        Args:
            video_path: Path to the video file
            word_timestamps: Whether to include word-level timestamps
            verbose: Whether to print progress segments
            
        Returns:
            Transcript object with segments and words
            
        Raises:
            TranscriptionError: If transcription fails
            WhisperModelError: If model fails to load
        """
        video_path = str(video_path)
        
        try:
            model = self._load_model()
            
            # Transcribe
            # Note: verbose=True in model.transcribe prints to stdout by default in faster-whisper, 
            # but we can also do custom printing if we iterate.
            segments, info = model.transcribe(video_path, word_timestamps=word_timestamps)
            
            if verbose:
                print(f"Detected language: {info.language} with probability {info.language_probability:.2f}")
            
            # Convert to our domain models
            transcript_segments = []
            full_text = ""
            
            for segment in segments:
                # Log progress if verbose
                if verbose:
                    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

                words = []
                if segment.words:
                    for word in segment.words:
                        words.append(Word(
                            text=word.word,
                            start=word.start,
                            end=word.end,
                            probability=word.probability
                        ))
                
                seg = TranscriptSegment(
                    text=segment.text,
                    start=segment.start,
                    end=segment.end,
                    words=words
                )
                transcript_segments.append(seg)
                full_text += segment.text + " "
            
            return Transcript(
                text=full_text.strip(),
                segments=transcript_segments,
                language=info.language
            )
            
        except Exception as e:
            if isinstance(e, (TranscriptionError, WhisperModelError)):
                raise
            raise TranscriptionError(f"Transcription failed: {e}")
    
    def transcribe_to_dict(self, video_path: str | Path, word_timestamps: bool = True, verbose: bool = False) -> dict:
        """
        Transcribe and return as dictionary for backward compatibility.
        
        Args:
            video_path: Path to the video file
            word_timestamps: Whether to include word-level timestamps
            verbose: Whether to print progress logs
            
        Returns:
            Dictionary with transcript data
        """
        transcript = self.transcribe(video_path, word_timestamps, verbose=verbose)
        return transcript.to_dict()


# Legacy function for backward compatibility
def transcribe_video(
    video_path: str,
    model_size: str = "base",
    device: str = "cpu",
    compute_type: str = "int8",
    verbose: bool = False
) -> dict:
    """
    Legacy function for backward compatibility with existing code.
    Transcribes a video using Faster-Whisper.
    
    Returns a dictionary with full text, segments, and language info.
    """
    service = TranscriptionService(model_size, device, compute_type)
    return service.transcribe_to_dict(video_path, verbose=verbose)
