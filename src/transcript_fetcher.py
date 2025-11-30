"""
YouTube文字起こし取得モジュール
"""
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Optional
from src.utils import format_timestamp, ProgressLogger

class TranscriptFetcher:
    def __init__(self, logger: ProgressLogger = None):
        self.logger = logger or ProgressLogger()

    def fetch_transcript(
        self,
        video_id: str,
        languages: List[str] = ['ja', 'en']
    ) -> Optional[List[Dict]]:
        """
        動画の文字起こしを取得

        Args:
            video_id: YouTube動画ID
            languages: 優先言語リスト

        Returns:
            [{
                "text": "テキスト",
                "start": 開始秒数,
                "duration": 継続秒数,
                "timestamp": "分:秒"
            }]
        """
        self.logger.info(f"文字起こし取得中: {video_id}")

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 優先言語で取得を試みる
            transcript = None
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except:
                    continue

            if not transcript:
                # 自動生成字幕を含めて最初に見つかったものを使用
                transcript = transcript_list.find_generated_transcript(languages)

            if not transcript:
                self.logger.warning(f"字幕が見つかりませんでした: {video_id}")
                return None

            transcript_data = transcript.fetch()

            # タイムスタンプを追加
            formatted_transcript = []
            for item in transcript_data:
                formatted_transcript.append({
                    "text": item['text'],
                    "start": item['start'],
                    "duration": item['duration'],
                    "timestamp": format_timestamp(item['start'])
                })

            self.logger.success(f"文字起こし取得完了: {len(formatted_transcript)}セグメント")
            return formatted_transcript

        except Exception as e:
            self.logger.error(f"文字起こし取得エラー: {str(e)}")
            return None

    def get_transcript_text(
        self,
        video_id: str,
        max_duration: Optional[float] = None
    ) -> str:
        """
        文字起こしをテキストとして取得

        Args:
            video_id: YouTube動画ID
            max_duration: 最大秒数（指定した秒数まで）

        Returns:
            文字起こしテキスト
        """
        transcript = self.fetch_transcript(video_id)
        if not transcript:
            return ""

        texts = []
        for item in transcript:
            if max_duration and item['start'] > max_duration:
                break
            texts.append(item['text'])

        return " ".join(texts)

    def get_transcript_with_timestamps(
        self,
        video_id: str
    ) -> str:
        """
        タイムスタンプ付きの文字起こしテキストを取得

        Args:
            video_id: YouTube動画ID

        Returns:
            "[0:00] テキスト\n[0:05] テキスト\n..." 形式
        """
        transcript = self.fetch_transcript(video_id)
        if not transcript:
            return ""

        lines = []
        for item in transcript:
            lines.append(f"[{item['timestamp']}] {item['text']}")

        return "\n".join(lines)

    def search_in_transcript(
        self,
        video_id: str,
        keyword: str
    ) -> List[Dict]:
        """
        文字起こし内でキーワードを検索

        Args:
            video_id: YouTube動画ID
            keyword: 検索キーワード

        Returns:
            該当箇所のリスト
        """
        transcript = self.fetch_transcript(video_id)
        if not transcript:
            return []

        matches = []
        for item in transcript:
            if keyword.lower() in item['text'].lower():
                matches.append(item)

        return matches


if __name__ == "__main__":
    # テスト実行
    fetcher = TranscriptFetcher()

    # 実際の動画IDでテスト（存在する動画IDに置き換えてください）
    video_id = "dQw4w9WgXcQ"  # サンプル
    text = fetcher.get_transcript_text(video_id, max_duration=180)  # 最初の3分

    if text:
        print(f"文字起こし（最初の100文字）:\n{text[:100]}...")
