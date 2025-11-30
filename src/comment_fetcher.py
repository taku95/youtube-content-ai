"""
YouTubeコメント取得モジュール
"""
from googleapiclient.discovery import build
from typing import List, Dict
from src.utils import get_env, ProgressLogger

class CommentFetcher:
    def __init__(self, logger: ProgressLogger = None):
        self.api_key = get_env("YOUTUBE_API_KEY")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.logger = logger or ProgressLogger()

    def fetch_comments(
        self,
        video_id: str,
        max_results: int = 100,
        order: str = "relevance"
    ) -> List[Dict]:
        """
        動画のコメントを取得

        Args:
            video_id: YouTube動画ID
            max_results: 最大取得件数
            order: "time" (新しい順) or "relevance" (関連度順)

        Returns:
            [{
                "text": "コメント本文",
                "author": "投稿者名",
                "like_count": いいね数,
                "published_at": "投稿日時",
                "reply_count": 返信数
            }]
        """
        self.logger.info(f"コメント取得中: {video_id} (最大{max_results}件)")

        comments = []
        next_page_token = None

        try:
            while len(comments) < max_results:
                request = self.youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=min(100, max_results - len(comments)),
                    order=order,
                    pageToken=next_page_token,
                    textFormat="plainText"
                )

                response = request.execute()

                for item in response.get('items', []):
                    top_comment = item['snippet']['topLevelComment']['snippet']

                    comment_data = {
                        "text": top_comment['textDisplay'],
                        "author": top_comment['authorDisplayName'],
                        "like_count": top_comment.get('likeCount', 0),
                        "published_at": top_comment['publishedAt'],
                        "reply_count": item['snippet'].get('totalReplyCount', 0)
                    }

                    comments.append(comment_data)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            self.logger.success(f"{len(comments)}件のコメントを取得")
            return comments

        except Exception as e:
            self.logger.error(f"コメント取得エラー: {str(e)}")
            return comments  # 取得できた分だけ返す

    def get_top_comments(
        self,
        video_id: str,
        count: int = 20
    ) -> List[str]:
        """
        上位N件のコメントテキストのみを取得

        Args:
            video_id: YouTube動画ID
            count: 取得件数

        Returns:
            コメントテキストのリスト
        """
        comments = self.fetch_comments(video_id, max_results=count, order="relevance")
        return [c['text'] for c in comments]

    def get_comments_summary(
        self,
        video_id: str
    ) -> Dict:
        """
        コメント統計情報を取得

        Args:
            video_id: YouTube動画ID

        Returns:
            {
                "total_comments": 総コメント数,
                "avg_like_count": 平均いいね数,
                "top_liked_comment": 最もいいねが多いコメント
            }
        """
        comments = self.fetch_comments(video_id, max_results=100)

        if not comments:
            return {"total_comments": 0}

        total_likes = sum(c['like_count'] for c in comments)
        top_liked = max(comments, key=lambda c: c['like_count'])

        return {
            "total_comments": len(comments),
            "avg_like_count": total_likes / len(comments) if comments else 0,
            "top_liked_comment": top_liked['text'],
            "top_liked_count": top_liked['like_count']
        }


if __name__ == "__main__":
    # テスト実行
    fetcher = CommentFetcher()

    # 実際の動画IDでテスト（存在する動画IDに置き換えてください）
    video_id = "dQw4w9WgXcQ"
    comments = fetcher.fetch_comments(video_id, max_results=10)

    print(f"\n取得したコメント ({len(comments)}件):")
    for i, comment in enumerate(comments[:5], 1):
        print(f"{i}. {comment['text'][:50]}...")
        print(f"   👍 {comment['like_count']} | 💬 {comment['reply_count']}")
