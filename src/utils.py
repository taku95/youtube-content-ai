"""
ユーティリティ関数
"""
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

def get_env(key: str, default: Optional[str] = None) -> str:
    """環境変数取得"""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"環境変数 {key} が設定されていません")
    return value

def parse_youtube_url(url: str) -> Optional[str]:
    """YouTube URLから動画IDを抽出"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def format_timestamp(seconds: float) -> str:
    """秒数を「分:秒」形式に変換"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def parse_timestamp(timestamp: str) -> Optional[int]:
    """「分:秒」形式をタイムスタンプ秒数に変換"""
    try:
        parts = timestamp.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        return None
    return None

def save_json(data: Any, filename: str, output_dir: str = "outputs") -> str:
    """JSONファイルとして保存"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{timestamp}_{filename}.json")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath

def load_json(filepath: str) -> Any:
    """JSONファイル読み込み"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_json_from_text(text: str) -> Optional[Dict]:
    """テキストからJSON部分を抽出してパース"""
    # JSONブロックを探す
    json_pattern = r'```json\s*(\{.*?\}|\[.*?\])\s*```'
    match = re.search(json_pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1)
    else:
        # ```なしの場合、全体をJSONとして試す
        json_str = text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # {または[で始まる部分を探す
        start_idx = text.find('{')
        if start_idx == -1:
            start_idx = text.find('[')

        if start_idx >= 0:
            # 対応する閉じ括弧を見つける
            bracket_count = 0
            bracket_type = text[start_idx]
            end_bracket = '}' if bracket_type == '{' else ']'

            for i in range(start_idx, len(text)):
                if text[i] == bracket_type:
                    bracket_count += 1
                elif text[i] == end_bracket:
                    bracket_count -= 1
                    if bracket_count == 0:
                        try:
                            return json.loads(text[start_idx:i+1])
                        except:
                            pass
        return None

def truncate_text(text: str, max_length: int = 100) -> str:
    """テキストを指定文字数で切り詰め"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def clean_text(text: str) -> str:
    """テキストのクリーニング"""
    # 改行を統一
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # 連続する空白を1つに
    text = re.sub(r' +', ' ', text)
    # 連続する改行を2つまでに
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

class ProgressLogger:
    """進捗ログ出力"""
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def log(self, message: str, level: str = "INFO"):
        """ログ出力"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")

    def success(self, message: str):
        """成功ログ"""
        self.log(f"✅ {message}", "SUCCESS")

    def error(self, message: str):
        """エラーログ"""
        self.log(f"❌ {message}", "ERROR")

    def warning(self, message: str):
        """警告ログ"""
        self.log(f"⚠️  {message}", "WARNING")

    def info(self, message: str):
        """情報ログ"""
        self.log(f"ℹ️  {message}", "INFO")
