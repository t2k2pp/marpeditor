
import customtkinter as ctk
from typing import TYPE_CHECKING, List, Optional
import tkinter
from PIL import Image
import io
import tkinterweb

from pygments.lexers.markup import MarkdownLexer
from pygments.token import Token

# Avoid circular import for type hinting
if TYPE_CHECKING:
    from src.controllers.app_controller import AppController
    from src.models.app_state import SlideData

class EditorPanel(ctk.CTkFrame):
    def __init__(self, parent, controller: 'AppController'):
        super().__init__(parent)
        self.controller = controller

        # Search/Replace Frame
        self.search_frame = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.search_frame.pack(side="top", fill="x", padx=5, pady=5)
        self.search_frame.pack_propagate(False) # Prevent frame from resizing to content
        self.search_frame.pack_forget() # Hide by default

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Find")
        self.search_entry.pack(side="left", padx=(0, 5), expand=True, fill="x")
        self.search_entry.bind("<Return>", lambda event: self._find_next())

        self.find_prev_button = ctk.CTkButton(self.search_frame, text="< Prev", width=60, command=self._find_prev)
        self.find_prev_button.pack(side="left", padx=(0, 5))

        self.find_next_button = ctk.CTkButton(self.search_frame, text="Next >", width=60, command=self._find_next)
        self.find_next_button.pack(side="left", padx=(0, 10))

        self.replace_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Replace with")
        self.replace_entry.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.replace_button = ctk.CTkButton(self.search_frame, text="Replace", width=70, command=self._replace_text)
        self.replace_button.pack(side="left", padx=(0, 5))

        self.replace_all_button = ctk.CTkButton(self.search_frame, text="Replace All", width=90, command=self._replace_all)
        self.replace_all_button.pack(side="left", padx=(0, 5))

        self.close_search_button = ctk.CTkButton(self.search_frame, text="X", width=30, command=self._hide_search_bar)
        self.close_search_button.pack(side="right", padx=(5, 0))

        # Text widget
        self.text_widget = ctk.CTkTextbox(self, wrap="none") # Set wrap to none
        self.text_widget.pack(expand=True, fill="both")
        self.text_widget.configure(font=("Consolas", 12)) # Set monospaced font and size to 12
        self.text_widget.bind("<KeyRelease>", self._on_key_release)
        self.text_widget.bind("<<Modified>>", self._on_text_modified)
        self.text_widget.edit_modified(False)
        self.text_widget.bind("<Control-f>", lambda event: self._show_search_bar())
        self.text_widget.bind("<Control-h>", lambda event: self._show_search_bar())

        self.lexer = MarkdownLexer()

        # Define tag configurations for syntax highlighting
        self.tag_configurations = {
            Token.Keyword: {"foreground": "#0000FF"},  # Blue
            Token.Name.Builtin: {"foreground": "#800080"}, # Purple
            Token.Literal.String: {"foreground": "#A52A2A"}, # Brown
            Token.Literal.Number: {"foreground": "#FF4500"}, # OrangeRed
            Token.Comment: {"foreground": "#008000"}, # Green
            Token.Operator: {"foreground": "#FF0000"}, # Red
            Token.Punctuation: {"foreground": "#808080"}, # Gray
            Token.Generic.Heading: {"foreground": "#00008B", "font": ("Consolas", 12, "bold")}, # DarkBlue, same size as text
            Token.Generic.Emph: {"font": ("Consolas", 12, "italic")},
            Token.Generic.Strong: {"font": ("Consolas", 12, "bold")},
            Token.Generic.Code: {"foreground": "#8B008B"}, # DarkMagenta
            Token.Generic.Error: {"foreground": "#FF0000", "underline": True}, # Red with underline
            Token.Text: {"foreground": "#000000"}, # Black for regular text
        }

        for token_type, config in self.tag_configurations.items():
            self.text_widget._textbox.tag_configure(str(token_type), **config)
        
        # Configure search highlight tag
        self.text_widget._textbox.tag_configure("search_highlight", background="yellow")
        self.last_search_index = "1.0"

    def _on_key_release(self, event):
        self.controller.on_content_changed(self.text_widget.get("1.0", "end-1c"))

    def _on_text_modified(self, event=None):
        if self.text_widget.edit_modified():
            self._apply_syntax_highlighting()
            self.text_widget.edit_modified(False)

    def _apply_syntax_highlighting(self):
        text = self.text_widget.get("1.0", "end-1c")
        for tag_name in self.text_widget._textbox.tag_names():
            if tag_name not in ["sel", "insert", "search_highlight"]:
                self.text_widget._textbox.tag_remove(tag_name, "1.0", "end")

        current_index = "1.0"
        for token_type, value in self.lexer.get_tokens(text):
            tag_name = str(token_type)
            if tag_name in self.tag_configurations:
                start_index = self.text_widget._textbox.index(current_index)
                end_index = self.text_widget._textbox.index(f"{start_index}+{len(value)}c")
                self.text_widget._textbox.tag_add(tag_name, start_index, end_index)
            current_index = f"{current_index}+{len(value)}c"

    def set_content(self, content: str):
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", content)
        self._apply_syntax_highlighting()

    def _show_search_bar(self):
        self.search_frame.pack(side="top", fill="x", padx=5, pady=5)
        self.search_entry.focus_set()
        self._find_text()

    def _hide_search_bar(self):
        self.search_frame.pack_forget()
        self._clear_search_highlights()

    def _clear_search_highlights(self):
        self.text_widget._textbox.tag_remove("search_highlight", "1.0", "end")

    def _find_text(self, start_index="1.0", direction="forward"):
        self._clear_search_highlights()
        search_term = self.search_entry.get()
        if not search_term:
            return

        start_pos = self.text_widget._textbox.search(search_term, start_index, stopindex="end", nocase=True)
        while start_pos:
            end_pos = f"{start_pos}+{len(search_term)}c"
            self.text_widget._textbox.tag_add("search_highlight", start_pos, end_pos)
            start_pos = self.text_widget._textbox.search(search_term, end_pos, stopindex="end", nocase=True)

        first_occurrence = self.text_widget._textbox.search(search_term, "1.0", stopindex="end", nocase=True)
        if first_occurrence:
            self.text_widget._textbox.see(first_occurrence)
            self.last_search_index = first_occurrence

    def _find_next(self):
        search_term = self.search_entry.get()
        if not search_term: return
        
        start_index = f"{self.last_search_index}+{len(search_term)}c"
        next_occurrence = self.text_widget._textbox.search(search_term, start_index, stopindex="end", nocase=True)
        
        if next_occurrence:
            end_pos = f"{next_occurrence}+{len(search_term)}c"
            self._clear_search_highlights()
            self.text_widget._textbox.tag_add("search_highlight", next_occurrence, end_pos)
            self.text_widget._textbox.see(next_occurrence)
            self.last_search_index = next_occurrence
        else:
            self._find_text(start_index="1.0")

    def _find_prev(self):
        search_term = self.search_entry.get()
        if not search_term: return

        prev_occurrence = self.text_widget._textbox.search(search_term, self.last_search_index, stopindex="1.0", backwards=True, nocase=True)
        if prev_occurrence:
            end_pos = f"{prev_occurrence}+{len(search_term)}c"
            self._clear_search_highlights()
            self.text_widget._textbox.tag_add("search_highlight", prev_occurrence, end_pos)
            self.text_widget._textbox.see(prev_occurrence)
            self.last_search_index = prev_occurrence
        else:
            self._find_text(start_index="end", direction="backward")

    def _replace_text(self):
        search_term = self.search_entry.get()
        replace_term = self.replace_entry.get()
        if not search_term or not replace_term: return

        current_selection = self.text_widget._textbox.tag_ranges("search_highlight")
        if current_selection:
            self.text_widget._textbox.delete(current_selection[0], current_selection[1])
            self.text_widget._textbox.insert(current_selection[0], replace_term)
            self.controller.on_content_changed(self.text_widget.get("1.0", "end-1c"))
            self._find_next()

    def _replace_all(self):
        search_term = self.search_entry.get()
        replace_term = self.replace_entry.get()
        if not search_term or not replace_term: return

        text_content = self.text_widget.get("1.0", "end")
        updated_content = text_content.replace(search_term, replace_term)
        self.set_content(updated_content)
        self.controller.on_content_changed(updated_content)

class PreviewPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller: 'AppController'):
        super().__init__(parent)
        self.controller = controller
        self.previews: List[ctk.CTkLabel] = []

    def update_previews(self, image_data: List[bytes], aspect_ratio: str):
        for widget in self.winfo_children():
            widget.destroy()
        self.previews.clear()

        if not image_data:
            ctk.CTkLabel(self, text="Preview not available.").pack(pady=20)
            return

        base_width = 800
        width, height = (base_width, int(base_width * 3/4)) if aspect_ratio == "4:3" else (base_width, int(base_width * 9/16))

        for data in image_data:
            try:
                pil_image = Image.open(io.BytesIO(data))
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(width, height))
                label = ctk.CTkLabel(self, image=ctk_image, text="")
                label.pack(padx=10, pady=10)
                self.previews.append(label)
            except Exception as e:
                print(f"Error displaying image: {e}")
                error_label = ctk.CTkLabel(self, text=f"Error: {e}")
                error_label.pack(padx=10, pady=10)

class SidePanel(ctk.CTkTabview):
    def __init__(self, parent, controller: 'AppController'):
        super().__init__(master=parent)
        self.controller = controller
        self.add("Outline")
        self.add("Slides")
        self.add("Files")
        self.add("Themes")

        ctk.CTkLabel(self.tab("Outline"), text="Outline content").pack(padx=20, pady=20)
        
        self.slides_frame = ctk.CTkScrollableFrame(self.tab("Slides"))
        self.slides_frame.pack(expand=True, fill="both")
        self.slide_buttons: List[ctk.CTkButton] = [] # Consider renaming to slide_widgets if they are not all buttons
        # self.slide_thumbnails: List[ctk.CTkLabel] = [] # Alternative if using labels for images

        ctk.CTkLabel(self.tab("Files"), text="Files content").pack(padx=20, pady=20)

        self.theme_option_menu = ctk.CTkOptionMenu(
            self.tab("Themes"),
            values=self.controller.state.available_themes,
            command=self._on_theme_selected
        )
        self.theme_option_menu.set(self.controller.state.selected_theme)
        self.theme_option_menu.pack(padx=20, pady=10, fill="x")

        # Settings Tab
        self.add("Settings")
        settings_tab = self.tab("Settings")

        # Live Preview Switch
        self.live_preview_switch_var = ctk.StringVar(value="on" if self.controller.state.is_live_preview_enabled else "off")
        self.live_preview_switch = ctk.CTkSwitch(settings_tab, text="Live Preview",
                                                 variable=self.live_preview_switch_var, onvalue="on", offvalue="off",
                                                 command=self._on_live_preview_toggled)
        self.live_preview_switch.pack(padx=20, pady=10, anchor="w")

        # Debounce Delay OptionMenu
        ctk.CTkLabel(settings_tab, text="Preview Debounce Time (seconds):").pack(padx=20, pady=(10,0), anchor="w")
        self.debounce_option_menu = ctk.CTkOptionMenu(
            settings_tab,
            values=[str(d) for d in self.controller.state.available_debounce_delays],
            command=self._on_debounce_delay_selected
        )
        self.debounce_option_menu.set(str(self.controller.state.debounce_delay))
        self.debounce_option_menu.pack(padx=20, pady=(0,10), fill="x")


    def _on_theme_selected(self, theme_name: str):
        self.controller.apply_theme(theme_name)

    def _on_live_preview_toggled(self):
        is_enabled = self.live_preview_switch_var.get() == "on"
        self.controller.toggle_live_preview(enabled=is_enabled)

    def _on_debounce_delay_selected(self, delay_str: str):
        self.controller.set_debounce_delay(float(delay_str))

    def update_settings_ui(self):
        """Updates the settings UI elements based on AppState."""
        self.live_preview_switch_var.set("on" if self.controller.state.is_live_preview_enabled else "off")
        self.debounce_option_menu.set(str(self.controller.state.debounce_delay))

    def update_theme_selection(self, themes: list, selected_theme: str):
        self.theme_option_menu.configure(values=themes)
        self.theme_option_menu.set(selected_theme)

    def update_slide_list(self, slides: List['SlideData'], current_slide_index: int, slide_images: List[bytes]):
        for widget in self.slide_buttons:
            widget.destroy()
        self.slide_buttons.clear()

        # Determine thumbnail width dynamically
        frame_width = self.slides_frame.winfo_width()
        horizontal_padding = 20  # Total padding (left + right)
        min_thumbnail_width = 80
        default_thumbnail_width = 220 # Approx 1.7x of 128

        if frame_width > (horizontal_padding + min_thumbnail_width): # Check if frame is wide enough
            thumbnail_width = frame_width - horizontal_padding
            if thumbnail_width < min_thumbnail_width: # Should not happen if previous check is correct, but as a safeguard
                thumbnail_width = min_thumbnail_width
        elif frame_width > min_thumbnail_width : # Frame is somewhat rendered but not very wide
             thumbnail_width = frame_width - horizontal_padding # Allow smaller than default if frame is small
             if thumbnail_width < min_thumbnail_width:
                 thumbnail_width = min_thumbnail_width
        else: # Frame is very small or not rendered (e.g. winfo_width is 1)
            thumbnail_width = default_thumbnail_width

        # Fallback to text if no images are provided or if there's a mismatch
        if not slide_images or len(slide_images) != len(slides):
            for slide in slides:
                button_text = f"Slide {slide.index}"
                # Try to get a title or the first line of content
                title_or_content = ""
                if slide.title:
                    title_or_content = slide.title[:20]
                elif slide.content:
                    first_line = slide.content.strip().splitlines()[0] if slide.content.strip() else ""
                    title_or_content = first_line[:20]
                if title_or_content:
                     button_text += f": {title_or_content}..."
                else:
                    button_text += "..."


                button = ctk.CTkButton(
                    self.slides_frame,
                    text=button_text,
                    command=lambda idx=slide.index: self.controller.navigate_to_slide(idx)
                )
                if slide.index == current_slide_index:
                    button.configure(fg_color=("#3a7ebf", "#1f538d"))
                button.pack(fill="x", pady=2, padx=5)
                self.slide_buttons.append(button)
            return

        thumbnail_width = 128  # Thumbnail width

        for i, slide in enumerate(slides):
            if i < len(slide_images) and slide_images[i]:
                try:
                    img_data = slide_images[i]
                    pil_image = Image.open(io.BytesIO(img_data))

                    aspect_ratio = pil_image.height / pil_image.width
                    thumbnail_height = int(thumbnail_width * aspect_ratio)

                    ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(thumbnail_width, thumbnail_height))

                    image_widget = ctk.CTkButton(
                        self.slides_frame,
                        image=ctk_image,
                        text="",
                        command=lambda idx=slide.index: self.controller.navigate_to_slide(idx),
                        fg_color="transparent"
                    )

                    if slide.index == current_slide_index:
                        image_widget.configure(fg_color=("#90CAF9", "#1E88E5")) # Example selected color (light blueish)

                    image_widget.pack(padx=5, pady=5)
                    self.slide_buttons.append(image_widget)

                except Exception as e:
                    print(f"Error displaying slide thumbnail {slide.index}: {e}")
                    error_button = ctk.CTkButton(
                        self.slides_frame,
                        text=f"Slide {slide.index} (Error)",
                        command=lambda idx=slide.index: self.controller.navigate_to_slide(idx)
                    )
                    if slide.index == current_slide_index:
                        error_button.configure(fg_color=("#3a7ebf", "#1f538d"))
                    error_button.pack(fill="x", pady=2, padx=5)
                    self.slide_buttons.append(error_button)
            else:
                # Fallback for missing image for a specific slide
                fallback_button = ctk.CTkButton(
                    self.slides_frame,
                    text=f"Slide {slide.index} (No image data)",
                    command=lambda idx=slide.index: self.controller.navigate_to_slide(idx)
                )
                if slide.index == current_slide_index:
                    fallback_button.configure(fg_color=("#3a7ebf", "#1f538d"))
                fallback_button.pack(fill="x", pady=2, padx=5)
                self.slide_buttons.append(fallback_button)

