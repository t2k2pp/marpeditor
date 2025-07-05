from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

@dataclass
class SlideData:
    index: int
    title: str
    content: str
    directives: Dict[str, str]
    notes: Optional[str] = None
    
@dataclass
class DocumentMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None
    size: Optional[str] = None
    custom_directives: Dict[str, str] = field(default_factory=dict)

@dataclass
class AppState:
    # ドキュメント関連
    markdown_content: str = ""
    html_content: str = ""
    current_file_path: Optional[Path] = None
    is_document_modified: bool = False
    document_encoding: str = "utf-8"
    
    # プレゼンテーション関連
    slide_count: int = 0
    current_slide_index: int = 1
    slides_data: List[SlideData] = field(default_factory=list)
    is_presentation_mode: bool = False # Added this line
    
    # テーマ・設定関連
    selected_theme: str = "default"
    available_themes: List[str] = field(default_factory=lambda: ["default", "gaia", "uncover"])
    
    # UI状態
    is_live_preview_enabled: bool = True
    editor_font_size: int = 12
    preview_zoom_level: float = 1.0
    debounce_delay: float = 1.0  # Default debounce delay in seconds
    available_debounce_delays: List[float] = field(default_factory=lambda: [1.0, 3.0, 5.0])
    aspect_ratio: str = "16:9" # Add aspect_ratio
    window_layout: Dict[str, Any] = field(default_factory=dict)
    
    # 最近使用したファイル
    recent_files: List[Path] = field(default_factory=list)
    
    # エラー・メッセージ
    last_error: Optional[str] = None
    status_message: str = "Ready"