"""
YouTube動画検索モジュール
Creative Commons動画のみを対象
"""
from googleapiclient.discovery import build
from typing import List, Dict, Optional
from src.utils import get_env, ProgressLogger

class YouTubeSearcher:
    def __init__(self, logger: ProgressLogger = None):
        self.api_key = get_env("YOUTUBE_API_KEY")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.logger = logger or ProgressLogger()

    def search_videos(
        self,
        query: str,
        max_results: int = 3,
        video_license: str = "creativeCommon"
    ) -> List[Dict]:
        """
        YouTube動画を検索

        Args:
            query: 検索ワード
            max_results: 最大取得件数
            video_license: "creativeCommon" または "youtube"

        Returns:
            動画情報のリスト
        """
        self.logger.info(f"YouTube検索中: '{query}'")

        try:
            request = self.youtube.search().list(
                part="id,snippet",
                q=query,
                type="video",
                videoLicense=video_license,
                maxResults=max_results,
                order="relevance",
                relevanceLanguage="ja"
            )

            response = request.execute()

            videos = []
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']

                video_info = {
                    "video_id": video_id,
                    "title": snippet['title'],
                    "description": snippet['description'],
                    "channel_title": snippet['channelTitle'],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url']
                }

                videos.append(video_info)

            self.logger.success(f"{len(videos)}件の動画を取得")
            return videos

        except Exception as e:
            self.logger.error(f"YouTube検索エラー: {str(e)}")
            return []

    def search_multiple_queries(
        self,
        queries: List[str],
        max_results_per_query: int = 3
    ) -> List[Dict]:
        """
        複数の検索ワードで動画を検索

        Args:
            queries: 検索ワードのリスト
            max_results_per_query: 各クエリあたりの最大取得件数

        Returns:
            全動画情報のリスト（重複除去済み）
        """
        all_videos = []
        video_ids_seen = set()

        for query in queries:
            videos = self.search_videos(query, max_results=max_results_per_query)

            for video in videos:
                if video['video_id'] not in video_ids_seen:
                    all_videos.append(video)
                    video_ids_seen.add(video['video_id'])

        self.logger.success(f"合計{len(all_videos)}件のユニーク動画を取得")
        return all_videos


if __name__ == "__main__":
    # テスト実行
    searcher = YouTubeSearcher()
    videos = searcher.search_videos("面白い ハプニング")

    print("\n検索結果:")
    for v in videos:
        print(f"  - {v['title']}")
        print(f"    URL: {v['url']}")
