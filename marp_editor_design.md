# Marp Editor 統合設計書

## 1. 概要

CustomTkinterとPythonを用いて、Marp for VS Codeのような直感的でモダンなデスクトップエディタを開発する。本設計書では、実装可能性と保守性を重視し、段階的な開発が可能な堅牢なアーキテクチャを定義する。

## 2. システム全体アーキテクチャ

### 2.1. 基本設計思想

**改良されたMVCアーキテクチャ**を採用し、以下の4つの主要コンポーネントで構成する：

```
┌─────────────────┐    ┌─────────────────┐
│   MainAppView   │◄──►│ AppController   │
│   (View Layer)  │    │ (Controller)    │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │    AppState     │
         │              │    (Model)      │
         │              └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         └──────────────┤   MarpEngine    │
                        │   (Service)     │
                        └─────────────────┘
```

### 2.2. 各層の責務

- **View Layer**: UI表示とユーザー入力の受付
- **Controller**: ビジネスロジックと状態管理
- **Model**: アプリケーション状態の保持
- **Service**: Markdown変換とファイル操作

## 3. 詳細クラス設計

### 3.1. AppState (Model) - アプリケーション状態管理

アプリケーションの全状態を一元管理するデータクラス。

#### 3.1.1. 基本プロパティ

```python
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
    
    # テーマ・設定関連
    selected_theme: str = "default"
    available_themes: List[str] = field(default_factory=lambda: ["default", "gaia", "uncover"])
    
    # UI状態
    is_live_preview_enabled: bool = True
    editor_font_size: int = 12
    preview_zoom_level: float = 1.0
    window_layout: Dict[str, Any] = field(default_factory=dict)
    
    # 最近使用したファイル
    recent_files: List[Path] = field(default_factory=list)
    
    # エラー・メッセージ
    last_error: Optional[str] = None
    status_message: str = "Ready"
```

#### 3.1.2. 補助データクラス

```python
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
```

### 3.2. MarpEngine (Service) - Markdown変換エンジン

Pythonによる内部実装でMarkdownからMarpスライドへの変換を行う。

#### 3.2.1. 核心機能

**依存ライブラリ**:
- `markdown-it-py`: 高性能Markdownパーサー
- `python-frontmatter`: フロントマター解析
- `Pygments`: シンタックスハイライト
- `jinja2`: テンプレートエンジン

**主要メソッド**:

```python
class MarpEngine:
    def parse_document(self, markdown_content: str) -> ParsedDocument:
        """Markdownドキュメントを解析し、構造化データを返す"""
        
    def render_presentation(self, parsed_doc: ParsedDocument, theme: str) -> RenderedPresentation:
        """解析済みドキュメントをHTMLプレゼンテーションに変換"""
        
    def apply_theme(self, html_content: str, theme_name: str) -> str:
        """指定されたテーマを適用"""
        
    def extract_slides(self, markdown_content: str) -> List[SlideData]:
        """Markdownからスライドデータを抽出"""
        
    def validate_syntax(self, markdown_content: str) -> List[ValidationError]:
        """Markdown構文の検証"""
```

#### 3.2.2. テーマシステム

**テーマ管理**:
- 各テーマをCSS + メタデータで管理
- カスタムテーマの追加対応
- テーマのプレビュー機能

**テーマ構造**:
```python
@dataclass
class Theme:
    name: str
    display_name: str
    css_content: str
    variables: Dict[str, str]  # CSS変数
    fonts: List[str]
    preview_image: Optional[str] = None
    description: str = ""
```

#### 3.2.3. ディレクティブ処理

**グローバルディレクティブ**:
- フロントマターからの抽出
- `theme`, `size`, `class`, `header`, `footer`等への対応

**ローカルディレクティブ**:
- HTMLコメント形式 `<!-- directive: value -->`
- スライド単位での適用
- 継承ルールの実装

### 3.3. AppController (Controller) - アプリケーション制御

ViewとModelの仲介役として、アプリケーションのロジックを管理する。

#### 3.3.1. 基本構造

```python
class AppController:
    def __init__(self):
        self.state = AppState()
        self.view: Optional[MainAppView] = None
        self.marp_engine = MarpEngine()
        self.file_manager = FileManager()
        self.settings_manager = SettingsManager()
        self.auto_save_timer: Optional[Timer] = None
        self.preview_update_timer: Optional[Timer] = None
```

#### 3.3.2. 文書操作メソッド

```python
def create_new_document(self) -> bool:
    """新規ドキュメントを作成"""
    
def open_document(self, file_path: Path) -> bool:
    """ドキュメントを開く"""
    
def save_document(self, file_path: Optional[Path] = None) -> bool:
    """ドキュメントを保存"""
    
def close_document(self) -> bool:
    """ドキュメントを閉じる（保存確認含む）"""
    
def import_document(self, file_path: Path, file_type: str) -> bool:
    """他形式からのインポート"""
```

