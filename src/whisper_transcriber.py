"""
Whisper文字起こしモジュール
OpenAI Whisper APIを使って動画から文字起こしを生成
"""
import openai
import os
import tempfile
import subprocess
from typing import Optional
from src.utils import get_env, ProgressLogger


class WhisperTranscriber:
    def __init__(self, logger: ProgressLogger = None):
        self.client = openai.OpenAI(api_key=get_env("OPENAI_API_KEY"))
        self.logger = logger or ProgressLogger()

    def transcribe_video(self, video_id: str) -> Optional[str]:
        """
        YouTube動画IDから音声を抽出してWhisper APIで文字起こし

        Args:
            video_id: YouTube動画ID

        Returns:
            文字起こしテキスト（タイムスタンプ付き）
        """
        self.logger.info(f"Whisper文字起こし開始: {video_id}")

        audio_file = None
        try:
            # Step 1: yt-dlpで音声抽出
            audio_file = self._download_audio(video_id)
            if not audio_file:
                return None

            # Step 2: Whisper APIで文字起こし
            transcript = self._transcribe_with_whisper(audio_file)

            if transcript:
                self.logger.success(f"文字起こし成功: {len(transcript)}文字")
                return transcript
            else:
                return None

        except Exception as e:
            self.logger.error(f"Whisper文字起こしエラー: {str(e)}")
            return None

        finally:
            # 一時ファイルを削除
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except:
                    pass

    def _download_audio(self, video_id: str) -> Optional[str]:
        """
        yt-dlpで音声をダウンロード

        Args:
            video_id: YouTube動画ID

        Returns:
            音声ファイルパス
        """
        try:
            # 一時ファイル作成
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                output_path = tmp.name

            url = f"https://www.youtube.com/watch?v={video_id}"

            # yt-dlpコマンド実行
            cmd = [
                "yt-dlp",
                "-x",  # 音声のみ抽出
                "--audio-format", "mp3",
                "--audio-quality", "5",  # 中品質（ファイルサイズ削減）
                "-o", output_path.replace('.mp3', ''),  # 出力先
                url
            ]

            self.logger.info(f"音声ダウンロード中: {video_id}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分タイムアウト
            )

            if result.returncode == 0:
                # yt-dlpは拡張子を自動で付けるので、実際のファイル名を探す
                base_path = output_path.replace('.mp3', '')
                for ext in ['.mp3', '.m4a', '.opus', '.webm']:
                    test_path = base_path + ext
                    if os.path.exists(test_path):
                        self.logger.success(f"音声ダウンロード完了: {test_path}")
                        return test_path

                # 元のパスも確認
                if os.path.exists(output_path):
                    return output_path

                self.logger.error("音声ファイルが見つかりません")
                return None
            else:
                self.logger.error(f"yt-dlpエラー: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            self.logger.error("音声ダウンロードがタイムアウトしました")
            return None
        except Exception as e:
            self.logger.error(f"音声ダウンロードエラー: {str(e)}")
            return None

    def _transcribe_with_whisper(self, audio_file: str) -> Optional[str]:
        """
        Whisper APIで文字起こし

        Args:
            audio_file: 音声ファイルパス

        Returns:
            文字起こしテキスト
        """
        try:
            # ファイルサイズチェック（25MB制限）
            file_size = os.path.getsize(audio_file)
            if file_size > 25 * 1024 * 1024:
                self.logger.warning(f"ファイルサイズが大きすぎます: {file_size / (1024*1024):.1f}MB")
                # TODO: ffmpegで圧縮処理を追加

            self.logger.info("Whisper API呼び出し中...")

            with open(audio_file, 'rb') as f:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",  # タイムスタンプ付き
                    language="ja"  # 日本語指定
                )

            # タイムスタンプ付きテキストを生成
            if hasattr(response, 'segments') and response.segments:
                transcript_parts = []
                for segment in response.segments:
                    start_time = self._format_timestamp(segment['start'])
                    text = segment['text']
                    transcript_parts.append(f"[{start_time}] {text}")

                return "\n".join(transcript_parts)
            else:
                # セグメントがない場合はテキストのみ
                return response.text

        except Exception as e:
            self.logger.error(f"Whisper APIエラー: {str(e)}")
            return None

    def _format_timestamp(self, seconds: float) -> str:
        """
        秒数を「分:秒」形式に変換

        Args:
            seconds: 秒数

        Returns:
            "0:32" 形式の文字列
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"


if __name__ == "__main__":
    # テスト実行
    transcriber = WhisperTranscriber()

    # テスト用の短い動画ID（実際のテストでは適切な動画IDを指定してください）
    test_video_id = "jNQXAC9IVRw"  # "Me at the zoo" - YouTube最初の動画

    transcript = transcriber.transcribe_video(test_video_id)
    if transcript:
        print(f"\n✅ 文字起こし成功！\n")
        print(transcript[:500])  # 最初の500文字のみ表示
    else:
        print("\n❌ 文字起こし失敗")
