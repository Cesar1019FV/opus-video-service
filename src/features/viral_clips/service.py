"""
Viral Clips Analysis Service
Uses Gemini AI to analyze transcripts and identify viral moments.
Extracted from src/core/analyzer.py
"""
import os
import json
from typing import List, Dict, Optional
from google import genai
from rich.console import Console
from rich.table import Table

from src.shared.models import ViralClip, TimeRange
from src.shared.exceptions import GeminiAPIError, MissingAPIKeyError, NoViralClipsFoundError, InvalidPromptResponseError
from .prompts import TITLE_PROMPT_TEMPLATE, DESCRIPTION_PROMPT_TEMPLATE, VIRAL_CLIPS_PROMPT_TEMPLATE


class ViralClipsService:
    """
    Service for analyzing videos using Gemini AI to find viral moments.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize viral clips service.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        
        if not self.api_key:
            raise MissingAPIKeyError("GEMINI_API_KEY")
        
        self.client = genai.Client(api_key=self.api_key)
        self.console = Console()
    
    def generate_viral_titles(self, transcript_text: str, max_chars: int = 2000) -> List[str]:
        """
        Generate viral title suggestions based on transcript.
        
        Args:
            transcript_text: Full or partial transcript
            max_chars: Maximum characters to send (to save tokens)
            
        Returns:
            List of viral title suggestions
        """
        truncated = transcript_text[:max_chars]
        prompt = TITLE_PROMPT_TEMPLATE.format(transcript_text=truncated)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            data = json.loads(response.text)
            return data.get("titles", [])
        except Exception as e:
            print(f"❌ Error generating titles: {e}")
            return []
    
    def generate_platform_descriptions(
        self,
        transcript_text: str,
        video_title: str = "",
        max_chars: int = 2000
    ) -> Dict[str, str]:
        """
        Generate platform-specific video descriptions.
        
        Args:
            transcript_text: Full or partial transcript
            video_title: Video title for context
            max_chars: Maximum characters to send
            
        Returns:
            Dictionary with keys: tiktok, instagram, youtube
        """
        truncated = transcript_text[:max_chars]
        prompt = DESCRIPTION_PROMPT_TEMPLATE.format(
            video_title=video_title or "Viral Short",
            transcript_text=truncated
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            data = json.loads(response.text)
            return {
                "tiktok": data.get("tiktok_description", ""),
                "instagram": data.get("instagram_description", ""),
                "youtube": data.get("youtube_description", "")
            }
        except Exception as e:
            print(f"❌ Error generating descriptions: {e}")
            return {"tiktok": "", "instagram": "", "youtube": ""}
    
    def find_viral_clips(
        self,
        transcript_dict: dict,
        video_duration: float,
        show_cost: bool = True
    ) -> List[ViralClip]:
        """
        Analyze transcript to find viral clip moments.
        
        Args:
            transcript_dict: Transcript dictionary with 'text' and 'segments' keys
            video_duration: Total video duration in seconds
            show_cost: Whether to display token usage and cost
            
        Returns:
            List of ViralClip objects
            
        Raises:
            GeminiAPIError: If API call fails
            NoViralClipsFoundError: If no clips are found
        """
        # Extract words from transcript
        words = []
        for segment in transcript_dict['segments']:
            for word in segment.get('words', []):
                words.append({
                    'w': word['word'],
                    's': word['start'],
                    'e': word['end']
                })
        
        prompt = VIRAL_CLIPS_PROMPT_TEMPLATE.format(
            video_duration=video_duration,
            transcript_text=json.dumps(transcript_dict['text']),
            words_json=json.dumps(words)
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Display cost if requested
            if show_cost:
                self._display_token_usage(response)
            
            # Clean markdown code blocks if present
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            result_json = json.loads(text)
            
            # Convert to ViralClip objects
            clips = []
            for short in result_json.get('shorts', []):
                clip = ViralClip(
                    time_range=TimeRange(
                        start=float(short['start']),
                        end=float(short['end'])
                    ),
                    title=short.get('video_title_for_youtube_short', ''),
                    descriptions={
                        'tiktok': short.get('video_description_for_tiktok', ''),
                        'instagram': short.get('video_description_for_instagram', ''),
                        'youtube': short.get('video_title_for_youtube_short', '')
                    }
                )
                clips.append(clip)
            
            if not clips:
                raise NoViralClipsFoundError("Gemini did not find any viral clips")
            
            return clips
            
        except json.JSONDecodeError as e:
            raise InvalidPromptResponseError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            if isinstance(e, (GeminiAPIError, NoViralClipsFoundError, InvalidPromptResponseError)):
                raise
            raise GeminiAPIError(f"Gemini API error: {e}")
    
    def _display_token_usage(self, response):
        """Display token usage and cost information"""
        try:
            usage = response.usage_metadata
            input_price_per_million = 0.10
            output_price_per_million = 0.40
            
            prompt_tokens = usage.prompt_token_count
            output_tokens = usage.candidates_token_count
            
            input_cost = (prompt_tokens / 1_000_000) * input_price_per_million
            output_cost = (output_tokens / 1_000_000) * output_price_per_million
            total_cost = input_cost + output_cost
            
            table = Table(
                title=f"💰 Token Usage ({self.model_name})",
                show_header=True,
                header_style="bold magenta"
            )
            table.add_column("Type", style="cyan")
            table.add_column("Count", justify="right")
            table.add_column("Cost ($)", justify="right", style="green")
            
            table.add_row("Input", str(prompt_tokens), f"${input_cost:.6f}")
            table.add_row("Output", str(output_tokens), f"${output_cost:.6f}")
            table.add_row("Total", "", f"${total_cost:.6f}", style="bold")
            
            self.console.print(table)
        except Exception:
            pass  # Silently ignore cost calculation errors


# Legacy functions for backward compatibility
def generate_viral_title(transcript_text: str) -> List[str]:
    """Legacy function for backward compatibility"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return []
    
    try:
        service = ViralClipsService(api_key=api_key)
        return service.generate_viral_titles(transcript_text)
    except Exception:
        return []


def generate_video_descriptions(transcript_text: str, video_title: str = "") -> Dict[str, str]:
    """Legacy function for backward compatibility"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"tiktok": "", "instagram": "", "youtube": ""}
    
    try:
        service = ViralClipsService(api_key=api_key)
        return service.generate_platform_descriptions(transcript_text, video_title)
    except Exception:
        return {"tiktok": "", "instagram": "", "youtube": ""}


def get_viral_clips(transcript_result: dict, video_duration: float) -> Optional[dict]:
    """
    Legacy function for backward compatibility.
    Returns dict format expected by existing code.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        return None
    
    try:
        service = ViralClipsService(api_key=api_key)
        clips = service.find_viral_clips(transcript_result, video_duration)
        
        # Convert back to old format
        shorts = []
        for clip in clips:
            shorts.append({
                'start': clip.start,
                'end': clip.end,
                'video_description_for_tiktok': clip.descriptions.get('tiktok', ''),
                'video_description_for_instagram': clip.descriptions.get('instagram', ''),
                'video_title_for_youtube_short': clip.title
            })
        
        return {'shorts': shorts}
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None
