"""
コメント分析エンジン
GPT-4で構文抽出とシーンマッチング
"""
import openai
from typing import List, Dict, Optional
from config.prompt_template import COMMENT_ANALYSIS_PROMPT, REFINEMENT_PROMPT_ADDITION
from src.utils import get_env, extract_json_from_text, ProgressLogger

class CommentAnalyzer:
    def __init__(self, logger: ProgressLogger = None):
        self.client = openai.OpenAI(api_key=get_env("OPENAI_API_KEY"))
        self.logger = logger or ProgressLogger()

    def analyze(
        self,
        video_info: Dict,
        transcript: str,
        comments: List[str],
        refinement_feedback: Optional[str] = None
    ) -> List[Dict]:
        """
        コメントを分析してネタパックを生成

        Args:
            video_info: 動画情報
            transcript: 文字起こし（タイムスタンプ付き）
            comments: 分析対象コメントリスト
            refinement_feedback: 再分析時のフィードバック

        Returns:
            [{
                "元コメント": str,
                "構文タグ": str,
                "いじりポイント": str,
                "ツッコミ例": str,
                "関連シーン": {
                    "タイムスタンプ": str,
                    "シーン説明": str,
                    "関連度": int
                }
            }]
        """
        self.logger.info(f"コメント分析中: {len(comments)}件")

        # コメントを整形
        comments_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(comments)])

        # 基本プロンプト
        prompt = COMMENT_ANALYSIS_PROMPT.format(
            title=video_info['title'],
            url=video_info['url'],
            transcript=transcript[:15000],  # トークン制限対策（約15K文字まで）
            comments=comments_text
        )

        # 再分析の場合はフィードバックを追加
        if refinement_feedback:
            prompt += REFINEMENT_PROMPT_ADDITION.format(
                previous_feedback=refinement_feedback,
                improvement_instructions=refinement_feedback,
                specific_focus_areas="シーンマッチングの精度とツッコミのキレ味"
            )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたはお笑い芸人のツッコミ職人です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # 創造性を確保
                max_tokens=4000
            )

            result_text = response.choices[0].message.content
            result = extract_json_from_text(result_text)

            if isinstance(result, list):
                self.logger.success(f"分析完了: {len(result)}件のネタを抽出")
                return result
            else:
                self.logger.error("分析結果が配列形式ではありません")
                return []

        except Exception as e:
            self.logger.error(f"分析エラー: {str(e)}")
            return []


if __name__ == "__main__":
    # テスト実行
    analyzer = CommentAnalyzer()

    video_info = {
        "title": "女性ドライバーの事故動画",
        "url": "https://youtube.com/watch?v=example"
    }

    transcript = """[0:00] 今日は事故動画を見ていきます
[0:15] こちらをご覧ください
[0:32] 左折しようとしていますが曲がり損ねました
[1:00] 大きな事故にはならなかったようです"""

    comments = [
        "だから女は運転するなって言ってんだよ",
        "これは男でも難しいと思う"
    ]

    result = analyzer.analyze(video_info, transcript, comments)

    print("\n分析結果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
