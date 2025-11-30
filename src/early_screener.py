"""
早期スクリーニングモジュール
動画がネタになるかを事前判定してコスト削減
"""
import openai
from typing import Dict, List
from config.prompt_template import EARLY_SCREENING_PROMPT
from src.utils import get_env, extract_json_from_text, ProgressLogger

class EarlyScreener:
    def __init__(self, logger: ProgressLogger = None):
        self.client = openai.OpenAI(api_key=get_env("OPENAI_API_KEY"))
        self.logger = logger or ProgressLogger()

    def screen_video(
        self,
        video_info: Dict,
        transcript_sample: str,
        top_comments: List[str],
        threshold: float = 5.0
    ) -> Dict:
        """
        動画がネタになるかスクリーニング

        Args:
            video_info: 動画情報 {"title", "description", ...}
            transcript_sample: 文字起こしサンプル（最初の数分）
            top_comments: 上位コメントリスト
            threshold: 合格スコア閾値

        Returns:
            {
                "passed": True/False,
                "score": スコア,
                "reason": 理由,
                "expected_content": 期待できるネタの種類
            }
        """
        self.logger.info(f"スクリーニング中: {video_info['title']}")

        # コメントを整形
        comments_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(top_comments)])

        prompt = EARLY_SCREENING_PROMPT.format(
            title=video_info['title'],
            description=video_info.get('description', '')[:300],  # 説明文は最初の300文字まで
            transcript_sample=transcript_sample,
            top_comments=comments_text,
            comment_count=len(top_comments)
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # 最高峰モデル使用
                messages=[
                    {"role": "system", "content": "あなたはYouTuberのネタ探しアシスタントです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 判定は安定性重視
                max_tokens=500
            )

            result_text = response.choices[0].message.content
            result = extract_json_from_text(result_text)

            if result:
                score = result.get("ネタ化可能性スコア", 0)
                passed = score >= threshold and result.get("推奨") == "continue"

                screening_result = {
                    "passed": passed,
                    "score": score,
                    "reason": result.get("理由", ""),
                    "expected_content": result.get("期待できるネタの種類", ""),
                    "recommendation": result.get("推奨", "skip")
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
        threshold: float = 5.0
    ) -> List[Dict]:
        """
        複数動画をスクリーニングして合格動画のみ返す

        Args:
            videos_data: [{
                "video_info": 動画情報,
                "transcript_sample": 文字起こしサンプル,
                "top_comments": コメントリスト
            }]
            threshold: 合格スコア閾値

        Returns:
            合格した動画データのリスト
        """
        passed_videos = []

        for data in videos_data:
            result = self.screen_video(
                data['video_info'],
                data['transcript_sample'],
                data['top_comments'],
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
        "description": "様々な事故の瞬間を集めました"
    }

    transcript_sample = "[0:00] 今日は事故の瞬間を見ていきます [0:05] まずはこちらの映像をご覧ください..."

    top_comments = [
        "だから女は運転するなって言ってんだよ",
        "これは男でも無理だろ",
        "運転下手すぎて草"
    ]

    result = screener.screen_video(video_info, transcript_sample, top_comments)
    print(f"\nスクリーニング結果: {result}")
