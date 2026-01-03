from src.shared.exceptions import FFmpegError, VideoNotFoundError
import subprocess
import os

def change_video_speed(
    input_path: str,
    output_path: str,
    factor_velocidad: float
) -> None:
    """
    Cambia la velocidad de un video (video + audio) usando FFmpeg directo.

    Args:
        input_path (str): Ruta de entrada.
        output_path (str): Ruta de salida.
        factor_velocidad (float): Factor para velocidad (>0).
                                  >1 acelera, <1 ralentiza.

    Raises:
        ValueError: Si factor_velocidad <= 0.
        VideoNotFoundError: Si no existe el archivo de entrada.
        FFmpegError: Si FFmpeg falla.
    """
    if factor_velocidad <= 0:
        raise ValueError("El factor de velocidad debe ser mayor que 0.")

    if not os.path.exists(input_path):
        raise VideoNotFoundError(f"No se encontró: {input_path}")

    # Construir filtros
    # Video: setpts
    setpts = f"setpts={1/factor_velocidad}*PTS"

    # Audio: atempo
    # atempo solo acepta 0.5 <= valor <= 2
    atempo_filters = []
    f = factor_velocidad
    while f > 2:
        atempo_filters.append("atempo=2")
        f /= 2
    while f < 0.5:
        atempo_filters.append("atempo=0.5")
        f *= 2
    atempo_filters.append(f"atempo={f:.8g}")
    atempo = ",".join(atempo_filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex",
        f"[0:v]{setpts}[v];[0:a]{atempo}[a]",
        "-map", "[v]",
        "-map", "[a]",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise FFmpegError(
            f"Error al ajustar velocidad con FFmpeg para {input_path}",
            command=' '.join(cmd),
            stderr=result.stderr
        )

    print(f"Velocidad ajustada correctamente: {output_path}")
