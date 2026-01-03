"""
CLI Helper Functions
Extracted from start_worker.py for separation of concerns.
Handles file selection, path management, and user input utilities.
"""
import os
import time
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt

console = Console()


from src.shared.config import get_config

def select_video_file(prompt="Selecciona Video de Entrada"):
    """
    Allows selecting a video from 'input' or 'output' folder with list selection.
    """
    console.print(f"\n[bold cyan]📂 {prompt}:[/]")
    console.print("1. [green]Carpeta Input[/] (Nuevos videos)")
    console.print("2. [yellow]Carpeta Output[/] (Videos ya procesados)")
    
    source = Prompt.ask("Fuente", choices=["1", "2"], default="1")
    
    config = get_config()
    
    if source == '1':
        # Input Dir Logic - ALWAYS show list for multiple files
        input_dir = config.input_dir
        # No need to makedirs here as config does it, but safe to keep or rely on config validation
        
        valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
        # os.listdir works with Path objects in recent Python, but explicit str cast is safer for older versions if needed
        # However, config paths are Path objects.
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
                return str(input_dir / files[0])
            else:
                return None
        else:
            console.print(f"\n[bold green]📹 Videos disponibles en Input:[/]")
            for idx, f in enumerate(files):
                console.print(f"[bold cyan]{idx+1}.[/] {f}")
            choice = IntPrompt.ask("Elige el número", choices=[str(i+1) for i in range(len(files))])
            return str(input_dir / files[choice-1])

    else:
        # Output Dir Logic
        output_dir = config.output_dir
        valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
        files = [f for f in os.listdir(output_dir) if f.lower().endswith(valid_exts)]
        
        if not files:
            console.print(f"[bold red]❌ La carpeta 'output' está vacía.[/]")
            return None
            
        console.print(f"\n[bold yellow]📹 Videos en Output:[/]")
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(output_dir / x), reverse=True)
        
        for idx, f in enumerate(files):
            console.print(f"[bold cyan]{idx+1}.[/] {f}")
            
        choice = IntPrompt.ask("Elige el video para procesar", choices=[str(i+1) for i in range(len(files))])
        return str(output_dir / files[choice-1])


def select_media_file():
    """
    Selects a background video from 'media' directory with list selection.
    """
    config = get_config()
    media_dir = config.media_dir
    
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
    return str(media_dir / files[choice-1])


def select_music_file():
    """
    Selects a music file from 'music' directory with list selection.
    """
    config = get_config()
    music_dir = config.music_dir
    
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
    return str(music_dir / files[choice-1])


