"""
Main CLI Menu Interface
Extracted from start_worker.py for clean separation.
Handles the Rich interactive menu and all user workflows.
"""
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.align import Align
from rich.text import Text

from .helpers import (
    select_video_file,
    select_media_file,
    select_music_file,
    get_save_path,
    finalize_output,
    get_video_from_input_dir,
    get_entry_effect_choice,
    get_subtitle_style_choice,
    clear_screen
)

console = Console()


def show_banner():
    """Display the application banner"""
    clear_screen()
    
    title = Text(r"""
   ____                  _     __     ___     _             
  / __ \                | |    \ \   / (_)   | |            
 | |  | |_ __  _   _ ___| |_____\ \ / / _  __| | ___  ___   
 | |  | | '_ \| | | / __| |______\ \ / | |/ _` |/ _ \/ _ \  
 | |__| | |_) | |_| \__ \_|       \ V /| | (_| |  __/ (_) | 
  \____/| .__/ \__,_|___(_)        \_/ |_|\__,_|\___|\___/  
        | |                                                 
        |_|                                                 
    """, style="bold cyan")
    
    subtitle = Text("\nOpus Video Service - AI Short Creator", style="bold white")
    
    console.print(Align.center(title))
    console.print(Align.center(subtitle))
    console.print(Align.center(Text("v1.0.0 | Powered by Gemini & Whisper", style="dim")))
    console.print("\n")


def main_menu():
    """Main interactive menu loop"""
    while True:
        show_banner()
        
        menu_text = """
[bold cyan]1.[/] 📥 Descargar Video (YouTube / TikTok)
[bold green]2.[/] 🚀 Procesar Video con IA (Detectar Virales / Vertical)
[bold blue]3.[/] 📝 Generar Subtítulos (Video Completo)
[bold magenta]4.[/] 🎨 Editor: Formatos Verticales (Split/Blur)
[bold yellow]5.[/] ✨ Editor: Agregar Efectos 'Hook' (Zoom/Flash)
[bold red]6.[/] 🎵 Audio: Agregar Música de Fondo
[bold cyan]7.[/] ⚡ Velocidad: Acelerar / Ralentizar
[bold cyan]8.[/] 🔇 Audio: Quitar Sonido (Mute)
[bold magenta]9.[/] 🎞️  60 FPS: Convertir a Sesenta
[bold red]10.[/] 🚪 Salir
        """
        
        console.print(Panel(menu_text, title="🔥 Opus Video Service - Menú Principal", border_style="blue", expand=False))
        
        choice = Prompt.ask("Selecciona una opción", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], default="2")
        
        if choice == '10':
            console.print("[bold red]¡Adiós![/]")
            sys.exit(0)
            
        run_job_ui(choice)


def run_editor_ui():
    """Sub-menu for Vertical Formats"""
    # ... (remains unchanged, lines 78-225) ...
    # Wait, the previous tool call doesn't show me lines 78-225 inside this block, 
    # but I must be careful not to delete them if I'm replacing a chunk.
    # The REPLACE block is lines 52-226? No, that's huge. 
    # Let's target just main_menu and the start of run_job_ui? 
    # BUT I need to change run_job_ui logic significantly for option 1 and 2.
    # It's better to do two replaces or one large one carefully.
    
    # I will replace main_menu function first.
    pass 

# Actually, I'll do the replace for main_menu and run_job_ui logic in steps or a larger block if needed.
# Let's replace main_menu first.



