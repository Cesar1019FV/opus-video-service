"""
Main CLI Menu Interface
Extracted from start_worker.py for clean separation.
Handles the Rich interactive menu and all user workflows.
"""
import os
import sys

# Suppress OpenCV logs to avoid terminal flickering
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["OPENCV_VIDEOIO_LOG_LEVEL"] = "SILENT"

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

from src.translations.manager import get_translator
t = get_translator().t

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
    
    subtitle = Text(f"\n{t('menu_subtitle')}", style="bold white")
    
    console.print(Align.center(title))
    console.print(Align.center(subtitle))
    console.print(Align.center(Text(f"v1.0.0 | {t('powered_by')}", style="dim")))
    console.print("\n")


def main_menu():
    """Main interactive menu loop"""
    while True:
        show_banner()
        
        menu_text = f"""
{t('menu_option_1')}
{t('menu_option_2')}
{t('menu_option_3')}
{t('menu_option_4')}
{t('menu_option_5')}
{t('menu_option_6')}
{t('menu_option_7')}
{t('menu_option_8')}
{t('menu_option_9')}
{t('menu_option_10')}
{t('menu_option_11')}
{t('menu_option_12')}
{t('menu_option_13')}
        """
        
        console.print(Panel(menu_text, title=t("menu_title"), border_style="blue", expand=False))
        
        choice = Prompt.ask(t("select_option"), choices=[str(i+1) for i in range(13)], default="2")
        
        if choice == '13':
            console.print(t("exit_msg"))
            sys.exit(0)
            
        run_job_ui(choice)


