"""
オーケストレーターモジュール
全処理フローを統合し、自己改善ループを管理
"""
from typing import Dict, List, Optional
from src.search_query_generator import SearchQueryGenerator
from src.youtube_search import YouTubeSearcher
from src.transcript_fetcher import TranscriptFetcher
from src.comment_fetcher import CommentFetcher
from src.early_screener import EarlyScreener
from src.comment_filter import CommentFilter
from src.comment_analyzer import CommentAnalyzer
from src.quality_evaluator import QualityEvaluator
from src.utils import get_env, save_json, ProgressLogger

class YouTubeCommentOrchestrator:
    """全処理を統括するメインオーケストレーター"""

    def __init__(self, verbose: bool = True):
        self.logger = ProgressLogger(verbose=verbose)

        # 各モジュール初期化
        self.query_generator = SearchQueryGenerator(self.logger)
        self.searcher = YouTubeSearcher(self.logger)
        self.transcript_fetcher = TranscriptFetcher(self.logger)
        self.comment_fetcher = CommentFetcher(self.logger)
        self.screener = EarlyScreener(self.logger)
        self.comment_filter = CommentFilter(self.logger)
        self.analyzer = CommentAnalyzer(self.logger)
        self.evaluator = QualityEvaluator(self.logger)

        # 設定読み込み
        self.max_search_results = int(get_env("MAX_SEARCH_RESULTS", "3"))
        self.max_comments = int(get_env("MAX_COMMENTS_PER_VIDEO", "200"))
        self.screening_comments = int(get_env("EARLY_SCREENING_COMMENTS", "20"))
        self.filtered_comments = int(get_env("FILTERED_COMMENTS", "50"))
        self.quality_threshold = float(get_env("QUALITY_THRESHOLD", "7.0"))
        self.max_retry = int(get_env("MAX_RETRY_ATTEMPTS", "2"))

    def process(self, user_input: str) -> List[Dict]:
        """
        メイン処理フロー

        Args:
            user_input: ユーザーの入力文章

        Returns:
            ネタパックのリスト
        """
        self.logger.log("=" * 60)
        self.logger.log("🎬 YouTube Comment Analyzer 開始")
        self.logger.log("=" * 60)

        # Step 1: 検索ワード生成
        self.logger.log("\n📝 Step 1: 検索ワード生成")
        search_queries = self.query_generator.generate(user_input)
        if not search_queries:
            self.logger.error("検索ワードの生成に失敗しました")
            return []

        # Step 2: YouTube動画検索
        self.logger.log("\n🔍 Step 2: YouTube動画検索")
        videos = self.searcher.search_multiple_queries(
            search_queries,
            max_results_per_query=self.max_search_results
        )
        if not videos:
            self.logger.error("動画が見つかりませんでした")
            return []

        # Step 3: 早期スクリーニング
        self.logger.log("\n🎯 Step 3: 早期スクリーニング")
        screened_videos = self._screen_videos(videos)
        if not screened_videos:
            self.logger.warning("ネタになる動画が見つかりませんでした")
            return []

        # Step 4: 各動画の詳細分析
        self.logger.log("\n🤖 Step 4: 詳細分析開始")
        all_results = []
        for video_data in screened_videos:
            result = self._analyze_video(video_data)
            if result:
                all_results.append(result)

        # Step 5: 結果保存
        if all_results:
            self.logger.log("\n💾 Step 5: 結果保存")
            filepath = save_json(all_results, "analysis_result")
            self.logger.success(f"結果を保存しました: {filepath}")

        self.logger.log("\n" + "=" * 60)
        self.logger.success(f"✅ 処理完了！ {len(all_results)}件のネタパックを生成")
        self.logger.log("=" * 60)

        return all_results

    def _screen_videos(self, videos: List[Dict]) -> List[Dict]:
        """動画を早期スクリーニング"""
        screened_videos = []

        for video in videos:
            # 文字起こしサンプル取得（最初の3分）
            transcript_sample = self.transcript_fetcher.get_transcript_text(
                video['video_id'],
                max_duration=180
            )

            if not transcript_sample:
                self.logger.warning(f"字幕なし、スキップ: {video['title']}")
                continue

            # 上位コメント取得
            top_comments = self.comment_fetcher.get_top_comments(
                video['video_id'],
                count=self.screening_comments
            )

            if not top_comments:
                self.logger.warning(f"コメントなし、スキップ: {video['title']}")
                continue

            # スクリーニング実行
            screening_result = self.screener.screen_video(
                video,
                transcript_sample,
                top_comments
            )

            if screening_result['passed']:
                screened_videos.append({
                    "video_info": video,
                    "screening_result": screening_result
                })

        return screened_videos

    def _analyze_video(self, video_data: Dict) -> Optional[Dict]:
        """1つの動画を詳細分析（自己改善ループ付き）"""
        video_info = video_data['video_info']
        self.logger.log(f"\n📹 分析中: {video_info['title']}")

        # 全文字起こし取得
        transcript = self.transcript_fetcher.get_transcript_with_timestamps(
            video_info['video_id']
        )
        if not transcript:
            self.logger.error("文字起こしの取得に失敗")
            return None

        # 全コメント取得
        comments_data = self.comment_fetcher.fetch_comments(
            video_info['video_id'],
            max_results=self.max_comments
        )
        comments = [c['text'] for c in comments_data]

        # コメントフィルタリング
        filtered_comments = self.comment_filter.filter_comments(
            comments,
            target_count=self.filtered_comments
        )

        # 自己改善ループ
        attempt = 1
        analysis_result = None
        refinement_feedback = None

        while attempt <= self.max_retry:
            self.logger.info(f"分析試行 {attempt}/{self.max_retry}")

            # コメント分析
            analysis_result = self.analyzer.analyze(
                video_info,
                transcript,
                filtered_comments,
                refinement_feedback=refinement_feedback
            )

            if not analysis_result:
                self.logger.error("分析に失敗しました")
                break

            # 品質評価
            evaluation = self.evaluator.evaluate(
                analysis_result,
                threshold=self.quality_threshold
            )

            if evaluation['passed']:
                self.logger.success(f"✅ 品質評価合格 (試行{attempt}回目)")
                return {
                    "video_info": video_info,
                    "screening_result": video_data['screening_result'],
                    "analysis": analysis_result,
                    "evaluation": evaluation,
                    "attempts": attempt
                }
            else:
                if attempt < self.max_retry:
                    self.logger.warning(f"品質不足、再分析します (試行{attempt + 1}回目)")
                    refinement_feedback = evaluation['feedback']
                    attempt += 1
                else:
                    self.logger.warning("最大試行回数に達しました。現在の結果を返します")
                    return {
                        "video_info": video_info,
                        "screening_result": video_data['screening_result'],
                        "analysis": analysis_result,
                        "evaluation": evaluation,
                        "attempts": attempt,
                        "warning": "品質基準未達成"
                    }

        return None


if __name__ == "__main__":
    # テスト実行
    orchestrator = YouTubeCommentOrchestrator(verbose=True)
    results = orchestrator.process("炎上している女性ドライバーの事故動画")

    if results:
        print("\n" + "=" * 60)
        print("最終結果:")
        print("=" * 60)
        for i, result in enumerate(results, 1):
            print(f"\n【動画{i}】{result['video_info']['title']}")
            print(f"スクリーニングスコア: {result['screening_result']['score']}/10")
            print(f"品質スコア: {result['evaluation']['total_score']}/10")
            print(f"ネタ数: {len(result['analysis'])}件")
            print(f"分析試行回数: {result['attempts']}回")
