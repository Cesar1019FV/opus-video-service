"""
Prompt Templates for Social Media AI Analysis
Separated from viral_clips to follow Feature Design architecture.
"""

TITLE_PROMPT_TEMPLATE = """
You are a senior short-form video editor for TikTok, IG Reels, and YouTube Shorts.
Read the transcript snippet below and generate 5 VIRAL titles/hooks (max 100 chars each) oriented to get maximum views.

INSTRUCTIONS:
- Focus on high Click-Through Rate (CTR).
- Use curiosity gaps, strong promises, or controversial questions.
- Style: Punchy, direct, and engaging.
- Output ONLY valid JSON.

TRANSCRIPT:
{transcript_text}

OUTPUT FORMAT:
{{
  "titles": [
    "Viral Title 1",
    "Viral Title 2",
    "..."
  ]
}}
"""

DESCRIPTION_PROMPT_TEMPLATE = """
You are a senior short-form video editor creating platform-specific descriptions for TikTok, Instagram Reels, and YouTube Shorts.

VIDEO CONTEXT:
Title: {video_title}
Transcript: {transcript_text}

INSTRUCTIONS:
- Create descriptions optimized for each platform to maximize views and engagement.
- TikTok: Casual, punchy, with trending hashtags and strong CTA.
- Instagram: Slightly more polished, emoji-friendly, aspirational tone.
- YouTube: SEO-optimized with keywords, clear value proposition.
- ALWAYS include a CTA (Call-To-Action) like "Follow for more", "Comment X and I'll send you...", etc.
- Keep descriptions concise but engaging (100-150 chars for TikTok/IG, 200 chars max for YouTube).
- Output ONLY valid JSON.

OUTPUT FORMAT:
{{
  "tiktok_description": "TikTok caption here with #hashtags and CTA",
  "instagram_description": "Instagram caption here with emojis 🔥 and CTA",
  "youtube_description": "YouTube description with SEO keywords and CTA"
}}
"""
