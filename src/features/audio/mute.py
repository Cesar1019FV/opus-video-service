from src.shared.exceptions import FFmpegError, VideoNotFoundError
import subprocess
import os

def remove_audio(input_path: str, output_path: str) -> None:
    """
    Elimina la pista de audio de un video usando FFmpeg, sin recodificar el video.

    Args:
        input_path (str): Ruta al video de entrada.
        output_path (str): Ruta al video sin audio.

    Raises:
        VideoNotFoundError: Si el archivo de entrada no existe.
        FFmpegError: Si FFmpeg falla.
    """
    if not os.path.exists(input_path):
        raise VideoNotFoundError(f"No se encontró el archivo: {input_path}")
    
    cmd = [
        "ffmpeg", "-y",    # -y to overwrite if already exists
        "-i", input_path,
        "-c:v", "copy",
        "-an",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise FFmpegError(
            f"Error al eliminar el audio con FFmpeg para {input_path}",
            command=' '.join(cmd),
            stderr=result.stderr
        )

    print(f"Audio eliminado exitosamente con FFmpeg: {output_path}")