def get_save_path(input_path, default_suffix, output_dir=None):
    """
    Determines output path, allowing overwrite of input or other files.
    Returns (final_path, temp_path) tuple.
    temp_path is not None when overwriting to avoid data loss.
    """
    config = get_config()
    # If output_dir is "output" (legacy default from caller) or None, use config
    if output_dir is None or output_dir == "output":
        output_dir = config.output_dir
    else:
        output_dir = Path(output_dir)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    default_name = f"{base_name}_{default_suffix}.mp4"
    default_path = output_dir / default_name
    
    # PATH VALIDATION LOGIC
    abs_input = os.path.abspath(input_path)
    abs_input_dir = os.path.abspath(config.input_dir)
    
    # CASE A: Input is from 'input' folder -> Force Save as New
    if abs_input.startswith(abs_input_dir):
        console.print(f"\n[dim]ℹ️  El archivo de origen está en 'input'. Guardando como nuevo archivo.[/]")
        # Ensure unique name
        final_path = _get_unique_path(default_path)
        if final_path != default_path:
             console.print(f"[dim]⚠️  El nombre ya existía. Guardando como: {os.path.basename(final_path)}[/]")
        return str(final_path), None

    console.print(f"\n[bold yellow]💾 ¿Cómo quieres guardar el resultado?[/]")
    console.print(f"1. [green]Guardar como Nuevo[/]: {default_name}")
    console.print(f"2. [red]Sobrescribir Entrada[/]: {os.path.basename(input_path)}")
    console.print(f"3. [cyan]Sobrescribir Otro...[/] (Seleccionar manual)")
    
    choice = Prompt.ask("Opción de guardado", choices=["1", "2", "3"], default="1")
    
    target_path = str(default_path)
    
    if choice == '1':
        # Save as New -> Ensure unique
        target_path = str(_get_unique_path(default_path))
        if Path(target_path).name != default_name:
             console.print(f"[dim]⚠️  El nombre ya existía. Se guardará como: {os.path.basename(target_path)}[/]")
        return target_path, None
        
    elif choice == '2':
        target_path = input_path
        
    elif choice == '3':
        # List output files
        valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
        files = [f for f in os.listdir(output_dir) if f.lower().endswith(valid_exts)]
        files.sort(key=lambda x: os.path.getmtime(output_dir / x), reverse=True)
        
        if not files:
            console.print("[red]No hay archivos para sobrescribir. Usando automático.[/]")
        else:
            for idx, f in enumerate(files):
                console.print(f"{idx+1}. {f}")
            sel = IntPrompt.ask("Elige archivo a sobrescribir", choices=[str(i+1) for i in range(len(files))])
            target_path = str(output_dir / files[sel-1])
            
    # Collision handling (Only for Overwrite modes)
    if os.path.abspath(target_path) == os.path.abspath(input_path):
        console.print("[dim]✏️  Se sobrescribirá el archivo original al finalizar.[/]")
        timestamp = int(time.time())
        temp_path = str(output_dir / f"temp_{timestamp}_{os.path.basename(target_path)}")
        return target_path, temp_path
        
    if os.path.exists(target_path):
         console.print(f"[yellow]⚠️  El archivo {os.path.basename(target_path)} será reemplazado.[/]")
         timestamp = int(time.time())
         temp_path = str(output_dir / f"temp_{timestamp}_{os.path.basename(target_path)}")
         return target_path, temp_path

    return target_path, None


def _get_unique_path(path_obj: Path) -> Path:
    """
    If path exists, append _1, _2, etc. until unique.
    """
    if not path_obj.exists():
        return path_obj
        
    stem = path_obj.stem
    suffix = path_obj.suffix
    parent = path_obj.parent
    
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


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
    """
    Selects a file from input directory.
    If multiple files exist, allows user to choose one.
    """
    config = get_config()
    input_dir = config.input_dir
    
    valid_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]
    
    if len(files) == 0:
        console.print(f"[bold red]❌ La carpeta 'input' está vacía.[/]")
        console.print(f"[yellow]👉 Por favor, coloca videos en: {input_dir}[/]")
        return None
        
    if len(files) == 1:
        console.print(f"[bold green]📹 Video disponible: {files[0]}[/]")
        return str(input_dir / files[0])
    
    # Allow selection if multiple
    console.print(f"\n[bold green]📹 Videos disponibles en Input:[/]")
    for idx, f in enumerate(files):
        console.print(f"[bold cyan]{idx+1}.[/] {f}")
    
    choice = IntPrompt.ask("Elige el video a procesar", choices=[str(i+1) for i in range(len(files))])
    return str(input_dir / files[choice-1])


def get_entry_effect_choice():
    """Helper to ask for effect"""
    if not Confirm.ask("✨ ¿Quieres agregar un efecto de entrada 'Hook'?", default=False):
        return None
        
    console.print("\n[bold magenta]Selecciona un Efecto de Entrada:[/]")
    console.print("1. [cyan]Zoom Punch + Focus[/] (Estilo TikTok clásico)")
    console.print("2. [cyan]Flash In + Punch[/] (Agresivo)")
    console.print("3. [cyan]Slide In Top + Zoom[/] (Gaming/Dinámico)")
    
    return Prompt.ask("Opción", choices=["1", "2", "3"], default="1")


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')
