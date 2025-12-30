import os
import sys
import time
import subprocess
import importlib

# ---------------------------------------------------------
# Auto-Venv Bootstrap
# ---------------------------------------------------------
def ensure_venv():
    """Ensures the script runs inside a virtual environment (.venv)."""
    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
    
    # Are we already in a virtual environment?
    in_venv = sys.prefix != sys.base_prefix
    
    if in_venv:
        return

    # If not in venv, check if .venv exists
    if not os.path.exists(venv_dir):
        print("\n🚀 Primera ejecución detectada. Configurando entorno virtual...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", ".venv"])
            print("✅ Entorno virtual (.venv) creado.")
            
            # Identify venv python
            venv_python = os.path.join(venv_dir, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(venv_dir, "bin", "python")
            
            # Install requirements
            if os.path.exists("requirements.txt"):
                print("⏳ Instalando dependencias desde requirements.txt...")
                subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
                subprocess.check_call([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])
                print("✅ Dependencias instaladas correctamente.")
        except Exception as e:
            print(f"❌ Error al configurar el entorno: {e}")
            sys.exit(1)

    # Re-run the script using the venv python
    venv_python = os.path.join(venv_dir, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(venv_dir, "bin", "python")
    
    if os.path.exists(venv_python):
        # Reiniciar usando el python del venv
        # print(f"🔄 Reiniciando en entorno virtual...")
        try:
            # sys.argv[0] is the script path
            result = subprocess.run([venv_python] + sys.argv)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"❌ Error al reiniciar en el entorno virtual: {e}")
            sys.exit(1)
    else:
        print("⚠️ Advertencia: No se encontró el ejecutable en .venv. Continuando con el Python actual.")

# Bootstrap before anything else
ensure_venv()

# ---------------------------------------------------------
# Dependency Check (Pre-Rich)
# ---------------------------------------------------------
def check_dependencies():
    """Checks if FFMPEG and critical python libs are available."""
    print("🔍 Diagnosticando entorno...")
    missing = []
    
    # Check FFMPEG
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        # ... (keep ffmpeg error) ...
        print("\n❌ ERROR: FFMPEG no está instalado o no está en el PATH.")
        # ...
        sys.exit(1)
        
    # Check Python Libs (including rich)
    libs = [
        ('cv2', 'opencv-python'),
        ('scenedetect', 'scenedetect'),
        ('ultralytics', 'ultralytics'),
        ('faster_whisper', 'faster-whisper'),
        ('yt_dlp', 'yt-dlp'),
        ('google.genai', 'google-genai'),
        ('rich.console', 'rich') # Check specific submodule for rich
    ]
    
    for module_name, pip_name in libs:
        try:
            importlib.import_module(module_name)
        except ImportError:
             missing.append(f"{pip_name}")

    if missing:
        print("\n📦 Paquetes faltantes encontrados:")
        for m in missing:
            print(f"   - {m}")
        
        confirm = input("\n¿Instalar paquetes faltantes ahora? (s/n) [s]: ").strip().lower() or 's'
        
        if confirm == 's':
            try:
                print("⏳ Instalando dependencias...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                print("\n✅ Dependencias instaladas! Continuando...")
                time.sleep(1)
                importlib.invalidate_caches()
            except Exception as e:
                print(f"❌ Falló la instalación: {e}")
                sys.exit(1)
        else:
            sys.exit(1)

# Run check BEFORE importing rich
check_dependencies()

# ---------------------------------------------------------
# Rich UI Imports
# ---------------------------------------------------------
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.align import Align
from rich import print as rprint
from rich.text import Text

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
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
    while True:
        show_banner()
        
        menu_text = """
[bold green]1.[/] 🧠 Encontrar Clips Virales (YouTube URL)
[bold green]2.[/] 📂 Encontrar Clips Virales (Archivo Local)
[bold cyan]3.[/] 📝 Generar Subtítulos (Video Completo)
[bold magenta]4.[/] 🎨 Editor: Formatos Verticales (Split/Blur)
[bold yellow]5.[/] ✨ Editor: Agregar Efectos 'Hook' (Zoom/Flash)
[bold blue]6.[/] 🎵 Audio: Agregar Música de Fondo
[bold red]7.[/] 🚪 Salir
        """
        
        console.print(Panel(menu_text, title="🔥 Opus Video Service - Menú Principal", border_style="blue", expand=False))
        
        choice = Prompt.ask("Selecciona una opción", choices=["1", "2", "3", "4", "5", "6", "7"], default="2")
        
        if choice == '7':
            console.print("[bold red]¡Adiós![/]")
            sys.exit(0)
            
        run_job_ui(choice)

def select_video_file(prompt="Selecciona Video de Entrada"):
    """
    Allows selecting a video from 'input' or 'output' folder with list selection.
    """
    console.print(f"\n[bold cyan]📂 {prompt}:[/]")
    console.print("1. [green]Carpeta Input[/] (Nuevos videos)")
    console.print("2. [yellow]Carpeta Output[/] (Videos ya procesados)")
    
    source = Prompt.ask("Fuente", choices=["1", "2"], default="1")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if source == '1':
        # Input Dir Logic - ALWAYS show list for multiple files
        input_dir = os.path.join(base_dir, 'input')
        os.makedirs(input_dir, exist_ok=True)
        valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
        files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]
        
        if not files:
            console.print(f"[bold red]❌ La carpeta 'input' está vacía.[/]")
            console.print(f"[yellow]👉 Por favor, coloca videos en: {input_dir}[/]")
            return None
        
        # Show list regardless of count
        if len(files) == 1:
            console.print(f"\n[bold green]📹 Video disponible:[/]")
            console.print(f"1. {files[0]}")
            if Confirm.ask("¿Usar este video?", default=True):
                return os.path.join(input_dir, files[0])
            else:
                return None
        else:
            console.print(f"\n[bold green]📹 Videos disponibles en Input:[/]")
            for idx, f in enumerate(files):
                console.print(f"[bold cyan]{idx+1}.[/] {f}")
            choice = IntPrompt.ask("Elige el número", choices=[str(i+1) for i in range(len(files))])
            return os.path.join(input_dir, files[choice-1])

    else:
        # Output Dir Logic
        output_dir = os.path.join(base_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
        files = [f for f in os.listdir(output_dir) if f.lower().endswith(valid_exts)]
        
        if not files:
            console.print(f"[bold red]❌ La carpeta 'output' está vacía.[/]")
            return None
            
        console.print(f"\n[bold yellow]📹 Videos en Output:[/]")
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
        
        for idx, f in enumerate(files):
            console.print(f"[bold cyan]{idx+1}.[/] {f}")
            
        choice = IntPrompt.ask("Elige el video para procesar", choices=[str(i+1) for i in range(len(files))])
        return os.path.join(output_dir, files[choice-1])

def select_media_file():
    """
    Selects a background video from 'media' directory with list selection.
    """
    media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
    os.makedirs(media_dir, exist_ok=True)
    valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    files = [f for f in os.listdir(media_dir) if f.lower().endswith(valid_exts)]
    
    if not files:
        console.print(f"[bold red]❌ La carpeta 'media' está vacía.[/]")
        console.print(f"[yellow]👉 Por favor, coloca videos de fondo (gameplay) en: {media_dir}[/]")
        return None
        
    console.print(f"\n[bold magenta]🎮 Videos de Fondo Disponibles:[/]")
    for idx, f in enumerate(files):
        console.print(f"[bold cyan]{idx+1}.[/] {f}")
        
    choice = IntPrompt.ask("Elige el video de fondo", choices=[str(i+1) for i in range(len(files))])
    return os.path.join(media_dir, files[choice-1])

def select_music_file():
    """
    Selects a music file from 'music' directory with list selection.
    """
    music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music')
    os.makedirs(music_dir, exist_ok=True)
    valid_exts = ('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac')
    files = [f for f in os.listdir(music_dir) if f.lower().endswith(valid_exts)]
    
    if not files:
        console.print(f"[bold red]❌ La carpeta 'music' está vacía.[/]")
        console.print(f"[yellow]👉 Por favor, coloca archivos de música en: {music_dir}[/]")
        return None
        
    console.print(f"\n[bold cyan]🎵 Música Disponible:[/]")
    for idx, f in enumerate(files):
        console.print(f"[bold cyan]{idx+1}.[/] {f}")
        
    choice = IntPrompt.ask("Elige la música de fondo", choices=[str(i+1) for i in range(len(files))])
    return os.path.join(music_dir, files[choice-1])

def get_save_path(input_path, default_suffix, output_dir="output"):
    """
    Determines output path, allowing overwrite of input or other files.
    """
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    default_name = f"{base_name}_{default_suffix}.mp4"
    default_path = os.path.join(output_dir, default_name)
    
    console.print(f"\n[bold yellow]💾 ¿Cómo quieres guardar el resultado?[/]")
    console.print(f"1. [green]Guardar como Nuevo[/]: {default_name}")
    console.print(f"2. [red]Sobrescribir Entrada[/]: {os.path.basename(input_path)}")
    console.print(f"3. [cyan]Sobrescribir Otro...[/] (Seleccionar manual)")
    
    choice = Prompt.ask("Opción de guardado", choices=["1", "2", "3"], default="1")
    
    target_path = default_path
    
    if choice == '2':
        target_path = input_path
        
    elif choice == '3':
        # List output files
        valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
        files = [f for f in os.listdir(output_dir) if f.lower().endswith(valid_exts)]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
        
        if not files:
            console.print("[red]No hay archivos para sobrescribir. Usando automático.[/]")
        else:
            for idx, f in enumerate(files):
                console.print(f"{idx+1}. {f}")
            sel = IntPrompt.ask("Elige archivo a sobrescribir", choices=[str(i+1) for i in range(len(files))])
            target_path = os.path.join(output_dir, files[sel-1])
            
    # Collision handling logic
    if os.path.abspath(target_path) == os.path.abspath(input_path):
        console.print("[dim]✏️  Se sobrescribirá el archivo original al finalizar.[/]")
        timestamp = int(time.time())
        temp_path = os.path.join(output_dir, f"temp_{timestamp}_{os.path.basename(target_path)}")
        return target_path, temp_path
        
    if os.path.exists(target_path) and choice != '2':
         console.print(f"[yellow]⚠️  El archivo {os.path.basename(target_path)} ya existe y será reemplazado.[/]")
         timestamp = int(time.time())
         temp_path = os.path.join(output_dir, f"temp_{timestamp}_{os.path.basename(target_path)}")
         return target_path, temp_path

    return target_path, None

def finalize_output(temp_path, final_path):
    """Helper to finalize overwrite"""
    if temp_path and os.path.exists(temp_path):
        import shutil
        # If final exists, remove
        if os.path.exists(final_path):
            os.remove(final_path)
        shutil.move(temp_path, final_path)
        return final_path
    return final_path

def get_video_from_input_dir():
    """Legacy function for Mode 2 (Viral Clips) - enforces single file"""
    input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input')
    os.makedirs(input_dir, exist_ok=True)
    
    # Valid extensions
    valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]
    
    if len(files) == 0:
        console.print(f"[bold red]❌ La carpeta 'input' está vacía.[/]")
        console.print(f"[yellow]👉 Por favor, coloca 1 archivo de video en: {input_dir}[/]")
        return None
        
    if len(files) > 1:
        console.print(f"[bold red]❌ Hay demasiados videos ({len(files)}) en la carpeta 'input'.[/]")
        console.print(f"[yellow]👉 Por favor, deja SOLO UN archivo para evitar errores.[/]")
        for f in files:
            console.print(f"   - {f}")
        return None
        
    return os.path.join(input_dir, files[0])

def get_entry_effect_choice():
    """Helper to ask for effect"""
    if not Confirm.ask("✨ ¿Quieres agregar un efecto de entrada 'Hook'?", default=False):
        return None
        
    console.print("\n[bold magenta]Selecciona un Efecto de Entrada:[/]")
    console.print("1. [cyan]Zoom Punch + Focus[/] (Estilo TikTok clásico)")
    console.print("2. [cyan]Flash In + Punch[/] (Agresivo)")
    console.print("3. [cyan]Slide In Top + Zoom[/] (Gaming/Dinámico)")
    
    return Prompt.ask("Opción", choices=["1", "2", "3"], default="1")

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
            return # Back to main menu
            
        input_path = select_video_file("Video para Edición")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            continue
            
        if choice == '1': # Split Screen
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
            
            if not Confirm.ask("¿Proceder con Renderizado?", default=True): continue
            
            try:
                from src.core.editor import make_vertical_split_video
                with console.status("[bold magenta]🎬 Renderizando...[/]", spinner="bouncingBall"):
                    make_vertical_split_video(input_path, media_path, write_path, effect_type=effect)
                
                finalize_output(temp_path, final_path)
                console.print(f"[bold green]✨ Video listo: {final_path}[/]")
            except Exception as e:
                console.print(f"[bold red]❌ Error: {e}[/]")
                
        elif choice == '2': # Blur Vert
            # 1. Ask for Title Gen
            title_text = ""
            use_ai_title = Confirm.ask("🧠 ¿Generar título con IA (basado en audio)?", default=True)
            
            if use_ai_title:
                try:
                    # Check for transcript or generate one
                    from src.core.transcriber import transcribe_video
                    from src.core.analyzer import generate_viral_title
                    
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
                
            if not title_text: continue
            
            # 2. Ask for Description Generation (Optional)
            descriptions = {}
            gen_desc = Confirm.ask("📝 ¿Generar descripciones para redes sociales?", default=False)
            
            if gen_desc:
                try:
                    from src.core.analyzer import generate_video_descriptions
                    
                    # Reuse transcript if already loaded, otherwise transcribe
                    if use_ai_title and 'transcript_data' in locals():
                        trans_text = transcript_data['text']
                    else:
                        from src.core.transcriber import transcribe_video
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
                from src.core.editor import make_blur_background_vertical_video
                console.print("[dim]Requiere ImageMagick para títulos.[/]")
                with console.status("[bold blue]🎬 Renderizando...[/]", spinner="bouncingBall"):
                    make_blur_background_vertical_video(input_path, write_path, title_text, effect_type=effect)
                
                finalize_output(temp_path, final_path)
                console.print(f"[bold green]✨ Video listo: {final_path}[/]")
            except Exception as e:
                 console.print(f"[bold red]❌ Error: {e}[/]")

        Prompt.ask("\nPresiona Enter para continuar...")


def run_job_ui(mode):
    url = None
    input_path = None
    
    if mode == '1':
        url = Prompt.ask("[bold cyan]Pega la URL de YouTube[/]")
        if not url: return
    
    elif mode == '2':
        # Auto-scan input folder
        input_path = get_video_from_input_dir()
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
        console.print(f"[bold green]✅ Archivo encontrado: {os.path.basename(input_path)}[/]")
        
    elif mode == '3':
        # Subtitle Only
        input_path = select_video_file("Video para Subtítulos")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
        
        console.print(f"[bold green]✅ Archivo seleccionado: {os.path.basename(input_path)}[/]")
        
        align = Prompt.ask("📍 Posición de subtítulos", choices=["bottom", "middle", "top"], default="bottom")
        
        # Save Path Logic
        final_path, temp_path = get_save_path(input_path, "subbed")
        write_path = temp_path if temp_path else final_path
        
        try:
             # Lazy import
            from src.main import run_subtitles_only
            # run_subtitles_only needs update or we pass output_dir?
            # It expects output_dir and constructs name.
            # We need to change run_subtitles_only to accept specific output file or directory?
            # Currently: output_dir=... -> joins basname.
            # We should probably modify run_subtitles_only signature OR 
            # pass a custom directory/filename trick.
            
            # Let's modify src/main.py quickly? Or pass a fake output path?
            # Easier to update src/main.py run_subtitles_only to accept 'output_file' argument.
            
            # WORKAROUND: For now, if run_subtitles_only is rigid, we might need to patch it.
            # But the user asked to "use the output again and overwrite", implying strong control.
            # Let's assume we update `run_subtitles_only` too.
            
            # Assuming I will update run_subtitles_only to support `specific_output_path`.
            run_subtitles_only(input_path, specific_output_path=write_path, alignment=align)
            
            finalize_output(temp_path, final_path)
            
        except TypeError: 
             # Fallback if I haven't updated main.py yet (Safety)
             run_subtitles_only(input_path, output_dir="output", alignment=align)
             
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
        # Standalone Hook Effects
        input_path = select_video_file("Video para Agregar Hooks")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
            
        console.print(f"[bold green]✅ Video: {os.path.basename(input_path)}[/]")
        effect = get_entry_effect_choice()
        
        if not effect: return

        final_path, temp_path = get_save_path(input_path, f"hook_{effect}")
        write_path = temp_path if temp_path else final_path
        
        try:
            # Standalone effect application
            from moviepy.editor import VideoFileClip, CompositeVideoClip
            from src.core.effects import apply_effect_to_clip
            
            with console.status("[bold yellow]✨ Aplicando efecto Hook...[/]", spinner="dots"):
                clip = VideoFileClip(input_path)
                
                # Apply effect
                # Note: effects assume resizing logic.
                final = apply_effect_to_clip(clip, effect, size=clip.size, final_y_pos=0)
                
                # Wrap in composite to respect set_position if implicit
                final_comp = CompositeVideoClip([final], size=clip.size).set_duration(clip.duration)
                
                final_comp.write_videofile(
                    write_path, fps=30, codec="libx264", audio_codec="aac", preset="fast", verbose=False, logger=None
                )
                clip.close()
                final_comp.close()
            
            finalize_output(temp_path, final_path)
            console.print(f"[bold green]✨ Video mejorado listo: {final_path}[/]")
            
        except ImportError:
            console.print("[bold red]❌ Error importando moviepy/src.[/]")
        except Exception as e:
            console.print(f"[bold red]❌ Error al aplicar efecto: {e}[/]")
            import traceback
            traceback.print_exc()
            
        Prompt.ask("Presiona Enter para volver...")
        return

    elif mode == '6':
        # Add Background Music
        input_path = select_video_file("Video para Agregar Música")
        if not input_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
        
        console.print(f"[bold green]✅ Video seleccionado: {os.path.basename(input_path)}[/]")
        
        # Select music
        music_path = select_music_file()
        if not music_path:
            Prompt.ask("\nPresiona Enter para volver...")
            return
        
        console.print(f"[bold cyan]🎵 Música seleccionada: {os.path.basename(music_path)}[/]")
        
        # Ask for music volume
        console.print("\n[bold yellow]🔊 Volumen de música de fondo:[/]")
        console.print("  [dim]0.1 = Muy suave (10%)[/]")
        console.print("  [dim]0.3 = Suave (30%) - Recomendado[/]")
        console.print("  [dim]0.5 = Medio (50%)[/]")
        console.print("  [dim]0.7 = Alto (70%)[/]")
        
        volume_input = Prompt.ask("Ingresa volumen", default="0.3")
        try:
            music_volume = float(volume_input)
            music_volume = max(0.0, min(1.0, music_volume))  # Clamp between 0-1
        except ValueError:
            music_volume = 0.3
        
        # Get save path
        final_path, temp_path = get_save_path(input_path, "music")
        write_path = temp_path if temp_path else final_path
        
        try:
            from src.core.audio import add_background_music_overlay
            
            with console.status("[bold magenta]🎵 Aplicando música de fondo...[/]", spinner="dots"):
                add_background_music_overlay(
                    video_path=input_path,
                    music_path=music_path,
                    output_path=write_path,
                    music_volume=music_volume
                )
            
            finalize_output(temp_path, final_path)
            console.print(f"[bold green]✨ Video con música listo: {final_path}[/]")
            
        except ImportError as e:
            console.print(f"[bold red]❌ Error importando módulo de audio: {e}[/]")
        except Exception as e:
            console.print(f"[bold red]❌ Error al añadir música: {e}[/]")
            import traceback
            traceback.print_exc()
        
        Prompt.ask("Presiona Enter para volver...")
        return

    # Options (Only for Mode 1 & 2)
    console.print("\n[bold yellow]Configuración del Trabajo:[/]")

    use_subs = Confirm.ask("📜 ¿Quieres quemar subtítulos en el video?", default=False)
    
    align = "bottom"
    if use_subs:
        align = Prompt.ask("📍 Posición de subtítulos", choices=["bottom", "middle", "top"], default="bottom")
    
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
            skip_analysis=skip_analysis
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

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        sys.exit(0)
