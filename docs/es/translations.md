# 🌐 Sistema de Traducciones (i18n)

El sistema de internacionalización de **Opus Video Service** permite que el CLI funcione en múltiples idiomas. Actualmente soporta **English (en)** y **Español (es)**.

## 📂 Estructura de Archivos

La lógica de traducción se encuentra en `src/translations/`:

- `manager.py`: El cerebro del sistema. Carga el idioma seleccionado y proporciona la función `t()` para obtener textos.
- `en.py`: Diccionario maestro con los textos en inglés.
- `es.py`: Diccionario con las traducciones al español.
- `settings.json`: (Autogenerado) Guarda la preferencia de idioma del usuario.

## 🚀 Cómo funciona

1.  **Arranque**: Al ejecutar el programa, el `Translator` lee `settings.json`. Si no existe, lanza un prompt en el CLI para que elijas el idioma.
2.  **Uso en el código**: En cualquier archivo del CLI o shared, importamos el traductor:
    ```python
    from src.translations.manager import get_translator
    t = get_translator().t
    
    # Uso simple
    print(t("menu_title"))
    
    # Uso con variables
    print(t("video_ready", path="/ruta/al/video.mp4"))
    ```

## ➕ Cómo añadir nuevos textos

Si estás creando una nueva funcionalidad y necesitas añadir mensajes:

1.  Abre `src/translations/en.py`.
2.  Añade una nueva clave descriptiva al diccionario `TRANSLATIONS`.
    ```python
    "mi_nueva_funci_prompt": "Ingresa el nombre:",
    ```
3.  Repite el proceso en `src/translations/es.py` con la traducción correspondiente.
4.  Usa `t("mi_nueva_funci_prompt")` en tu código.

## 🌍 Cómo añadir un nuevo idioma

Para añadir, por ejemplo, **Portugués (pt)**:

1.  Crea `src/translations/pt.py` siguiendo el formato de `en.py`.
2.  Modifica `manager.py` para que reconozca "pt" en el método `load_translations`.
3.  Actualiza el prompt inicial en `src/main.py` para incluir "pt" en las opciones de `choices`.

---
> [!TIP]
> **Formateo Rich**: Las cadenas de texto pueden incluir etiquetas de [Rich](https://rich.readthedocs.io/en/stable/appendix/style.html) (ej: `[bold red]Error[/]`) para mantener la estética del CLI.
