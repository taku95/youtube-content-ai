"""
早期スクリーニングモジュール（コメントのみ版）
コメントの面白さだけでスクリーニングしてコスト削減
"""
import openai
from typing import Dict, List
from config.prompt_template import COMMENT_SCREENING_PROMPT
from src.utils import get_env, extract_json_from_text, ProgressLogger

class EarlyScreener:
    def __init__(self, logger: ProgressLogger = None):
        self.client = openai.OpenAI(api_key=get_env("OPENAI_API_KEY"))
        self.logger = logger or ProgressLogger()

    def screen_comments(
        self,
        video_info: Dict,
        comments: List[str],
        threshold: float = 6.0
    ) -> Dict:
        """
        コメントの面白さだけでスクリーニング（動画内容は見ない）

        Args:
            video_info: 動画情報 {"title", "channel_title", ...}
            comments: 全コメントリスト
            threshold: 合格スコア閾値（デフォルト6.0）

        Returns:
            {
                "passed": True/False,
                "score": スコア,
                "reason": 理由,
                "example_comments": サンプルコメント,
                "expected_content_type": 期待できるネタの種類
            }
        """
        self.logger.info(f"コメントスクリーニング中: {video_info['title']}")

        # コメントを整形
        comments_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(comments)])

        prompt = COMMENT_SCREENING_PROMPT.format(
            title=video_info['title'],
            channel_title=video_info.get('channel_title', '不明'),
            comments=comments_text,
            comment_count=len(comments)
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # 最高峰モデル使用
                messages=[
                    {"role": "system", "content": "あなたはYouTuberのネタ探しエージェントです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 判定は安定性重視
                max_tokens=500
            )

            result_text = response.choices[0].message.content
            result = extract_json_from_text(result_text)

            if result:
                score = result.get("score", 0)
                passed = result.get("passed", False) and score >= threshold

                screening_result = {
                    "passed": passed,
                    "score": score,
                    "reason": result.get("reason", ""),
                    "example_comments": result.get("example_comments", []),
                    "expected_content_type": result.get("expected_content_type", "")
                }

                if passed:
                    self.logger.success(f"✅ 合格 (スコア: {score}/10) - {screening_result['reason'][:50]}...")
                else:
                    self.logger.warning(f"❌ 不合格 (スコア: {score}/10) - スキップします")

                return screening_result
            else:
                self.logger.error("スクリーニング結果のパースに失敗")
                return {"passed": False, "score": 0, "reason": "解析エラー"}

        except Exception as e:
            self.logger.error(f"スクリーニングエラー: {str(e)}")
            return {"passed": False, "score": 0, "reason": str(e)}

    def screen_multiple_videos(
        self,
        videos_data: List[Dict],
        threshold: float = 6.0
    ) -> List[Dict]:
        """
        複数動画をコメントでスクリーニングして合格動画のみ返す

        Args:
            videos_data: [{
                "video_info": 動画情報,
                "comments": コメントリスト
            }]
            threshold: 合格スコア閾値

        Returns:
            合格した動画データのリスト
        """
        passed_videos = []

        for data in videos_data:
            result = self.screen_comments(
                data['video_info'],
                data['comments'],
                threshold
            )

            if result['passed']:
                data['screening_result'] = result
                passed_videos.append(data)

        self.logger.success(f"スクリーニング完了: {len(passed_videos)}/{len(videos_data)}件が合格")
        return passed_videos


if __name__ == "__main__":
    # テスト実行
    screener = EarlyScreener()

    # サンプルデータ
    video_info = {
        "title": "女性ドライバーの衝撃事故集",
        "channel_title": "交通安全チャンネル"
    }

    comments = [
        "だから女は運転するなって言ってんだよ",
        "これは男でも無理だろ",
        "運転下手すぎて草",
        "女性差別やめろ",
        "これだから最近の若者は...",
        "完全に信号無視じゃん",
        "免許返納しろよマジで"
    ]

    result = screener.screen_comments(video_info, comments)
    print(f"\nスクリーニング結果: {result}")