def run_editor_ui():
    """Sub-menu for Vertical Formats"""
    while True:
        menu_text = f"""
{t('editor_option_1')}
{t('editor_option_2')}
{t('editor_option_3')}
{t('editor_option_4')}
        """
        console.print(Panel(menu_text, title=t("editor_title"), border_style="magenta", expand=False))
        
        choice = Prompt.ask(t("select_option"), choices=["1", "2", "3", "4"], default="1")
        
        if choice == '4':
            return  # Back to main menu
            
        input_path = select_video_file(t("editor_title"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            continue
            
        if choice == '1':  # Split Screen
            # Select background Media
            media_path = select_media_file()
            if not media_path:
                Prompt.ask("\nPresiona Enter para volver...")
                continue

            console.print(t("video_principal_ready", file=os.path.basename(input_path)))
            console.print(t("video_fondo_ready", file=os.path.basename(media_path)))
            
            final_path, temp_path = get_save_path(input_path, "split")
            write_path = temp_path if temp_path else final_path
            
            if not Confirm.ask(t("render_confirm"), default=True): 
                continue
            
            try:
                from src.features.editing.split_screen import make_vertical_split_video
                with console.status(t("rendering"), spinner="bouncingBall"):
                    make_vertical_split_video(input_path, media_path, write_path)
                
                finalize_output(temp_path, final_path)
                console.print(t("video_ready", path=final_path))
            except Exception as e:
                console.print(t("error", error=e))
                
        elif choice == '2':  # Blur Vert
            # 1. Ask for Title Gen
            title_text = ""
            use_ai_title = Confirm.ask(t("blur_ask_ai_title"), default=True)
            
            if use_ai_title:
                try:
                    # Check for transcript or generate one
                    from src.features.transcription.service import transcribe_video
                    from src.features.viral_clips.service import generate_viral_title
                    
                    with console.status(t("blur_transcribing"), spinner="dots"):
                         # We use a fast model just for the text context
                         transcript_data = transcribe_video(input_path, model_size="tiny", device="cpu")
                         
                    with console.status(t("blur_generating_titles"), spinner="earth"):
                        titles = generate_viral_title(transcript_data['text'])
                        
                    if titles:
                        console.print(t("social_suggested_titles"))
                        for i, t_opt in enumerate(titles):
                            console.print(f"{i+1}. {t_opt}")
                        console.print(f"{len(titles)+1}. [{t('manual_input')}]")
                        
                        sel = IntPrompt.ask(t("choose_title"), choices=[str(i+1) for i in range(len(titles)+1)], default=1)
                        
                        if sel <= len(titles):
                            title_text = titles[sel-1]
                        else:
                            title_text = Prompt.ask(t("manual_title_prompt"))
                    else:
                        console.print(t("error_ai_titles"))
                        title_text = Prompt.ask(t("manual_title_obs"))
                        
                except Exception as e:
                    console.print(t("error", error=e))
                    title_text = Prompt.ask(t("manual_title_obs"))
            else:
                title_text = Prompt.ask(t("manual_title_obs"))
                
            if not title_text: 
                continue
            
            # Style for title
            title_style = get_subtitle_style_choice()
            
            try:
                from src.workflows.use_cases import convert_to_vertical_blur
                with console.status(t("rendering"), spinner="bouncingBall"):
                    convert_to_vertical_blur(input_path, write_path, title_text, style_name=title_style)
                
                finalize_output(temp_path, final_path)
                console.print(t("video_ready", path=final_path))
            except Exception as e:
                 console.print(t("error", error=e))

        elif choice == '3':  # Smart Crop Full Video
            console.print(t("smart_crop_mode"))
            
            try:
                from src.main import run_pipeline
                with console.status(t("smart_crop_rendering"), spinner="bouncingBall"):
                    run_pipeline(
                        input_path=input_path,
                        output_dir="assets/output",
                        use_subs=False,
                        skip_analysis=True, # Process whole video
                        alignment="bottom",
                        single_word=False,
                        style_name="default"
                    )
                
                console.print(t("convert_success"))
            except Exception as e:
                console.print(t("error", error=e))

        Prompt.ask(t("press_enter_continue"))


def run_job_ui(mode):
    """Handle the selected menu option"""
    url = None
    input_path = None
    
    if mode == '1':
        # Download Video (Generic)
        console.print(t("download_platform_title"))
        console.print(t("download_platform_yt"))
        console.print(t("download_platform_tt"))
        
        platform_choice = Prompt.ask(t("choose_platform"), choices=["1", "2"], default="1")
        
        platform_name = "YouTube" if platform_choice == '1' else "TikTok"
        url = Prompt.ask(t("paste_url", platform=platform_name))
        
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
                
            console.print(t("download_success"))
            console.print(f"[cyan]{video_path}[/]")
            console.print(t("download_next_step"))
            
        except Exception as e:
            console.print(t("download_error", error=e))
            
        Prompt.ask(t("press_enter_back"))
        return
    
    elif mode in ['2', '3']:
        # Viral Clips (AI Analysis)
        input_path = get_video_from_input_dir()
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
        
        # New options: Count and Duration
        target_count = IntPrompt.ask(t("viral_count_prompt"), default=0)
        target_duration = IntPrompt.ask(t("viral_duration_prompt"), default=60)
        
        vertical_format = (mode == '2')
        console.print(Panel(t("viral_start"), style="bold green"))
        
        try:
            from src.main import run_pipeline
            run_pipeline(
                input_path=input_path,
                output_dir="assets/output",
                skip_analysis=False,
                vertical_format=vertical_format,
                target_count=target_count,
                target_duration=target_duration
            )
        except Exception as e:
            console.print(t("error", error=e))
            
        console.print(t("viral_success"))
        Prompt.ask(t("press_enter_back"))
        return
        
    elif mode == '4':
        # Subtitle Only
        input_path = select_video_file(t("subs_select_video"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
        
        console.print(t("subs_selected", file=os.path.basename(input_path)))
        
        align = Prompt.ask(t("subs_position"), choices=["bottom", "middle", "top"], default="bottom")
        
        # Style choice
        console.print(t("subs_style_title"))
        console.print(t("subs_style_phrases"))
        console.print(t("subs_style_dynamic"))
        style_choice = Prompt.ask(t("subs_choose_style"), choices=["1", "2"], default="1")
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
            console.print(t("fatal_error"))
            console.print(e)
            
        console.print(t("viral_success"))
        Prompt.ask(t("press_enter_back"))
        return

    elif mode == '5':
        # Vertical Editor Sub-menu
        run_editor_ui()
        return

    elif mode == '6':
        # Hook Effects Workflow
        input_path = select_video_file(t("hook_select_video"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
            
        effect = get_entry_effect_choice()
        if not effect:
            Prompt.ask(t("press_enter_back"))
            return
            
        final_path, temp_path = get_save_path(input_path, "hook")
        write_path = temp_path if temp_path else final_path
        
        try:
            from src.workflows.use_cases import add_hook_effect_to_video
            add_hook_effect_to_video(input_path, write_path, effect)
            
            finalize_output(temp_path, final_path)
            console.print(t("video_ready", path=final_path))
        except Exception as e:
            console.print(t("error", error=e))
            
        Prompt.ask(t("press_enter_continue"))
        return

    elif mode == '7':
        # Add Music Workflow
        input_path = select_video_file(t("music_select_main"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
            
        music_path = select_music_file()
        if not music_path:
            Prompt.ask(t("press_enter_back"))
            return
            
        vol = Prompt.ask(t("music_vol"), default="0.3")
        try:
            vol = float(vol)
        except:
            vol = 0.3
            
        final_path, temp_path = get_save_path(input_path, "music")
        write_path = temp_path if temp_path else final_path
        
        if not Confirm.ask(t("render_confirm"), default=True): 
            return
            
        try:
            from src.features.audio.service import add_background_music_overlay
            with console.status(t("music_mixing"), spinner="wave"):
                add_background_music_overlay(input_path, music_path, write_path, music_volume=vol)
            
            finalize_output(temp_path, final_path)
            console.print(t("video_ready", path=final_path))
        except Exception as e:
            console.print(t("error", error=e))
            
        Prompt.ask(t("press_enter_continue"))
        return

    elif mode == '8':
        # Video Speed adjustment
        input_path = select_video_file(t("speed_select_video"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
            
        console.print(t("speed_title"))
        console.print(t("speed_opt_1"))
        console.print(t("speed_opt_2"))
        console.print(t("speed_opt_3"))
        console.print(t("speed_opt_4"))
        console.print(t("speed_opt_5"))
        console.print(t("speed_opt_6"))
        console.print(t("speed_opt_7"))
        
        speed_choice = Prompt.ask(t("select_option"), choices=["1", "2", "3", "4", "5", "6", "7"], default="3")
        
        factors = {
            "1": 0.5,
            "2": 0.75,
            "3": 1.1,
            "4": 1.25,
            "5": 1.5,
            "6": 2.0
        }
        
        if speed_choice == "7":
            factor = Prompt.ask(t("speed_custom_input"), default="1.1")
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
            with console.status(t("speed_adjusting", factor=factor), spinner="runner"):
                change_video_speed(input_path, write_path, factor)
                
            finalize_output(temp_path, final_path)
            console.print(t("video_ready", path=final_path))
        except Exception as e:
            console.print(t("error", error=e))
            
        Prompt.ask(t("press_enter_continue"))
        return

    elif mode == '9':
        # Mute video
        input_path = select_video_file(t("mute_select_video"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
            
        final_path, temp_path = get_save_path(input_path, "mute")
        write_path = temp_path if temp_path else final_path
        
        if not Confirm.ask(t("mute_confirm"), default=True):
            return
            
        try:
            from src.features.audio.mute import remove_audio
            with console.status(t("mute_removing"), spinner="dots"):
                remove_audio(input_path, write_path)
                
            finalize_output(temp_path, final_path)
            console.print(t("video_ready", path=final_path))
        except Exception as e:
            console.print(t("error", error=e))
            
        Prompt.ask(t("press_enter_continue"))
        return

    elif mode == '10':
        # Convert to 60fps
        input_path = select_video_file(t("fps_select_video"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
            
        final_path, temp_path = get_save_path(input_path, "60fps")
        write_path = temp_path if temp_path else final_path
        
        try:
            from src.features.effects.fps import convert_to_60fps
            with console.status(t("fps_converting"), spinner="arc"):
                convert_to_60fps(input_path, write_path)
                
            finalize_output(temp_path, final_path)
            console.print(t("video_ready", path=final_path))
        except Exception as e:
            console.print(t("error", error=e))
            
        Prompt.ask(t("press_enter_continue"))
        return
            
    elif mode == '11':
        # Remove Silences
        input_path = select_video_file(t("silence_select_video"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
            
        final_path, temp_path = get_save_path(input_path, "trimmed")
        write_path = temp_path if temp_path else final_path
        
        console.print(t("silence_config_title"))
        duration = Prompt.ask(t("silence_min_duration"), default="1500")
        padding = Prompt.ask(t("silence_padding"), default="500")
        
        try:
            duration = int(duration)
            padding = int(padding)
        except:
            duration = 1500
            padding = 500
            
        if not Confirm.ask(t("silence_confirm"), default=True):
            return
            
        try:
            from src.main import remove_video_silences
            with console.status(t("silence_removing"), spinner="bouncingBall"):
                remove_video_silences(
                    input_path=input_path, 
                    output_path=write_path,
                    silence_duration=duration,
                    padding=padding
                )
                
            finalize_output(temp_path, final_path)
            console.print(t("video_ready", path=final_path))
        except Exception as e:
            console.print(t("error", error=e))
            
        Prompt.ask(t("press_enter_continue"))
        return

    elif mode == '12':
        # Social Media AI Workflow
        input_path = select_video_file(t("social_select_video"))
        if not input_path:
            Prompt.ask(t("press_enter_back"))
            return
            
        try:
            from src.features.transcription.service import transcribe_video
            from src.features.social.service import SocialMediaService
            
            with console.status(t("social_transcribing"), spinner="dots"):
                transcript_data = transcribe_video(input_path, model_size="tiny", device="cpu")
            
            service = SocialMediaService()
            
            # 1. Generate Titles
            with console.status(t("social_generating_titles"), spinner="earth"):
                titles = service.generate_titles(transcript_data['text'])
            
            title_text = ""
            if titles:
                console.print(t("social_suggested_titles"))
                for i, t_opt in enumerate(titles):
                    console.print(f"{i+1}. {t_opt}")
                sel = IntPrompt.ask(t("social_choose_title"), choices=[str(i+1) for i in range(len(titles))], default=1)
                title_text = titles[sel-1]
            else:
                title_text = Prompt.ask(t("social_manual_title"))

            # 2. Generate Descriptions
            with console.status(t("social_generating_desc"), spinner="point"):
                descriptions = service.generate_descriptions(transcript_data['text'], title_text)
            
            if descriptions:
                console.print(t("social_content_ready"))
                console.print(Panel(f"[yellow]TikTok:[/]\n{descriptions.get('tiktok')}\n\n[magenta]Instagram:[/]\n{descriptions.get('instagram')}\n\n[red]YouTube:[/]\n{descriptions.get('youtube')}", title=t("social_panel_title")))
                
                # Save to file
                desc_file = input_path.replace('.mp4', '_social_media.txt')
                with open(desc_file, 'w', encoding='utf-8') as f:
                    f.write(f"TÍTULO SELECCIONADO: {title_text}\n\n")
                    f.write(f"TIKTOK:\n{descriptions.get('tiktok', '')}\n\n")
                    f.write(f"INSTAGRAM:\n{descriptions.get('instagram', '')}\n\n")
                    f.write(f"YOUTUBE:\n{descriptions.get('youtube', '')}\n")
                
                console.print(t("social_saved", file=os.path.basename(desc_file)))
            
        except Exception as e:
            console.print(t("error", error=e))
            
        Prompt.ask(t("press_enter_continue"))
        return

    # Catch-all
    console.print(t("op_not_impl"))
    Prompt.ask(t("press_enter_back"))