def run_editor_ui():
    """Sub-menu for Vertical Formats"""
    while True:
        menu_text = """
[bold magenta]1.[/] ✂️  Split Screen (Input + Gameplay)
[bold blue]2.[/] 💧 Blur Vertical (Input + Fondo Borroso)
[bold red]3.[/] 🔙 Volver al Menú Principal
        """
        console.print(Panel(menu_text, title="🎨 Editor de Formatos", border_style="magenta", expand=False))
        
        choice = Prompt.ask("Selecciona una opción", choices=["1", "2", "3"], default="1")
        
        if choice == '3':
            return  # Back to main menu
            
        input_path = select_video_file("Video para Edición")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            continue
            
        if choice == '1':  # Split Screen
            # Select background Media
            media_path = select_media_file()
            if not media_path:
                Prompt.ask("\nPresiona Enter para volver...")
                continue

            console.print(f"[bold green]✅ Video Principal: {os.path.basename(input_path)}[/]")
            console.print(f"[bold green]✅ Video Fondo: {os.path.basename(media_path)}[/]")
            
            effect = get_entry_effect_choice()
            
            final_path, temp_path = get_save_path(input_path, "split")
            write_path = temp_path if temp_path else final_path
            
            if not Confirm.ask("¿Proceder con Renderizado?", default=True): 
                continue
            
            try:
                from src.features.editing.split_screen import make_vertical_split_video
                with console.status("[bold magenta]🎬 Renderizando...[/]", spinner="bouncingBall"):
                    make_vertical_split_video(input_path, media_path, write_path, effect_type=effect)
                
                finalize_output(temp_path, final_path)
                console.print(f"[bold green]✨ Video listo: {final_path}[/]")
            except Exception as e:
                console.print(f"[bold red]❌ Error: {e}[/]")
                
        elif choice == '2':  # Blur Vert
            # 1. Ask for Title Gen
            title_text = ""
            use_ai_title = Confirm.ask("🧠 ¿Generar título con IA (basado en audio)?", default=True)
            
            if use_ai_title:
                try:
                    # Check for transcript or generate one
                    from src.features.transcription.service import transcribe_video
                    from src.features.viral_clips.service import generate_viral_title
                    
                    with console.status("[bold green]🎙️  Transcribiendo audio para título...[/]", spinner="dots"):
                         # We use a fast model just for the text context
                         transcript_data = transcribe_video(input_path, model_size="tiny", device="cpu")
                         
                    with console.status("[bold magenta]✨ Generando títulos virales...[/]", spinner="earth"):
                        titles = generate_viral_title(transcript_data['text'])
                        
                    if titles:
                        console.print("\n[bold cyan]💡 Títulos Sugeridos:[/]")
                        for i, t in enumerate(titles):
                            console.print(f"{i+1}. {t}")
                        console.print(f"{len(titles)+1}. [Escrbir Manualmente]")
                        
                        sel = IntPrompt.ask("Elige un título", choices=[str(i+1) for i in range(len(titles)+1)], default=1)
                        
                        if sel <= len(titles):
                            title_text = titles[sel-1]
                        else:
                            title_text = Prompt.ask("[bold yellow]📝 Ingresa título manual[/]")
                    else:
                        console.print("[red]❌ No se pudieron generar títulos.[/]")
                        title_text = Prompt.ask("[bold yellow]📝 Ingresa título (OBLIGATORIO)[/]")
                        
                except Exception as e:
                    console.print(f"[red]❌ Error IA: {e}[/]")
                    title_text = Prompt.ask("[bold yellow]📝 Ingresa título (OBLIGATORIO)[/]")
            else:
                title_text = Prompt.ask("[bold yellow]📝 Ingresa título (OBLIGATORIO)[/]")
                
            if not title_text: 
                continue
            
            # 2. Ask for Description Generation (Optional)
            descriptions = {}
            gen_desc = Confirm.ask("📝 ¿Generar descripciones para redes sociales?", default=False)
            
            if gen_desc:
                try:
                    from src.features.viral_clips.service import generate_video_descriptions
                    
                    # Reuse transcript if already loaded, otherwise transcribe
                    if use_ai_title and 'transcript_data' in locals():
                        trans_text = transcript_data['text']
                    else:
                        from src.features.transcription.service import transcribe_video
                        with console.status("[bold green]🎙️  Transcribiendo para descripciones...[/]", spinner="dots"):
                            trans_data = transcribe_video(input_path, model_size="tiny", device="cpu")
                            trans_text = trans_data['text']
                    
                    with console.status("[bold magenta]✨ Generando descripciones...[/]", spinner="earth"):
                        descriptions = generate_video_descriptions(trans_text, title_text)
                    
                    if descriptions:
                        console.print("\n[bold cyan]📱 Descripciones Generadas:[/]")
                        console.print(f"[yellow]TikTok:[/] {descriptions.get('tiktok', 'N/A')}")
                        console.print(f"[magenta]Instagram:[/] {descriptions.get('instagram', 'N/A')}")
                        console.print(f"[red]YouTube:[/] {descriptions.get('youtube', 'N/A')}")
                        
                        # Save descriptions to a text file alongside the video
                        final_path, temp_path = get_save_path(input_path, "blur")
                        desc_file = final_path.replace('.mp4', '_descriptions.txt')
                        with open(desc_file, 'w', encoding='utf-8') as f:
                            f.write(f"TITLE: {title_text}\n\n")
                            f.write(f"TIKTOK:\n{descriptions.get('tiktok', '')}\n\n")
                            f.write(f"INSTAGRAM:\n{descriptions.get('instagram', '')}\n\n")
                            f.write(f"YOUTUBE:\n{descriptions.get('youtube', '')}\n")
                        
                        console.print(f"[dim]💾 Descripciones guardadas en: {os.path.basename(desc_file)}[/]")
                        
                except Exception as e:
                    console.print(f"[red]❌ Error generando descripciones: {e}[/]")
            
            effect = get_entry_effect_choice()
            
            final_path, temp_path = get_save_path(input_path, "blur")
            write_path = temp_path if temp_path else final_path
            
            try:
                from src.features.editing.blur_background import make_blur_background_vertical_video
                console.print("[dim]Requiere ImageMagick para títulos.[/]")
                with console.status("[bold blue]🎬 Renderizando...[/]", spinner="bouncingBall"):
                    make_blur_background_vertical_video(input_path, write_path, title_text, effect_type=effect)
                
                finalize_output(temp_path, final_path)
                console.print(f"[bold green]✨ Video listo: {final_path}[/]")
            except Exception as e:
                 console.print(f"[bold red]❌ Error: {e}[/]")

        Prompt.ask("\nPresiona Enter para continuar...")


