"""
Social Media AI Service
Handles titles and platform descriptions generation using Gemini AI.
"""
import os
import json
from typing import List, Dict, Optional
from google import genai
from rich.console import Console

from src.shared.exceptions import GeminiAPIError, MissingAPIKeyError
from .prompts import TITLE_PROMPT_TEMPLATE, DESCRIPTION_PROMPT_TEMPLATE


class SocialMediaService:
    """
    Service for generating viral titles and platform descriptions.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        """
        Initialize social media service.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        
        if not self.api_key:
            raise MissingAPIKeyError("GEMINI_API_KEY")
        
        self.client = genai.Client(api_key=self.api_key)
        self.console = Console()
    
    def generate_titles(self, transcript_text: str, max_chars: int = 4000) -> List[str]:
        """
        Generate viral title suggestions.
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
            self.console.print(f"[bold red]❌ Error generating titles: {e}[/]")
            return []
    
    def generate_descriptions(
        self,
        transcript_text: str,
        video_title: str = "",
        max_chars: int = 4000
    ) -> Dict[str, str]:
        """
        Generate TikTok, Instagram and YouTube descriptions.
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
            self.console.print(f"[bold red]❌ Error generating descriptions: {e}[/]")
            return {"tiktok": "", "instagram": "", "youtube": ""}


# Helper functions for easy access
def generate_viral_titles(transcript_text: str) -> List[str]:
    service = SocialMediaService()
    return service.generate_titles(transcript_text)

def generate_video_descriptions(transcript_text: str, title: str = "") -> Dict[str, str]:
    service = SocialMediaService()
    return service.generate_descriptions(transcript_text, title)