#### 3.3.3. エディタ制御メソッド

```python
def on_content_changed(self, new_content: str) -> None:
    """エディタ内容変更時の処理"""
    
def toggle_live_preview(self, enabled: bool) -> None:
    """ライブプレビューの有効/無効切り替え"""
    
def update_preview(self, force: bool = False) -> None:
    """プレビューの更新"""
    
def apply_theme(self, theme_name: str) -> None:
    """テーマの適用"""
    
def insert_slide_break(self, position: int) -> None:
    """スライド区切りの挿入"""
```

#### 3.3.4. プレゼンテーション制御メソッド

```python
def navigate_to_slide(self, slide_index: int) -> bool:
    """指定スライドへの移動"""
    
def navigate_slide(self, direction: str) -> bool:
    """スライドナビゲーション（'prev'/'next'）"""
    
def enter_presentation_mode(self) -> None:
    """プレゼンテーションモードに入る"""
    
def exit_presentation_mode(self) -> None:
    """プレゼンテーションモードを終了"""
    
def toggle_speaker_notes(self, visible: bool) -> None:
    """スピーカーノートの表示切り替え"""
```

#### 3.3.5. エクスポート機能

```python
def export_html(self, output_path: Path, options: ExportOptions) -> bool:
    """HTMLファイルとしてエクスポート"""
    
def export_pdf(self, output_path: Path, options: ExportOptions) -> bool:
    """PDFファイルとしてエクスポート"""
    
def export_images(self, output_dir: Path, options: ExportOptions) -> bool:
    """画像ファイルとしてエクスポート"""
    
def export_pptx(self, output_path: Path, options: ExportOptions) -> bool:
    """PowerPointファイルとしてエクスポート"""
```

### 3.4. MainAppView (View) - ユーザーインターフェース

CustomTkinterを使用した現代的なUIを提供する。

#### 3.4.1. 基本ウィンドウ構造

```python
class MainAppView(ctk.CTk):
    def __init__(self, controller: AppController):
        super().__init__()
        self.controller = controller
        self.setup_window()
        self.create_widgets()
        self.setup_layout()
        self.bind_events()
```

#### 3.4.2. UI コンポーネント構成

**メインレイアウト**:
```
┌─────────────────────────────────────────────────┐
│                MenuBar                          │
├─────────────────────────────────────────────────┤
│                ToolBar                          │
├─────────────────┬───────────────────────────────┤
│                 │                               │
│   SidePanel     │        MainContent            │
│   - Outline     │   ┌─────────┬─────────────┐   │
│   - Files       │   │ Editor  │  Preview    │   │
│   - Slides      │   │ Panel   │  Panel      │   │
│                 │   └─────────┴─────────────┘   │
│                 │                               │
├─────────────────┴───────────────────────────────┤
│                StatusBar                        │
└─────────────────────────────────────────────────┘
```

**主要コンポーネント**:

1. **MenuBar**: ファイル、編集、表示、ツール、ヘルプメニュー
2. **ToolBar**: よく使用する機能のクイックアクセス
3. **SidePanel**: 補助情報の表示
4. **EditorPanel**: Markdownエディタ
5. **PreviewPanel**: リアルタイムプレビュー
6. **StatusBar**: ステータス情報の表示

#### 3.4.3. EditorPanel - 高機能エディタ

```python
class EditorPanel(ctk.CTkFrame):
    def __init__(self, parent, controller: AppController):
        super().__init__(parent)
        self.controller = controller
        self.setup_editor()
        self.setup_features()
    
    def setup_editor(self):
        """エディタの基本設定"""
        # テキストウィジェット
        # 行番号表示
        # スクロールバー
        
    def setup_features(self):
        """高度な機能の設定"""
        # シンタックスハイライト
        # オートコンプリート
        # 検索・置換
        # 折りたたみ
```

**エディタ機能**:
- Markdownシンタックスハイライト
- 行番号表示
- 検索・置換機能
- オートインデント
- 括弧の自動補完
- Marpディレクティブのオートコンプリート
- ライブ文字数カウント

#### 3.4.4. PreviewPanel - 高性能プレビュー

```python
class PreviewPanel(ctk.CTkFrame):
    def __init__(self, parent, controller: AppController):
        super().__init__(parent)
        self.controller = controller
        self.setup_webview()
        self.setup_controls()
    
    def setup_webview(self):
        """WebView コンポーネントの設定"""
        # HTMLレンダリング
        # JavaScript実行環境
        
    def setup_controls(self):
        """プレビュー制御の設定"""
        # スライドナビゲーション
        # ズーム制御
        # 全画面表示
```

