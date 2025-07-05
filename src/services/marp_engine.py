from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json
import io
from PIL import Image
from playwright.sync_api import sync_playwright

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from src.models.app_state import SlideData # Import SlideData

@dataclass
class ParsedDocument:
    # Placeholder for parsed document structure
    pass

@dataclass
class RenderedPresentation:
    # Placeholder for rendered presentation structure
    pass

@dataclass
class ValidationError:
    # Placeholder for validation error structure
    pass

@dataclass
class Theme:
    name: str
    display_name: str
    css_content: str
    variables: Dict[str, str]  # CSS変数
    fonts: List[str]
    preview_image: Optional[str] = None
    description: str = ""

class MarpEngine:
    def __init__(self):
        self.md = MarkdownIt('commonmark', {'html': True, 'typographer': True, 'breaks': True}) # Added 'breaks': True
        self.md.enable(['table', 'linkify', 'strikethrough'])
        self.md.add_render_rule('fence', self._render_fence_pygments)
        self.formatter = HtmlFormatter(cssclass="highlight")
        self.themes: Dict[str, Theme] = {}
        self._load_themes()

    def _render_fence_pygments(self, tokens, idx, options, env):
        token = tokens[idx]
        lang = token.info.strip()
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except:
            return '<pre class="highlight"><code>' + self.md.utils.escapeHtml(token.content) + '</code></pre>'

        return highlight(token.content, lexer, self.formatter)

    def _load_themes(self):
        themes_dir = Path(__file__).parent.parent.parent / "themes"
        if not themes_dir.exists():
            print(f"Themes directory not found: {themes_dir}")
            return

        for theme_path in themes_dir.iterdir():
            if theme_path.is_dir():
                theme_name = theme_path.name
                css_file = theme_path / "theme.css"
                json_file = theme_path / "theme.json"

                if css_file.exists() and json_file.exists():
                    try:
                        with open(css_file, 'r', encoding='utf-8') as f:
                            css_content = f.read()
                        with open(json_file, 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                        
                        theme = Theme(
                            name=theme_name,
                            display_name=theme_data.get("display_name", theme_name.capitalize()),
                            css_content=css_content,
                            variables=theme_data.get("variables", {}),
                            fonts=theme_data.get("fonts", []),
                            description=theme_data.get("description", "")
                        )
                        self.themes[theme_name] = theme
                    except Exception as e:
                        print(f"Error loading theme {theme_name}: {e}")
        if not self.themes:
            print("No themes loaded. Ensure 'themes' directory and its contents are correctly set up.")

    def get_available_themes(self) -> List[str]:
        return list(self.themes.keys())

    def parse_document(self, markdown_content: str) -> ParsedDocument:
        """Markdownドキュメントを解析し、構造化データを返す"""
        # Placeholder implementation - will be implemented more fully later
        return ParsedDocument()
        
    def render_presentation(self, markdown_content: str, theme_name: str, slide_index: Optional[int] = None) -> str:
        """解析済みドキュメントをHTMLプレゼンテーションに変換"""
        slides = self.extract_slides(markdown_content)
        
        content_to_render = ""
        if slide_index is not None and 0 <= slide_index < len(slides):
            content_to_render = slides[slide_index].content
        elif slide_index is None:
            content_to_render = markdown_content # Render all if no specific slide is requested
        
        # Render markdown to HTML using markdown-it-py
        html_content = self.md.render(content_to_render)
        
        # Apply theme
        theme_css = ""
        if theme_name in self.themes:
            theme_css = self.themes[theme_name].css_content
        else:
            print(f"Warning: Theme '{theme_name}' not found. Using default styles.")

        final_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Marp Preview</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; }}
        .highlight {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        pre {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        
        /* Default list styles for better rendering in tkinterweb */
        ol, ul {{
            margin-left: 20px;
            padding-left: 0;
        }}
        li {{
            margin-bottom: 5px;
        }}

        {self.formatter.get_style_defs()}
        {theme_css}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
        return final_html

    def render_slides_as_images(self, markdown_content: str, theme_name: str, aspect_ratio: str) -> List[bytes]:
        slides = self.extract_slides(markdown_content)
        images = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for slide in slides:
                html = self.render_slide_html(slide.content, theme_name, aspect_ratio)
                page = browser.new_page()
                width, height = (800, 600) if aspect_ratio == "4:3" else (1024, 576)
                page.set_viewport_size({"width": width, "height": height})
                page.set_content(html)
                image_bytes = page.screenshot(type="png")
                images.append(image_bytes)
                page.close()
            browser.close()
        return images

    def render_slide_html(self, slide_content: str, theme_name: str, aspect_ratio: str) -> str:
        html_content = self.md.render(slide_content)
        theme_css = self.themes.get(theme_name, Theme(name="default", display_name="Default", css_content="", variables={}, fonts=[])).css_content
        width, height = (800, 600) if aspect_ratio == "4:3" else (1024, 576)

        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Marp Preview</title>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; }}
        .slide {{ width: {width}px; height: {height}px; border: 1px solid #ccc; box-sizing: border-box; padding: 20px; overflow: hidden; }}
        {self.formatter.get_style_defs()}
        {theme_css}
    </style>
</head>
<body>
<div class="slide">
{html_content}
</div>
</body>
</html>
"""
        
    def apply_theme(self, html_content: str, theme_name: str) -> str:
        """指定されたテーマを適用"""
        # This method is now largely redundant as theme application is in render_presentation
        return html_content
        
    def extract_slides(self, markdown_content: str) -> List[SlideData]:
        """Markdownからスライドデータを抽出"""
        slides_raw = markdown_content.split('\n---\n') # Marp slide delimiter
        slides_data = []
        for i, slide_content in enumerate(slides_raw):
            # Basic extraction for now. Later, parse directives and notes.
            slides_data.append(SlideData(
                index=i + 1,
                title=f"Slide {i + 1}", # Placeholder title
                content=slide_content.strip(),
                directives={},
                notes=None
            ))
        return slides_data
        
    def validate_syntax(self, markdown_content: str) -> List[ValidationError]:
        """Markdown構文の検証"""
        # Placeholder implementation
        return []