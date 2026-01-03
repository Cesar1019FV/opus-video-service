"""
Effects Service
Wrapper for video entry effects.
"""
from moviepy.editor import VideoClip
from .implementations import apply_effect_to_clip, EFFECTS


class EffectsService:
    """Service for applying video entry effects"""
    
    def apply_effect(self, clip: VideoClip, effect_type: str) -> VideoClip:
        """
        Apply an entry effect to a clip.
        
        Args:
            clip: Input video clip
            effect_type: Effect type ('1'=zoom, '2'=flash, '3'=slide)
            
        Returns:
            Clip with effect applied
        """
        return apply_effect_to_clip(clip, effect_type)
    
    @staticmethod
    def get_available_effects() -> dict:
        """Get available effects"""
        return EFFECTS
