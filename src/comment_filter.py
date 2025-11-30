"""
コメントフィルタリングモジュール
GPT-3.5で大量コメントから候補を絞る
"""
import openai
from typing import List
from config.prompt_template import COMMENT_FILTERING_PROMPT
from src.utils import get_env, extract_json_from_text, ProgressLogger

class CommentFilter:
    def __init__(self, logger: ProgressLogger = None):
        self.client = openai.OpenAI(api_key=get_env("OPENAI_API_KEY"))
        self.logger = logger or ProgressLogger()

    def filter_comments(
        self,
        comments: List[str],
        target_count: int = 50
    ) -> List[str]:
        """
        コメントをフィルタリングして候補を絞る

        Args:
            comments: コメントリスト
            target_count: 目標件数

        Returns:
            フィルタリングされたコメントリスト
        """
        if len(comments) <= target_count:
            self.logger.info(f"コメント数が目標以下のためフィルタリングスキップ ({len(comments)}件)")
            return comments

        self.logger.info(f"コメントフィルタリング中: {len(comments)}件 → {target_count}件")

        # コメントを整形
        comments_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(comments)])

        prompt = COMMENT_FILTERING_PROMPT.format(
            comments=comments_text,
            target_count=target_count
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # コスト削減のためGPT-3.5使用
                messages=[
                    {"role": "system", "content": "あなたはお笑い芸人のネタ選びアシスタントです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content
            result = extract_json_from_text(result_text)

            if result and "selected_comments" in result:
                selected = result["selected_comments"]
                self.logger.success(f"フィルタリング完了: {len(selected)}件を選出")
                return selected
            else:
                self.logger.warning("フィルタリング結果のパースに失敗、元のコメントを返します")
                return comments[:target_count]

        except Exception as e:
            self.logger.error(f"フィルタリングエラー: {str(e)}")
            # エラー時は単純に上位N件を返す
            return comments[:target_count]


if __name__ == "__main__":
    # テスト実行
    filter_module = CommentFilter()

    sample_comments = [
        "面白かったです",
        "だから女は運転するなって言ってんだよ",
        "これ見て勉強になった",
        "運転下手すぎて草",
        "いい動画ですね",
        "こんなの誰でもできる（できない）",
        "参考になりました"
    ]

    filtered = filter_module.filter_comments(sample_comments, target_count=3)
    print("\nフィルタリング結果:")
    for c in filtered:
        print(f"  - {c}")