def run_job_ui(mode):
    """Handle the selected menu option"""
    url = None
    input_path = None
    
    if mode == '1':
        # Download Video (Generic)
        console.print("\n[bold cyan]Plataforma de Descarga:[/]")
        console.print("1. [red]YouTube[/]")
        console.print("2. [magenta]TikTok[/]")
        
        platform_choice = Prompt.ask("Elige plataforma", choices=["1", "2"], default="1")
        
        platform_name = "YouTube" if platform_choice == '1' else "TikTok"
        url = Prompt.ask(f"[bold cyan]Pega la URL de {platform_name}[/]")
        
        if not url: 
            return
            
        try:
            from src.shared.config import get_config
            config = get_config()
            
            video_path = None
            
            if platform_choice == '1':
                # YouTube
                from src.shared.youtube import download_youtube_video
                video_path, _ = download_youtube_video(url, str(config.input_dir))
            else:
                # TikTok
                from src.shared.tiktok import download_tiktok_video
                video_path, _ = download_tiktok_video(url, str(config.input_dir))
                
            console.print(f"[bold green]✅ Video descargado en Input:[/]")
            console.print(f"[cyan]{video_path}[/]")
            console.print("\n[dim]Ahora puedes seleccionarlo en la opción 2.[/]")
            
        except Exception as e:
            console.print(f"[bold red]❌ Error en descarga: {e}[/]")
            
        Prompt.ask("\nPresiona Enter para volver...")
        return
    
    elif mode == '2':
        # Auto-scan input folder for Processing
        input_path = get_video_from_input_dir()
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
        console.print(f"[bold green]✅ Archivo para procesar: {os.path.basename(input_path)}[/]")
        
    elif mode == '3':
        # Subtitle Only
        input_path = select_video_file("Video para Subtítulos")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
        
        console.print(f"[bold green]✅ Archivo seleccionado: {os.path.basename(input_path)}[/]")
        
        align = Prompt.ask("📍 Posición de subtítulos", choices=["bottom", "middle", "top"], default="bottom")
        
        # Style choice
        console.print("\n[bold yellow]Estilo de Subtítulos:[/]")
        console.print("1. [cyan]Frases (Estándar)[/]: Agrupa palabras para lectura cómoda.")
        console.print("2. [magenta]Dinámico (Palabra por palabra)[/]: Rápido, estilo TikTok.")
        style_choice = Prompt.ask("Elige estilo", choices=["1", "2"], default="1")
        single_word = (style_choice == '2')
        
        sub_style = get_subtitle_style_choice()
        
        # Save Path Logic
        final_path, temp_path = get_save_path(input_path, "subbed")
        write_path = temp_path if temp_path else final_path
        
        try:
             # Lazy import
            from src.main import run_subtitles_only
            
            run_subtitles_only(
                input_path, 
                specific_output_path=write_path, 
                alignment=align,
                single_word=single_word,
                style_name=sub_style
            )
            
            finalize_output(temp_path, final_path)
            
        except Exception as e:
            console.print(f"\n[bold red]❌ Error fatal:[/]")
            console.print(e)
            
        console.print("\n[bold green]✅ Proceso finalizado[/]")
        Prompt.ask("Presiona Enter para volver al menú...")
        return

    elif mode == '4':
        run_editor_ui()
        return

    elif mode == '5':
        # Hook Effects Workflow
        input_path = select_video_file("Video para Efecto 'Hook'")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
            
        effect = get_entry_effect_choice()
        if not effect:
            Prompt.ask("\nPresiona Enter para volver...")
            return
            
        final_path, temp_path = get_save_path(input_path, "hook")
        write_path = temp_path if temp_path else final_path
        
        try:
            from src.workflows.use_cases import add_hook_effect_to_video
            add_hook_effect_to_video(input_path, write_path, effect)
            
            finalize_output(temp_path, final_path)
            console.print(f"[bold green]✨ Video listo: {final_path}[/]")
        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/]")
            
        Prompt.ask("\nPresiona Enter para continuar...")
        return

    elif mode == '6':
        # Add Music Workflow
        input_path = select_video_file("Video Principal")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
            
        music_path = select_music_file()
        if not music_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
            
        vol = Prompt.ask("Volumen de música (0.0 a 1.0)", default="0.3")
        try:
            vol = float(vol)
        except:
            vol = 0.3
            
        final_path, temp_path = get_save_path(input_path, "music")
        write_path = temp_path if temp_path else final_path
        
        if not Confirm.ask("¿Proceder con Renderizado?", default=True): 
            return
            
        try:
            from src.features.audio.service import add_background_music_overlay
            with console.status("[bold red]🎵 Mezclando audio...[/]", spinner="wave"):
                add_background_music_overlay(input_path, music_path, write_path, music_volume=vol)
            
            finalize_output(temp_path, final_path)
            console.print(f"[bold green]✨ Video listo: {final_path}[/]")
        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/]")
            
        Prompt.ask("\nPresiona Enter para continuar...")
        return

    elif mode == '7':
        # Video Speed adjustment
        input_path = select_video_file("Video para Ajustar Velocidad")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
            
        console.print("\n[bold cyan]Selecciona el Factor de Velocidad:[/]")
        console.print("1. [yellow]0.5x[/] (Cámara Lenta)")
        console.print("2. [yellow]0.75x[/] (Suave)")
        console.print("3. [green]1.1x[/] (Retención Ligera - Recomendado)")
        console.print("4. [green]1.25x[/] (Dinámico)")
        console.print("5. [magenta]1.5x[/] (Rápido)")
        console.print("6. [red]2.0x[/] (Doble Velocidad)")
        console.print("7. [cyan]Personalizado[/]")
        
        speed_choice = Prompt.ask("Opción", choices=["1", "2", "3", "4", "5", "6", "7"], default="3")
        
        factors = {
            "1": 0.5,
            "2": 0.75,
            "3": 1.1,
            "4": 1.25,
            "5": 1.5,
            "6": 2.0
        }
        
        if speed_choice == "7":
            factor = Prompt.ask("Ingresa el multiplicador (e.g., 1.12)", default="1.1")
            try:
                factor = float(factor)
            except:
                factor = 1.1
        else:
            factor = factors[speed_choice]
            
        final_path, temp_path = get_save_path(input_path, f"speed_{factor}x")
        write_path = temp_path if temp_path else final_path
        
        try:
            from src.features.effects.speed import change_video_speed
            with console.status(f"[bold cyan]⚡ Ajustando velocidad a {factor}x...[/]", spinner="runner"):
                change_video_speed(input_path, write_path, factor)
                
            finalize_output(temp_path, final_path)
            console.print(f"[bold green]✨ Video listo: {final_path}[/]")
        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/]")
            
        Prompt.ask("\nPresiona Enter para continuar...")
        return

    elif mode == '8':
        # Mute video
        input_path = select_video_file("Video para Quitar Audio")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
            
        final_path, temp_path = get_save_path(input_path, "mute")
        write_path = temp_path if temp_path else final_path
        
        if not Confirm.ask("¿Confirmas que quieres quitar TODO el sonido?", default=True):
            return
            
        try:
            from src.features.audio.mute import remove_audio
            with console.status("[bold cyan]🔇 Quitando audio...[/]", spinner="dots"):
                remove_audio(input_path, write_path)
                
            finalize_output(temp_path, final_path)
            console.print(f"[bold green]✨ Video sin audio listo: {final_path}[/]")
        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/]")
            
        Prompt.ask("\nPresiona Enter para continuar...")
        return

    elif mode == '9':
        # Convert to 60fps
        input_path = select_video_file("Video para Convertir a 60fps")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
            
        final_path, temp_path = get_save_path(input_path, "60fps")
        write_path = temp_path if temp_path else final_path
        
        try:
            from src.features.effects.fps import convert_to_60fps
            with console.status("[bold magenta]🎞️  Convirtiendo a 60fps...[/]", spinner="arc"):
                convert_to_60fps(input_path, write_path)
                
            finalize_output(temp_path, final_path)
            console.print(f"[bold green]✨ Video a 60fps listo: {final_path}[/]")
        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/]")
            
        Prompt.ask("\nPresiona Enter para continuar...")
        return

    # Options (Only for Mode 1 & 2)
    console.print("\n[bold yellow]Configuración del Trabajo:[/]")

    use_subs = Confirm.ask("📜 ¿Quieres quemar subtítulos en el video?", default=False)
    
    align = "bottom"
    single_word = False
    
    if use_subs:
        align = Prompt.ask("📍 Posición de subtítulos", choices=["bottom", "middle", "top"], default="bottom")
        console.print("\n[bold yellow]Estilo de Subtítulos:[/]")
        console.print("1. [cyan]Frases (Estándar)[/]: Agrupa palabras.")
        console.print("2. [magenta]Dinámico (Palabra por palabra)[/]: Estilo TikTok.")
        style_choice = Prompt.ask("Elige estilo", choices=["1", "2"], default="1")
        single_word = (style_choice == '2')
    
    console.print("\n[bold yellow]Análisis con IA (Gemini):[/]")
    console.print("- [cyan]Sí[/]: Detecta clips virales automáticamente")
    console.print("- [cyan]No[/]: Convierte todo el video a vertical (sin cortes)")
    use_gemini = Confirm.ask("🧠 ¿Usar IA para detectar virales?", default=True)
    skip_analysis = not use_gemini

    console.print(Panel("🚀 Iniciando Pipeline...", style="bold green"))

    # Import pipeline here to avoid early crashes
    try:
        from src.main import run_pipeline
    except Exception as e:
        console.print(f"[bold red]❌ Error importando cerebro:[/]")
        console.print(e)
        input("Enter para volver...")
        return

    try:
        run_pipeline(
            input_path=input_path,
            url=url,
            output_dir="output",
            use_subs=use_subs,
            skip_analysis=skip_analysis,
            alignment=align,
            single_word=single_word,
            style_name=sub_style
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Interrumpido por usuario[/]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Error fatal:[/]")
        console.print(e)
        import traceback
        traceback.print_exc()
        
    console.print("\n[bold green]✅ Proceso finalizado[/]")
    Prompt.ask("Presiona Enter para volver al menú...")
