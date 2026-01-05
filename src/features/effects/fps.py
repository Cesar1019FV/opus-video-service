from src.shared.exceptions import FFmpegError, VideoNotFoundError
import subprocess
import os

def convert_to_60fps(
    input_path: str,
    output_path: str
) -> None:
    """
    Convierte un video a 60fps usando FFmpeg directo.

    Args:
        input_path (str): Ruta de entrada.
        output_path (str): Ruta de salida.

    Raises:
        VideoNotFoundError: Si no existe el archivo de entrada.
        FFmpegError: Si FFmpeg falla.
    """
    if not os.path.exists(input_path):
        raise VideoNotFoundError(f"No se encontró el archivo de video: {input_path}")

    # Comando optimizado según requerimiento:
    # ffmpeg -i input.mp4 -vf "fps=60" -c:v libx264 -preset fast -crf 23 -c:a copy output_60fps.mp4
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", "fps=60",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise FFmpegError(
            f"Error al convertir video a 60fps para {input_path}",
            command=' '.join(cmd),
            stderr=result.stderr
        )

    print(f"Video convertido a 60fps correctamente: {output_path}")
