from typing import Optional, Any
from pathlib import Path
from threading import Timer
from dataclasses import dataclass
import tkinter.filedialog as filedialog

from src.models.app_state import AppState
from src.services.marp_engine import MarpEngine
from src.services.file_manager import FileManager

# Placeholder for MainAppView, SettingsManager, ExportOptions
class MainAppView: 
    def update_status(self, message: str, char_count: int = 0, line_count: int = 0): pass
    def set_editor_content(self, content: str): pass
    def get_editor_content(self) -> str: pass
    def update_preview_panel(self, html_content: str): pass
    def update_theme_selection(self, themes: list, selected_theme: str): pass
    def update_slide_list(self, slides: list, current_slide_index: int): pass
    def enter_presentation_mode(self): pass
    def exit_presentation_mode(self): pass

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
        self.state.current_slide_index = 1
        self.state.slides_data = []
        if self.view:
            self.view.set_editor_content("")
            self.view.update_preview_panel("")
            self.view.update_status(self.state.status_message, 0, 0)
            self.view.update_slide_list(self.state.slides_data, self.state.current_slide_index)
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
            self.state.current_slide_index = 1 # Reset to first slide on open

            if self.view:
                self.view.set_editor_content(content)
                self.update_preview(force=True)
                self.view.update_status(self.state.status_message, len(content), content.count('\n') + 1)
                self.view.update_slide_list(self.state.slides_data, self.state.current_slide_index)
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

        # Update slide data and count
        self.state.slides_data = self.marp_engine.extract_slides(self.state.markdown_content)
        self.state.slide_count = len(self.state.slides_data)
        # Ensure current slide index is valid
        if self.state.slide_count > 0 and self.state.current_slide_index > self.state.slide_count:
            self.state.current_slide_index = self.state.slide_count
        elif self.state.slide_count == 0:
            self.state.current_slide_index = 0

        # Debounce preview update
        if self.preview_update_timer:
            self.preview_update_timer.cancel()
        
        self.preview_update_timer = Timer(0.2, self.update_preview) # 200ms delay
        self.preview_update_timer.start()

        if self.view:
            self.view.update_slide_list(self.state.slides_data, self.state.current_slide_index)
            self.view.update_status(self.state.status_message, len(new_content), new_content.count('\n') + 1)
        
    def toggle_live_preview(self, enabled: bool) -> None:
        """ライブプレビューの有効/無効切り替え"""
        self.state.is_live_preview_enabled = enabled
        self.update_preview() # Update preview when toggling live preview
        
    def update_preview(self, force: bool = False) -> None:
        """プレビューの更新"""
        if self.state.is_live_preview_enabled or force:
            if self.state.is_presentation_mode:
                rendered_html = self.marp_engine.render_presentation(
                    self.state.markdown_content,
                    self.state.selected_theme,
                    slide_index=self.state.current_slide_index - 1 if self.state.current_slide_index > 0 else None
                )
                if self.view:
                    self.view.presentation_html_frame.load_html(rendered_html)
            else:
                image_data = self.marp_engine.render_slides_as_images(
                    self.state.markdown_content,
                    self.state.selected_theme,
                    self.state.aspect_ratio
                )
                if self.view:
                    self.view.update_previews_panel(image_data, self.state.aspect_ratio)
        else:
            self.state.html_content = ""
            if self.view:
                if self.state.is_presentation_mode:
                    self.view.presentation_html_frame.load_html("Live preview is disabled.")
                else:
                    self.view.update_previews_panel([], self.state.aspect_ratio)
        
    def set_aspect_ratio(self, aspect_ratio: str) -> None:
        self.state.aspect_ratio = aspect_ratio
        self.update_preview(force=True)
        
    def apply_theme(self, theme_name: str) -> None:
        """テーマの適用"""
        self.state.selected_theme = theme_name
        self.update_preview(force=True) # Force update preview with new theme
        if self.view:
            self.view.update_theme_selection(self.state.available_themes, self.state.selected_theme)
        
    def insert_slide_break(self, position: int) -> None:
        """スライド区切りの挿入"""
        pass

    def navigate_to_slide(self, slide_index: int) -> bool:
        """指定スライドへの移動"""
        if 1 <= slide_index <= self.state.slide_count:
            self.state.current_slide_index = slide_index
            self.update_preview(force=True)
            if self.view:
                self.view.update_slide_list(self.state.slides_data, self.state.current_slide_index)
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
