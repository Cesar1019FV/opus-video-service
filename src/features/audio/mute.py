"""
Módulo para eliminar el audio de videos usando MoviePy.
"""

from moviepy.editor import VideoFileClip
import os

def remove_audio(
    input_path: str,
    output_path: str,
    codec: str = "libx264",
    audio_codec: str = "aac"
) -> None:
    """
    Elimina la pista de audio de un video (mute), sin alterar la imagen ni la duración.
    
    Args:
        input_path (str): Ruta al video de entrada.
        output_path (str): Ruta donde se guardará el video sin audio.
        codec (str, optional): Codec de video para la exportación. Por defecto "libx264".
        audio_codec (str, optional): Codec de audio. Aunque no haya audio, MoviePy puede requerirlo esporádicamente
                                     o se ignora si no hay audio track, pero se mantiene por compatibilidad de firma.
    
    Raises:
        FileNotFoundError: Si el archivo de entrada no existe.
    """
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {input_path}")

    clip = None

    try:
        # Cargar el video directamente sin audio (más rápido y seguro)
        clip = VideoFileClip(input_path, audio=False)

        # Exportar el video resultante
        clip.write_videofile(
            output_path,
            codec=codec,
            audio_codec=audio_codec, 
            audio=False, 
            logger=None
        )
        
        print(f"Audio eliminado exitosamente (vía load mute): {output_path}")

    except Exception as e:
        print(f"Error al eliminar audio: {e}")
        raise e
    finally:
        # Cerrar recursos
        if clip:
            clip.close()

# Ejemplo de uso:
if __name__ == "__main__":
    # remove_audio("video_con_audio.mp4", "video_muteado.mp4")
    pass
