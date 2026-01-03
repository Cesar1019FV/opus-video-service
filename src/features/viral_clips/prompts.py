"""
Prompt Templates for Gemini AI Analysis
Extracted from src/core/analyzer.py
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

VIRAL_CLIPS_PROMPT_TEMPLATE = """
You are a senior short-form video editor. Read the ENTIRE transcript and word-level timestamps to choose the 3–15 MOST VIRAL moments for TikTok/IG Reels/YouTube Shorts. Each clip must be between 15 and 60 seconds long.

⚠️ FFMPEG TIME CONTRACT — STRICT REQUIREMENTS:
- Return timestamps in ABSOLUTE SECONDS from the start of the video (usable in: ffmpeg -ss <start> -to <end> -i <input> ...).
- Only NUMBERS with decimal point, up to 3 decimals (examples: 0, 1.250, 17.350).
- Ensure 0 ≤ start < end ≤ VIDEO_DURATION_SECONDS.
- Each clip between 15 and 60 s (inclusive).
- Prefer starting 0.2–0.4 s BEFORE the hook and ending 0.2–0.4 s AFTER the payoff.
- Use silence moments for natural cuts; never cut in the middle of a word or phrase.
- STRICTLY FORBIDDEN to use time formats other than absolute seconds.

VIDEO_DURATION_SECONDS: {video_duration}

TRANSCRIPT_TEXT (raw):
{transcript_text}

WORDS_JSON (array of {{w, s, e}} where s/e are seconds):
{words_json}

STRICT EXCLUSIONS:
- No generic intros/outros or purely sponsorship segments unless they contain the hook.
- No clips < 15 s or > 60 s.

OUTPUT — RETURN ONLY VALID JSON (no markdown, no comments). Order clips by predicted performance (best to worst). In the descriptions, ALWAYS include a CTA like "Follow me and comment X and I'll send you the workflow" (especially if discussing an n8n workflow):
{{
  "shorts": [
    {{
      "start": <number in seconds, e.g., 12.340>,
      "end": <number in seconds, e.g., 37.900>,
      "video_description_for_tiktok": "<description for TikTok oriented to get views>",
      "video_description_for_instagram": "<description for Instagram oriented to get views>",
      "video_title_for_youtube_short": "<title for YouTube Short oriented to get views 100 chars max>"
    }}
  ]
}}
"""