**プレビュー機能**:
- リアルタイムHTML表示
- スライドナビゲーション
- ズーム機能
- 全画面プレゼンテーションモード
- スピーカーノート表示
- 同期スクロール

#### 3.4.5. SidePanel - 補助情報表示

```python
class SidePanel(ctk.CTkTabview):
    def __init__(self, parent, controller: AppController):
        super().__init__(parent)
        self.controller = controller
        self.setup_tabs()
    
    def setup_tabs(self):
        """タブの設定"""
        # アウトラインタブ
        # スライド一覧タブ
        # ファイルエクスプローラータブ
        # テーマ選択タブ
```

**サイドパネル機能**:
- **アウトライン**: 見出し構造の表示
- **スライド一覧**: スライドのサムネイル表示
- **ファイルエクスプローラー**: ファイル管理
- **テーマ選択**: テーマのプレビューと選択

## 4. 主要機能の実装方針

### 4.1. ライブプレビュー機能

**実装フロー**:
1. **テキスト変更検知**: `EditorPanel`がテキスト変更を検知
2. **デバウンス処理**: 連続入力による負荷軽減のため200ms遅延
3. **バックグラウンド処理**: 別スレッドでMarkdown変換を実行
4. **プレビュー更新**: メインスレッドでHTML表示を更新

**パフォーマンス最適化**:
- 変更差分の検出による部分更新
- 変換結果のキャッシュ
- 重い処理の非同期実行

### 4.2. スライドナビゲーション

**HTML生成方式**:
```html
<div class="marp-presentation">
  <section class="slide" data-slide="1">
    <!-- スライド1の内容 -->
  </section>
  <section class="slide" data-slide="2">
    <!-- スライド2の内容 -->
  </section>
</div>
```

**JavaScript制御**:
```javascript
function showSlide(slideNumber) {
    // 全スライドを非表示
    document.querySelectorAll('.slide').forEach(slide => {
        slide.style.display = 'none';
    });
    
    // 指定スライドを表示
    const targetSlide = document.querySelector(`[data-slide="${slideNumber}"]`);
    if (targetSlide) {
        targetSlide.style.display = 'block';
    }
}
```

### 4.3. テーマシステム

**テーマ構造**:
```
themes/
├── default/
│   ├── theme.css
│   ├── theme.json
│   └── preview.png
├── gaia/
│   ├── theme.css
│   ├── theme.json
│   └── preview.png
└── uncover/
    ├── theme.css
    ├── theme.json
    └── preview.png
```

**テーマ切り替え処理**:
1. 新テーマの読み込み
2. CSSの差し替え
3. プレビューの再レンダリング
4. 設定の保存

### 4.4. ファイル操作

**サポートファイル形式**:
- **読み込み**: `.md`, `.markdown`, `.txt`
- **保存**: `.md`, `.html`, `.pdf`, `.pptx`
- **エクスポート**: 各種形式に対応

**ファイル管理機能**:
- 最近使用したファイル
- 自動バックアップ
- 復旧機能
- 文字エンコーディング自動判別

## 5. エラーハンドリング設計

### 5.1. エラー分類

**ユーザーエラー**:
- 不正なMarkdown記法
- 存在しないファイルの指定
- 権限不足によるアクセス拒否

**システムエラー**:
- メモリ不足
- ディスク容量不足
- 予期しない例外

**ネットワークエラー**:
- 外部リソースの取得失敗
- タイムアウト

### 5.2. エラー処理方針

```python
class ErrorHandler:
    def handle_error(self, error: Exception, context: str) -> None:
        """統一的なエラー処理"""
        
    def show_user_error(self, message: str, details: str = None) -> None:
        """ユーザー向けエラー表示"""
        
    def log_system_error(self, error: Exception, context: str) -> None:
        """システムエラーのログ記録"""
        
    def attempt_recovery(self, error_type: str) -> bool:
        """自動復旧の試行"""
```

## 6. 設定管理システム

### 6.1. 設定項目

**エディタ設定**:
- フォント設定（種類、サイズ、行間）
- テーマ設定（ダーク/ライトモード）
- 自動保存間隔
- タブ設定（タブサイズ、スペース変換）

**プレビュー設定**:
- デフォルトテーマ
- ズームレベル
- 同期スクロール
- 更新間隔

**エクスポート設定**:
- デフォルト形式
- 画質設定
- ページサイズ
- 余白設定

### 6.2. 設定の永続化

```python
class SettingsManager:
    def __init__(self):
        self.config_file = Path.home() / '.marp-editor' / 'config.json'
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """設定の読み込み"""
        
    def save_settings(self) -> None:
        """設定の保存"""
        
    def reset_to_defaults(self) -> None:
        """デフォルト設定への復元"""
```

