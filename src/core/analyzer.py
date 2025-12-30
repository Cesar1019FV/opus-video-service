import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

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

def generate_viral_title(transcript_text):
    """
    Generates viral titles using Gemini based on transcript.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return None

    client = genai.Client(api_key=api_key)
    model_name = 'gemini-2.5-flash'
    
    # Limit transcript context to first 2000 chars to save tokens and focus on hook
    truncated_transcript = transcript_text[:2000]

    prompt = TITLE_PROMPT_TEMPLATE.format(transcript_text=truncated_transcript)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        
        data = json.loads(response.text)
        return data.get("titles", [])
    except Exception as e:
        print(f"❌ Error generating title: {e}")
        return []

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

def generate_video_descriptions(transcript_text, video_title=""):
    """
    Generates platform-specific descriptions using Gemini.
    Args:
        transcript_text: Full or partial transcript
        video_title: Optional title to provide context
    Returns:
        dict with keys: tiktok_description, instagram_description, youtube_description
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return None

    client = genai.Client(api_key=api_key)
    model_name = 'gemini-2.5-flash'
    
    # Limit transcript to 2000 chars to save tokens
    truncated_transcript = transcript_text[:2000]

    prompt = DESCRIPTION_PROMPT_TEMPLATE.format(
        video_title=video_title or "Viral Short",
        transcript_text=truncated_transcript
    )

    try:
        response = client.models.generate_content(
            model=model_name,
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

GEMINI_PROMPT_TEMPLATE = """
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

def get_viral_clips(transcript_result, video_duration):
    # print("🤖  Analyzing with Gemini...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        return None

    client = genai.Client(api_key=api_key)
    model_name = 'gemini-2.5-flash' 
    
    # print(f"🤖  Initializing Gemini with model: {model_name}")

    # Extract words
    words = []
    for segment in transcript_result['segments']:
        for word in segment.get('words', []):
            words.append({
                'w': word['word'],
                's': word['start'],
                'e': word['end']
            })

    prompt = GEMINI_PROMPT_TEMPLATE.format(
        video_duration=video_duration,
        transcript_text=json.dumps(transcript_result['text']),
        words_json=json.dumps(words)
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        # --- Cost Calculation ---
        try:
            usage = response.usage_metadata
            input_price_per_million = 0.10
            output_price_per_million = 0.40
            
            prompt_tokens = usage.prompt_token_count
            output_tokens = usage.candidates_token_count
            
            input_cost = (prompt_tokens / 1_000_000) * input_price_per_million
            output_cost = (output_tokens / 1_000_000) * output_price_per_million
            total_cost = input_cost + output_cost
            
            from rich.console import Console
            from rich.table import Table
            console = Console()
            
            table = Table(title=f"💰 Token Usage ({model_name})", show_header=True, header_style="bold magenta")
            table.add_column("Type", style="cyan")
            table.add_column("Count", justify="right")
            table.add_column("Cost ($)", justify="right", style="green")
            
            table.add_row("Input", str(prompt_tokens), f"${input_cost:.6f}")
            table.add_row("Output", str(output_tokens), f"${output_cost:.6f}")
            table.add_row("Total", "", f"${total_cost:.6f}", style="bold")
            
            console.print(table)
                
        except Exception as e:
            # print(f"⚠️ Could not calculate cost: {e}")
            pass
        # ------------------------
        
        # Clean response if it contains markdown code blocks
        text = response.text
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        result_json = json.loads(text)
            
        return result_json
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None
