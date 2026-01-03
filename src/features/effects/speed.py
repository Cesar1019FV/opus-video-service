"""
Módulo para ajustar la velocidad de videos usando MoviePy.
"""

from moviepy.editor import VideoFileClip
import moviepy.video.fx.all as vfx
import os

def change_video_speed(
    input_path: str,
    output_path: str,
    factor_velocidad: float,
    codec: str = "libx264",
    audio_codec: str = "aac"
) -> None:
    """
    Modifica la velocidad de un video aplicando el efecto speedx.
    
    Acelera o ralentiza un video (y su audio) basándose en el factor de velocidad.
    Mantiene la sincronización y no altera manualmente los FPS.
    
    Args:
        input_path (str): Ruta al archivo de video de entrada.
        output_path (str): Ruta donde se guardará el video resultante.
        factor_velocidad (float): Factor multiplicador de velocidad.
                                  > 1.0 para acelerar (e.g., 2.0 es doble velocidad).
                                  < 1.0 para ralentizar (e.g., 0.5 es mitad de velocidad).
        codec (str, optional): Codec de video para la exportación. Por defecto "libx264".
        audio_codec (str, optional): Codec de audio para la exportación. Por defecto "aac".
        
    Raises:
        ValueError: Si el factor_velocidad es menor o igual a 0.
        FileNotFoundError: Si el video de entrada no existe.
    """
    
    if factor_velocidad <= 0:
        raise ValueError("El factor de velocidad debe ser mayor que 0.")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {input_path}")

    clip = None
    final_clip = None

    try:
        # Cargar el video
        clip = VideoFileClip(input_path)

        # Aplicar el efecto speedx
        # vfx.speedx maneja tanto video como audio automáticamente
        final_clip = clip.fx(vfx.speedx, factor_velocidad)

        # Exportar el resultado
        # Se mantienen los parámetros originales excepto los codecs especificados
        final_clip.write_videofile(
            output_path,
            codec=codec,
            audio_codec=audio_codec,
            logger=None # Reducir verbosidad en consola si se desea, o 'bar'
        )
        
        print(f"Video procesado exitosamente: {output_path}")

    except Exception as e:
        print(f"Error al procesar el video: {e}")
        raise e
    finally:
        # Cerrar recursos explícitamente
        if final_clip:
            final_clip.close()
        if clip:
            clip.close()

# Ejemplo de uso:
if __name__ == "__main__":
    # Asegúrate de tener un video de prueba 'input.mp4' o cambiar la ruta
    # change_video_speed("input.mp4", "output_fast.mp4", 2.0)
    pass
