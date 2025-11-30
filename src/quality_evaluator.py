"""
品質評価モジュール
GPT-4oで分析結果の品質を評価
"""
import openai
import json
from typing import Dict, List
from config.prompt_template import QUALITY_EVALUATION_PROMPT
from src.utils import get_env, extract_json_from_text, ProgressLogger

class QualityEvaluator:
    def __init__(self, logger: ProgressLogger = None):
        self.client = openai.OpenAI(api_key=get_env("OPENAI_API_KEY"))
        self.logger = logger or ProgressLogger()

    def evaluate(
        self,
        analysis_result: List[Dict],
        threshold: float = 7.0
    ) -> Dict:
        """
        分析結果の品質を評価

        Args:
            analysis_result: コメント分析結果
            threshold: 合格スコア閾値

        Returns:
            {
                "passed": True/False,
                "total_score": 総合スコア,
                "individual_scores": 個別スコア,
                "improvements": 改善ポイント,
                "feedback": 次回への指示,
                "strengths": 優れている点
            }
        """
        self.logger.info("品質評価中...")

        # 分析結果をJSON文字列に
        analysis_json = json.dumps(analysis_result, ensure_ascii=False, indent=2)

        prompt = QUALITY_EVALUATION_PROMPT.format(
            analysis_result=analysis_json,
            threshold=threshold
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # 最高峰モデルで厳しく評価
                messages=[
                    {"role": "system", "content": "あなたは人気YouTuberのディレクター兼お笑いプロデューサーです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 評価は安定性重視
                max_tokens=1500
            )

            result_text = response.choices[0].message.content
            result = extract_json_from_text(result_text)

            if result:
                total_score = result.get("総合スコア", 0)
                passed = result.get("合格判定", False)

                evaluation = {
                    "passed": passed,
                    "total_score": total_score,
                    "individual_scores": result.get("個別スコア", {}),
                    "improvements": result.get("改善ポイント", []),
                    "feedback": result.get("次回への指示", ""),
                    "strengths": result.get("優れている点", [])
                }

                if passed:
                    self.logger.success(f"✅ 品質評価合格 (スコア: {total_score}/10)")
                else:
                    self.logger.warning(f"⚠️  品質評価不合格 (スコア: {total_score}/10) - 再分析を推奨")

                # 詳細ログ
                if evaluation['improvements']:
                    self.logger.info("改善ポイント:")
                    for imp in evaluation['improvements']:
                        self.logger.info(f"  - {imp}")

                return evaluation
            else:
                self.logger.error("評価結果のパースに失敗")
                return {
                    "passed": False,
                    "total_score": 0,
                    "improvements": ["評価エラー"],
                    "feedback": ""
                }

        except Exception as e:
            self.logger.error(f"品質評価エラー: {str(e)}")
            return {
                "passed": False,
                "total_score": 0,
                "improvements": [str(e)],
                "feedback": ""
            }


if __name__ == "__main__":
    # テスト実行
    evaluator = QualityEvaluator()

    sample_result = [
        {
            "元コメント": "だから女は運転するなって言ってんだよ",
            "構文タグ": "差別",
            "いじりポイント": "性別で十把一絡げにしてる時点で無理筋",
            "ツッコミ例": "まずお前が免許返納してから言え",
            "関連シーン": {
                "タイムスタンプ": "0:32",
                "シーン説明": "女性が左折しようとして曲がり損ねたシーン",
                "関連度": 8
            }
        }
    ]

    evaluation = evaluator.evaluate(sample_result)
    print("\n評価結果:")
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))
