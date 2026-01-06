"""
Main Entry Point
Dependency wiring and CLI launch.
This is imported by start_worker.py after bootstrap.
"""

def main():
    """
    Main application entry point.
    Wires dependencies and launches CLI.
    """
    # Multi-language setup
    from src.translations.manager import get_translator
    translator = get_translator()
    
    # Check if first time or settings missing
    if not translator.settings_file.exists():
        from rich.console import Console
        from rich.prompt import Prompt
        console = Console()
        console.print("\n[bold cyan]🌐 Language Selection / Selección de Idioma[/]")
        lang = Prompt.ask("Choose your language / Elige tu idioma", choices=["en", "es"], default="en")
        translator.set_language(lang)
    
    # Import CLI menu - done inside function to avoid startup circular imports
    from src.cli.menu import main_menu
    
    # Launch interactive menu
    main_menu()


# Backward compatibility exports
# These allow existing code (like start_worker.py or tests) to import from src.main
# effectively making src/main.py a facade for the new modular architecture.
try:
    from src.workflows.pipeline import run_pipeline
    from src.workflows.use_cases import run_subtitles_only, remove_video_silences
except ImportError:
    # If run standalone or strictly for CLI, these might not be needed immediately,
    # but practically they should exist.
    pass

__all__ = ['main', 'run_pipeline', 'run_subtitles_only', 'remove_video_silences']