class MainAppView(ctk.CTk):
    def __init__(self, controller: 'AppController'):
        super().__init__()
        self.controller = controller
        self.controller.view = self
        self.presentation_window: Optional[ctk.CTkToplevel] = None
        self.presentation_html_frame: Optional[tkinterweb.HtmlFrame] = None
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        self.title("Marp Editor")
        self.geometry("1200x800")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # MenuBar
        self.menu_bar_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.menu_bar_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.file_menu_button = ctk.CTkButton(self.menu_bar_frame, text="File", width=50, command=self._show_file_menu)
        self.file_menu_button.pack(side="left", padx=5, pady=2)

        self.view_menu_button = ctk.CTkButton(self.menu_bar_frame, text="View", width=50, command=self._show_view_menu)
        self.view_menu_button.pack(side="left", padx=5, pady=2)

        # ToolBar
        self.tool_bar_frame = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.tool_bar_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(1,0))
        
        self.prev_slide_button = ctk.CTkButton(self.tool_bar_frame, text="< Prev", width=70, command=lambda: self.controller.navigate_slide("prev"))
        self.prev_slide_button.pack(side="left", padx=5, pady=5)

        self.next_slide_button = ctk.CTkButton(self.tool_bar_frame, text="Next >", width=70, command=lambda: self.controller.navigate_slide("next"))
        self.next_slide_button.pack(side="left", padx=5, pady=5)

        self.aspect_ratio_button = ctk.CTkSegmentedButton(self.tool_bar_frame, values=["4:3", "16:9"], command=self._on_aspect_ratio_change)
        self.aspect_ratio_button.set("16:9")
        self.aspect_ratio_button.pack(side="left", padx=10, pady=5)

        self.refresh_preview_button = ctk.CTkButton(self.tool_bar_frame, text="Refresh Preview", width=120, command=self._on_refresh_preview)
        self.refresh_preview_button.pack(side="left", padx=10, pady=5)

        # Main Content Area
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_content_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.main_content_frame.grid_columnconfigure(1, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(1, weight=1)

        # SidePanel
        self.side_panel = SidePanel(self.main_content_frame, self.controller)
        self.side_panel.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=5, pady=5)

        # Editor and Preview Panels
        self.editor_panel = EditorPanel(self.main_content_frame, self.controller)
        self.editor_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.preview_panel = PreviewPanel(self.main_content_frame, self.controller)
        self.preview_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # StatusBar
        self.status_bar_frame = ctk.CTkFrame(self, height=20, corner_radius=0)
        self.status_bar_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar_frame, text="Ready")
        self.status_label.pack(side="left", padx=10, pady=2)

        self.char_count_label = ctk.CTkLabel(self.status_bar_frame, text="Chars: 0")
        self.char_count_label.pack(side="right", padx=10, pady=2)

        self.line_count_label = ctk.CTkLabel(self.status_bar_frame, text="Lines: 0")
        self.line_count_label.pack(side="right", padx=10, pady=2)

    def update_status(self, message: str, char_count: int = 0, line_count: int = 0):
        self.status_label.configure(text=message)
        self.char_count_label.configure(text=f"Chars: {char_count}")
        self.line_count_label.configure(text=f"Lines: {line_count}")

    def update_previews_panel(self, image_data: List[bytes], aspect_ratio: str):
        self.preview_panel.update_previews(image_data, aspect_ratio)

    def update_presentation_view(self, html_content: str):
        if self.presentation_html_frame:
            self.presentation_html_frame.load_html(html_content)

    def get_editor_content(self) -> str:
        return self.editor_panel.text_widget.get("1.0", "end-1c")

    def set_editor_content(self, content: str):
        self.editor_panel.set_content(content)

    def _on_aspect_ratio_change(self, aspect_ratio: str):
        self.controller.set_aspect_ratio(aspect_ratio)

    def _on_refresh_preview(self):
        self.controller._schedule_preview_update(force=True)

    def _show_file_menu(self):
        menu = tkinter.Menu(self, tearoff=0)
        menu.add_command(label="New", command=self.controller.create_new_document)
        menu.add_command(label="Open...", command=self.controller.open_document)
        menu.add_command(label="Save", command=self.controller.save_document)
        menu.add_command(label="Save As...", command=lambda: self.controller.save_document(file_path=None))
        export_menu = tkinter.Menu(menu, tearoff=0)
        export_menu.add_command(label="Export as HTML...", command=self.controller.export_html)
        menu.add_cascade(label="Export", menu=export_menu)
        try:
            menu.tk_popup(self.file_menu_button.winfo_rootx(), self.file_menu_button.winfo_rooty() + self.file_menu_button.winfo_height())
        finally:
            menu.grab_release()

    def _show_view_menu(self):
        menu = tkinter.Menu(self, tearoff=0)
        menu.add_command(label="Toggle Presentation Mode", command=self.toggle_presentation_mode)
        try:
            menu.tk_popup(self.view_menu_button.winfo_rootx(), self.view_menu_button.winfo_rooty() + self.view_menu_button.winfo_height())
        finally:
            menu.grab_release()

    def update_theme_selection(self, themes: list, selected_theme: str):
        self.side_panel.update_theme_selection(themes, selected_theme)

    def update_slide_list(self, slides: List['SlideData'], current_slide_index: int, slide_images: List[bytes]):
        self.side_panel.update_slide_list(slides, current_slide_index, slide_images)

    def toggle_presentation_mode(self):
        if self.presentation_window is None or not self.presentation_window.winfo_exists():
            self.enter_presentation_mode()
        else:
            self.exit_presentation_mode()

    def enter_presentation_mode(self):
        self.presentation_window = ctk.CTkToplevel(self)
        self.presentation_window.attributes("-fullscreen", True)
        self.presentation_window.bind("<Escape>", lambda e: self.exit_presentation_mode())
        
        self.presentation_html_frame = tkinterweb.HtmlFrame(self.presentation_window, messages_enabled=False)
        self.presentation_html_frame.pack(expand=True, fill="both")
        
        self.controller.state.is_presentation_mode = True
        self.controller.update_preview(force=True)

    def exit_presentation_mode(self):
        if self.presentation_window:
            self.presentation_window.destroy()
            self.presentation_window = None
        self.presentation_html_frame = None
        self.controller.state.is_presentation_mode = False
        self.controller.update_preview(force=True)
