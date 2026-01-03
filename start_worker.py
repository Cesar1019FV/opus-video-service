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
        ('rich.console', 'rich')  # Check specific submodule for rich
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
# Delegate to CLI
# ---------------------------------------------------------
if __name__ == "__main__":
    try:
        from src.main import main
        main()
    except KeyboardInterrupt:
        sys.exit(0)
