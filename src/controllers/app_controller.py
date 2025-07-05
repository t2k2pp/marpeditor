from typing import Optional, Any
from pathlib import Path
from threading import Timer
from dataclasses import dataclass
import tkinter.filedialog as filedialog

from src.models.app_state import AppState
from src.services.marp_engine import MarpEngine
from src.services.file_manager import FileManager
from typing import List # Add List

# Placeholder for MainAppView, SettingsManager, ExportOptions
class MainAppView: 
    def update_status(self, message: str, char_count: int = 0, line_count: int = 0): pass
    def set_editor_content(self, content: str): pass
    def get_editor_content(self) -> str: pass
    # def update_previews_panel(self, image_data: List[bytes], aspect_ratio: str): pass # Method removed from MainAppView
    def update_theme_selection(self, themes: list, selected_theme: str): pass
    def update_slide_list(self, slides: list, current_slide_index: int, slide_images: List[bytes]): pass # Added slide_images
    def enter_presentation_mode(self): pass
    def exit_presentation_mode(self): pass
    def open_popup_window(self, html_content: str): pass
    def close_popup_window(self): pass
    def update_popup_window_content(self, html_content: str): pass

class SettingsManager: pass

@dataclass
class ExportOptions:
    pass

class AppController:
    def __init__(self):
        self.state = AppState()
        self.view: Optional[MainAppView] = None
        self.marp_engine = MarpEngine()
        self.file_manager = FileManager()
        self.settings_manager = SettingsManager()
        self.auto_save_timer: Optional[Timer] = None
        self.preview_update_timer: Optional[Timer] = None
        self.last_rendered_slide_images: List[bytes] = []
        
        # Initialize available themes from MarpEngine
        self.state.available_themes = self.marp_engine.get_available_themes()
        if self.state.available_themes and self.state.selected_theme not in self.state.available_themes:
            self.state.selected_theme = self.state.available_themes[0]

    def create_new_document(self) -> bool:
        if self.state.is_document_modified:
            if not self._confirm_save():
                return False
        self.state.markdown_content = ""
        self.state.html_content = ""
        self.state.current_file_path = None
        self.state.is_document_modified = False
        self.state.status_message = "New document created."
        self.state.slide_count = 0
        self.state.current_slide_index = 1 # Should be 0 or 1, ensure consistency later
        self.state.slides_data = []
        self.last_rendered_slide_images = []
        if self.view:
            self.view.set_editor_content("")
            # self.view.update_previews_panel([], self.state.aspect_ratio) # Removed
            self.view.update_status(self.state.status_message, 0, 0)
            self.view.update_slide_list(self.state.slides_data, self.state.current_slide_index, self.last_rendered_slide_images)
            if self.state.is_popup_window_open: # Close popup if open
                self.view.close_popup_window()
        return True
    
    def open_document(self, file_path: Optional[Path] = None) -> bool:
        if self.state.is_document_modified:
            if not self._confirm_save():
                return False

        if not file_path:
            file_path_str = filedialog.askopenfilename(
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md *.markdown"), ("Text files", "*.txt"), ("All files", "*.* ")]
            )
            if not file_path_str:
                return False
            file_path = Path(file_path_str)

        content = self.file_manager.read_file(file_path)
        if content is not None:
            self.state.markdown_content = content
            self.state.current_file_path = file_path
            self.state.is_document_modified = False
            self.state.status_message = f"Opened: {file_path.name}"
            
            self.state.slides_data = self.marp_engine.extract_slides(self.state.markdown_content)
            self.state.slide_count = len(self.state.slides_data)
            self.state.current_slide_index = 1
            self.last_rendered_slide_images = []

            if self.view:
                self.view.set_editor_content(content)
                self._schedule_preview_update(force=True) # This will also update slide list and popup
                self.view.update_status(self.state.status_message, len(content), content.count('\n') + 1)
            return True
        else:
            self.state.status_message = f"Failed to open: {file_path.name}"
            if self.view:
                self.view.update_status(self.state.status_message)
            return False
    
    def save_document(self, file_path: Optional[Path] = None) -> bool:
        if not file_path and self.state.current_file_path:
            file_path = self.state.current_file_path
        
        if not file_path:
            file_path_str = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md *.markdown"), ("All files", "*.* ")]
            )
            if not file_path_str:
                return False
            file_path = Path(file_path_str)

        if file_path:
            success = self.file_manager.write_file(file_path, self.state.markdown_content)
            if success:
                self.state.current_file_path = file_path
                self.state.is_document_modified = False
                self.state.status_message = f"Saved: {file_path.name}"
                if self.view:
                    self.view.update_status(self.state.status_message, len(self.state.markdown_content), self.state.markdown_content.count('\n') + 1)
                return True
            else:
                self.state.status_message = f"Failed to save: {file_path.name}"
                if self.view:
                    self.view.update_status(self.state.status_message)
                return False
        return False
    
    def _confirm_save(self) -> bool:
        # Placeholder for a dialog asking user to save changes
        # For now, just return True to proceed without saving
        return True

    def close_document(self) -> bool:
        """ドキュメントを閉じる（保存確認含む）"""
        return True
    
    def import_document(self, file_path: Path, file_type: str) -> bool:
        """他形式からのインポート"""
        return True

    def on_content_changed(self, new_content: str) -> None:
        """エディタ内容変更時の処理"""
        self.state.markdown_content = new_content
        self.state.is_document_modified = True

        new_slides_data = self.marp_engine.extract_slides(self.state.markdown_content)
        if new_slides_data != self.state.slides_data:
            self.state.slides_data = new_slides_data
            self.state.slide_count = len(self.state.slides_data)
            if self.state.slide_count > 0 and self.state.current_slide_index > self.state.slide_count:
                self.state.current_slide_index = self.state.slide_count
            elif self.state.slide_count == 0:
                self.state.current_slide_index = 0

        if self.state.is_live_preview_enabled:
            if self.preview_update_timer:
                self.preview_update_timer.cancel()
            self.preview_update_timer = Timer(self.state.debounce_delay, self._schedule_preview_update)
            self.preview_update_timer.start()
        elif self.preview_update_timer:
            self.preview_update_timer.cancel()

        if self.view:
            # Update slide list with metadata first (no images yet)
            self.view.update_slide_list(self.state.slides_data, self.state.current_slide_index, [])
            self.view.update_status(self.state.status_message, len(new_content), new_content.count('\n') + 1)
        
    def toggle_live_preview(self, enabled: bool) -> None:
        """ライブプレビューの有効/無効切り替え"""
        self.state.is_live_preview_enabled = enabled
        if self.view: # Update settings UI
            self.view.after(0, lambda: self.view.side_panel.update_settings_ui())

        if not enabled and self.preview_update_timer: # If live preview is disabled, cancel any pending timer
            self.preview_update_timer.cancel()
        elif enabled:
            self._schedule_preview_update(force=True) # If enabled, force update preview
        
    def set_debounce_delay(self, delay: float) -> None:
        """Sets the debounce delay for preview updates."""
        self.state.debounce_delay = delay
        if self.view: # Update settings UI
            self.view.after(0, lambda: self.view.side_panel.update_settings_ui())

    def _schedule_preview_update(self, force: bool = False) -> None:
        """Schedules the preview update to run on the main Tkinter thread."""
        if self.view:
            # Pass force as an argument to update_preview
            self.view.after(0, lambda: self.update_preview(force=force))

    def update_preview(self, force: bool = False) -> None:
        """プレビューの更新 (UI操作はメインスレッドで行われる想定)"""
        if not self.state.is_live_preview_enabled and not force: # If live preview is off and not a forced update, do nothing
            if self.view: # Still ensure to clear preview if it was forced off
                 if self.state.is_presentation_mode:
                    if hasattr(self.view, 'presentation_html_frame') and self.view.presentation_html_frame:
                        self.view.presentation_html_frame.load_html("Live preview is disabled.")
                 # else: # No main preview panel to update with images anymore
                    # self.view.update_previews_panel([], self.state.aspect_ratio)
            return

        if self.state.is_live_preview_enabled or force:
            if self.state.is_presentation_mode:
                rendered_html = self.marp_engine.render_presentation(
                    self.state.markdown_content,
                    self.state.selected_theme,
                    slide_index=self.state.current_slide_index - 1 if self.state.current_slide_index > 0 else None
                )
                if self.view and hasattr(self.view, 'presentation_html_frame') and self.view.presentation_html_frame:
                    self.view.presentation_html_frame.load_html(rendered_html)
            else:
                image_data_list = self.marp_engine.render_slides_as_images(
                    self.state.markdown_content,
                    self.state.selected_theme,
                    self.state.aspect_ratio
                )
                self.last_rendered_slide_images = image_data_list
                if self.view:
                    # self.view.update_previews_panel(self.last_rendered_slide_images, self.state.aspect_ratio) # Removed
                    self.view.update_slide_list(self.state.slides_data, self.state.current_slide_index, self.last_rendered_slide_images)
        else: # Not live preview enabled and not forced
            self.state.html_content = "" # Should this be cleared? If so, where is it used?
            self.last_rendered_slide_images = [] # Clear images if preview is off
            if self.view:
                if self.state.is_presentation_mode: # Clear presentation mode if it was active
                    if hasattr(self.view, 'presentation_html_frame') and self.view.presentation_html_frame:
                        self.view.presentation_html_frame.load_html("Live preview is disabled.")
                # No main preview panel to clear
                self.view.update_slide_list(self.state.slides_data, self.state.current_slide_index, self.last_rendered_slide_images) # Update slide list with no images
            # self.update_popup_window_if_open() # Update popup as well # This is already called at the end of the outer if/else

        self.update_popup_window_if_open() # Ensure popup is updated regardless of preview state if content changed

    def set_aspect_ratio(self, aspect_ratio: str) -> None:
        self.state.aspect_ratio = aspect_ratio
        self._schedule_preview_update(force=True)
        
    def apply_theme(self, theme_name: str) -> None:
        """テーマの適用"""
        self.state.selected_theme = theme_name
        self._schedule_preview_update(force=True) # Force update preview with new theme, this will also update popup
        if self.view:
            # This UI update should also be scheduled if it's not already safe
            self.view.after(0, lambda: self.view.update_theme_selection(self.state.available_themes, self.state.selected_theme))
        
    def insert_slide_break(self, position: int) -> None:
        """スライド区切りの挿入"""
        pass

    def navigate_to_slide(self, slide_index: int) -> bool:
        """指定スライドへの移動"""
        if 1 <= slide_index <= self.state.slide_count:
            self.state.current_slide_index = slide_index
            self._schedule_preview_update(force=True) # This will also update slide list and popup
            return True
        elif self.state.slide_count == 0 and slide_index == 0: # Allow navigating to 0 if no slides
            self.state.current_slide_index = 0
            self._schedule_preview_update(force=True)
            return True
        return False
    
    def navigate_slide(self, direction: str) -> bool:
        """スライドナビゲーション（'prev'/'next'）"""
        if direction == 'next':
            return self.navigate_to_slide(self.state.current_slide_index + 1)
        elif direction == 'prev':
            return self.navigate_to_slide(self.state.current_slide_index - 1)
        return False
    
    def enter_presentation_mode(self) -> None:
        """プレゼンテーションモードに入る"""
        if self.view:
            self.view.enter_presentation_mode()
    
    def exit_presentation_mode(self) -> None:
        """プレゼンテーションモードを終了"""
        if self.view:
            self.view.exit_presentation_mode()
    
    def toggle_speaker_notes(self, visible: bool) -> None:
        """スピーカーノートの表示切り替え"""
        pass

    def export_html(self, output_path: Optional[Path] = None, options: Optional[ExportOptions] = None) -> bool:
        """HTMLファイルとしてエクスポート"""
        if not output_path:
            file_path_str = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.* ")]
            )
            if not file_path_str:
                self.state.status_message = "HTML export cancelled."
                if self.view: self.view.update_status(self.state.status_message)
                return False
            output_path = Path(file_path_str)

        success = self.file_manager.write_file(output_path, self.state.html_content)
        if success:
            self.state.status_message = f"HTML exported to: {output_path.name}"
            if self.view: self.view.update_status(self.state.status_message, len(self.state.markdown_content), self.state.markdown_content.count('\n') + 1)
            return True
        else:
            self.state.status_message = f"Failed to export HTML to: {output_path.name}"
            if self.view: self.view.update_status(self.state.status_message)
            return False
    
    def export_pdf(self, output_path: Path, options: ExportOptions) -> bool:
        """PDFファイルとしてエクスポート"""
        return True
    
    def export_images(self, output_dir: Path, options: ExportOptions) -> bool:
        """画像ファイルとしてエクスポート""" 
        return True
    
    def export_pptx(self, output_path: Path, options: ExportOptions) -> bool:
        """PowerPointファイルとしてエクスポート"""
        return True

    def toggle_popup_window(self):
        if not self.view:
            return

        if self.state.is_popup_window_open:
            self.view.close_popup_window()
            # self.state.is_popup_window_open is set to False in view's close_popup_window
        else:
            if self.state.slide_count > 0 and self.state.current_slide_index > 0:
                html_content = self.marp_engine.render_presentation(
                    self.state.markdown_content,
                    self.state.selected_theme,
                    slide_index=self.state.current_slide_index -1 # MarpEngine uses 0-based index
                )
                self.view.open_popup_window(html_content)
                # self.state.is_popup_window_open is set to True in view's open_popup_window
            elif self.state.slide_count == 0 :
                 self.view.open_popup_window("<html><body>No slides to display.</body></html>")
            # If current_slide_index is 0 (e.g. after creating new doc), don't open

    def update_popup_window_if_open(self):
        if self.view and self.state.is_popup_window_open:
            if self.state.slide_count > 0 and self.state.current_slide_index > 0:
                html_content = self.marp_engine.render_presentation(
                    self.state.markdown_content,
                    self.state.selected_theme,
                    slide_index=self.state.current_slide_index - 1 # MarpEngine uses 0-based index
                )
                self.view.update_popup_window_content(html_content)
            elif self.state.slide_count == 0:
                 self.view.update_popup_window_content("<html><body>No slides to display.</body></html>")
            # If current_slide_index is 0, perhaps clear or show a message
            # For now, it will retain the last valid slide if current_slide_index becomes invalid temporarily
            # This behavior is refined by the checks above.