## 7. パフォーマンス最適化

### 7.1. レンダリング最適化

**戦略**:
- 変更差分の検出
- 仮想DOM的なアプローチ
- レンダリング処理の分割実行

**実装**:
```python
class OptimizedRenderer:
    def __init__(self):
        self.last_rendered_content = ""
        self.render_cache = {}
    
    def render_with_diff(self, content: str) -> str:
        """差分レンダリング"""
        
    def cache_result(self, key: str, result: str) -> None:
        """結果のキャッシュ"""
```

### 7.2. メモリ管理

**メモリ使用量の監視**:
- 大きなドキュメントの処理
- 画像リソースの管理
- 不要なオブジェクトの解放

**実装**:
```python
class MemoryManager:
    def monitor_usage(self) -> Dict[str, int]:
        """メモリ使用量の監視"""
        
    def cleanup_cache(self) -> None:
        """キャッシュのクリーンアップ"""
        
    def optimize_for_large_files(self, file_size: int) -> None:
        """大きなファイル用の最適化"""
```

## 8. 実装ステップ（詳細版）

### Phase 1: 基盤構築（3-4週間）

**Week 1: アーキテクチャ構築**
- `AppState`, `AppController`, `MarpEngine`の基本実装
- 依存関係の整理
- 基本的なエラーハンドリング

**Week 2: 基本UI構築**
- `MainAppView`の基本レイアウト
- `EditorPanel`の基本機能
- `PreviewPanel`の基本表示

**Week 3: 基本機能統合**
- テキスト入力とプレビュー表示の連携
- 基本的なMarkdown変換
- ファイル読み込み・保存

**Week 4: 品質向上**
- 単体テストの実装
- 基本的なエラーハンドリング
- コードレビューと改善

### Phase 2: 核心機能実装（5-6週間）

**Week 5-6: Markdown変換エンジン**
- `markdown-it-py`を使用した変換処理
- フロントマター解析
- 基本的なディレクティブ対応

**Week 7-8: テーマシステム**
- テーマ読み込み機能
- CSS適用処理
- テーマ切り替えUI

**Week 9-10: スライドナビゲーション**
- スライド分割処理
- JavaScript制御システム
- ナビゲーションUI

### Phase 3: 高度機能実装（4-5週間）

**Week 11-12: エクスポート機能**
- HTML出力機能
- PDF生成機能（`weasyprint`または`playwright`使用）
- 画像出力機能

**Week 13-14: UI/UX向上**
- シンタックスハイライト
- オートコンプリート
- 検索・置換機能

**Week 15: プレゼンテーションモード**
- 全画面表示機能
- スピーカーノート表示
- キーボードショートカット

### Phase 4: 品質向上・最適化（2-3週間）

**Week 16-17: パフォーマンス最適化**
- レンダリング最適化
- メモリ使用量改善
- 大きなファイルの対応

**Week 18: 最終調整**
- 統合テスト
- ドキュメント整備
- リリース準備

## 9. 技術選定の詳細

### 9.1. 必須ライブラリ

**UI関連**:
- `customtkinter`: モダンなUI
- `tkinter.ttk`: 標準ウィジェット
- `PIL` (Pillow): 画像処理

**Markdown処理**:
- `markdown-it-py`: 高性能パーサー
- `python-frontmatter`: フロントマター解析
- `pygments`: シンタックスハイライト

**ファイル処理**:
- `pathlib`: パス操作
- `chardet`: 文字エンコーディング判定
- `watchdog`: ファイル変更監視

### 9.2. オプションライブラリ

**エクスポート関連**:
- `weasyprint`: HTML→PDF変換
- `playwright`: ブラウザ自動化
- `python-pptx`: PowerPoint出力

**その他**:
- `jinja2`: テンプレートエンジン
- `pydantic`: データ検証
- `typer`: CLI機能

## 10. 将来拡張計画

### 10.1. 近期計画（6ヶ月以内）

**機能追加**:
- プラグインシステム
- カスタムテーマエディタ
- 数式表示対応（MathJax）
- 図表作成支援（Mermaid）

**改善項目**:
- パフォーマンス向上
- アクセシビリティ対応
- 多言語対応

### 10.2. 長期計画（1年以内）

**高度機能**:
- リアルタイム協調編集
- クラウドストレージ連携
- バージョン管理統合
- AI支援機能

**プラットフォーム拡張**:
- Web版の開発
- モバイル対応
- VSCodeエクステンション

この統合設計書により、実装に必要な具体的な情報と、将来の拡張性を両立したMarp Editorの開発が可能になります。各実装段階で参照すべき設計指針と、技術的な詳細を網羅的に記載しています。