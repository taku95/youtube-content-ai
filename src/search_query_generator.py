"""
検索ワード生成モジュール
ユーザー入力からYouTube検索ワードを生成
"""
import openai
from typing import List
from config.prompt_template import SEARCH_QUERY_GENERATOR_PROMPT
from src.utils import get_env, extract_json_from_text, ProgressLogger

class SearchQueryGenerator:
    def __init__(self, logger: ProgressLogger = None):
        self.client = openai.OpenAI(api_key=get_env("OPENAI_API_KEY"))
        self.logger = logger or ProgressLogger()

    def generate(self, user_input: str) -> List[str]:
        """
        ユーザー入力から検索ワードリストを生成

        Args:
            user_input: ユーザーの入力文章

        Returns:
            検索ワードのリスト
        """
        self.logger.info(f"検索ワード生成中: '{user_input}'")

        prompt = SEARCH_QUERY_GENERATOR_PROMPT.format(user_input=user_input)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "あなたはYouTube検索のエキスパートです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            result_text = response.choices[0].message.content
            result = extract_json_from_text(result_text)

            if result and "search_queries" in result:
                queries = result["search_queries"]
                self.logger.success(f"{len(queries)}個の検索ワードを生成: {queries}")
                return queries
            else:
                self.logger.error("検索ワードの生成に失敗")
                return []

        except Exception as e:
            self.logger.error(f"検索ワード生成エラー: {str(e)}")
            return []


if __name__ == "__main__":
    # テスト実行
    generator = SearchQueryGenerator()
    queries = generator.generate("炎上している女性ドライバーの事故動画")
    print("生成された検索ワード:")
    for q in queries:
        print(f"  - {q}")
