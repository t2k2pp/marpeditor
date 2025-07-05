from pathlib import Path
from typing import Optional
import chardet

class FileManager:
    def read_file(self, file_path: Path) -> Optional[str]:
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # Attempt to detect encoding
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['encoding'] else 'utf-8'
            
            return raw_data.decode(encoding)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def write_file(self, file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False