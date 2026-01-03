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
    # Import CLI menu - done inside function to avoid startup circular imports
    from src.cli.menu import main_menu
    
    # Launch interactive menu
    main_menu()


# Backward compatibility exports
# These allow existing code (like start_worker.py or tests) to import from src.main
# effectively making src/main.py a facade for the new modular architecture.
try:
    from src.workflows.pipeline import run_pipeline
    from src.workflows.use_cases import run_subtitles_only
except ImportError:
    # If run standalone or strictly for CLI, these might not be needed immediately,
    # but practically they should exist.
    pass

__all__ = ['main', 'run_pipeline', 'run_subtitles_only']
