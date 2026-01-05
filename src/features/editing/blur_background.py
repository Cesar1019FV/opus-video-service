import subprocess
import shutil
import tempfile
import os
from pathlib import Path

def _run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"FFmpeg failed.\nCMD: {' '.join(cmd)}\n\nSTDERR:\n{p.stderr}")
    return p

def _escape_for_subtitles_filter(path_str: str) -> str:
    """
    Escapado razonable para el filtro subtitles (especialmente Windows):
    - usar / en vez de \
    - escapar ':' como '\:'
    - escapar "'" porque usamos comillas simples en la expresión
    """
    s = path_str.replace("\\", "/")
    # En Windows, el ':' del drive es el problema principal
    s = s.replace(":", r"\:")
    # Si el path tuviera comillas simples
    s = s.replace("'", r"\'")
    return s

def make_blur_background_vertical_video(
    input_video_path: str,
    output_path: str,
    title_text: str = None,
    blur_sigma: int = 35,
    main_width_ratio: float = 0.88,
    fps: int = 30,
    style_name: str = "default",
    effect_type: str = None  # Agregado para compatibilidad con el workflow
):
    from src.features.subtitles.styles import SUBTITLE_STYLES

    if not shutil.which("ffmpeg"):
        raise EnvironmentError("❌ FFmpeg no está en el PATH.")

    input_video_path = str(Path(input_video_path))
    output_path = str(Path(output_path))

    temp_output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    temp_srt_path = None

    # ---- Etapa 1: fondo blur + video centrado (1080x1920) ----
    scale_main_w = int(1080 * main_width_ratio)
    scale_main_w = (scale_main_w // 2) * 2

    filter_complex = (
        f"[0:v]split=2[fg][bg];"
        f"[bg]scale=1200:2134:force_original_aspect_ratio=increase,"
        f"crop=1200:2134,"
        f"gblur=sigma={blur_sigma}[blurred];"
        f"[fg]scale=1140:-2:force_original_aspect_ratio=increase[front];"
        f"[blurred][front]overlay=(W-w)/2:(H-h)/2[tmp];"
        f"[tmp]crop=1080:1920,setsar=1[v]"
    )


    cmd1 = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", input_video_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        temp_output
    ]
    _run(cmd1)

    # ---- Etapa 2: título arriba usando subtitles + force_style ----
    if title_text:
        def wrap_text(text, max_chars=25):
            words = text.split()
            lines, cur = [], ""
            for w in words:
                if len(cur) + len(w) + (1 if cur else 0) > max_chars:
                    lines.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            if cur:
                lines.append(cur)
            return r"\N".join(lines)

        wrapped_title = wrap_text(title_text.strip().upper())

        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False, mode="w", encoding="utf-8") as tf:
            temp_srt_path = tf.name
            tf.write(f"1\n00:00:00,000 --> 02:00:00,000\n{wrapped_title}\n\n")

        style = SUBTITLE_STYLES.get(style_name, SUBTITLE_STYLES["default"])

        # force_style acepta claves ASS. Ejemplos típicos: Alignment, Fontsize, Outline, etc. :contentReference[oaicite:2]{index=2}
        style_parts = [
            "Alignment=6",      # top-center
            "MarginV=100",
            "Outline=2",
            "OutlineColour=&H000000&",
            "Fontsize=15",
            "Fontname=Arial Black"
        ]

        for k, v in style.items():
            if k != "name":
                style_parts.append(f"{k}={v}")
        style_str = ",".join(style_parts)

        safe_srt = _escape_for_subtitles_filter(temp_srt_path)

        cmd2 = [
            "ffmpeg", "-y",
            "-i", temp_output,
            "-vf", f"subtitles='{safe_srt}':force_style='{style_str}'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            output_path
        ]
        _run(cmd2)
    else:
        shutil.move(temp_output, output_path)

    # cleanup
    if os.path.exists(temp_output):
        os.remove(temp_output)
    if temp_srt_path and os.path.exists(temp_srt_path):
        os.remove(temp_srt_path)

    return output_path
