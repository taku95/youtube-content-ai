"""
CLI インターフェース
YouTubeコメント構文抽出ツール
"""
import argparse
import json
import sys
from src.orchestrator import YouTubeCommentOrchestrator

def main():
    parser = argparse.ArgumentParser(
        description='YouTube Comment Analyzer - YouTuberのネタパック生成ツール'
    )

    parser.add_argument(
        'query',
        type=str,
        help='探したいネタ（例: "炎上している女性ドライバーの事故動画"）'
    )

    parser.add_argument(
        '--max-videos',
        type=int,
        default=3,
        help='検索動画数（クエリあたり）デフォルト: 3'
    )

    parser.add_argument(
        '--max-comments',
        type=int,
        default=200,
        help='取得コメント数 デフォルト: 200'
    )

    parser.add_argument(
        '--quality-threshold',
        type=float,
        default=7.0,
        help='品質スコア閾値 デフォルト: 7.0'
    )

    parser.add_argument(
        '--max-retry',
        type=int,
        default=2,
        help='最大再試行回数 デフォルト: 2'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='outputs',
        help='出力ディレクトリ デフォルト: outputs'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='詳細ログを非表示'
    )

    args = parser.parse_args()

    # 環境変数を設定
    import os
    os.environ["MAX_SEARCH_RESULTS"] = str(args.max_videos)
    os.environ["MAX_COMMENTS_PER_VIDEO"] = str(args.max_comments)
    os.environ["QUALITY_THRESHOLD"] = str(args.quality_threshold)
    os.environ["MAX_RETRY_ATTEMPTS"] = str(args.max_retry)

    # オーケストレーター実行
    orchestrator = YouTubeCommentOrchestrator(verbose=not args.quiet)

    try:
        results = orchestrator.process(args.query)

        if results:
            print("\n" + "=" * 80)
            print("📊 最終結果サマリー")
            print("=" * 80)

            for i, result in enumerate(results, 1):
                print(f"\n【動画 {i}】")
                print(f"タイトル: {result['video_info']['title']}")
                print(f"URL: {result['video_info']['url']}")
                print(f"スクリーニングスコア: {result['screening_result']['score']}/10")
                print(f"品質スコア: {result['evaluation']['total_score']}/10")
                print(f"ネタ数: {len(result['analysis'])}件")
                print(f"試行回数: {result['attempts']}回")

                print(f"\nネタプレビュー:")
                for j, item in enumerate(result['analysis'][:3], 1):  # 最初の3件のみ
                    print(f"  {j}. [{item['構文タグ']}] {item['元コメント'][:40]}...")
                    print(f"     ツッコミ: {item['ツッコミ例']}")

                if len(result['analysis']) > 3:
                    print(f"  ... 他 {len(result['analysis']) - 3}件")

            print("\n" + "=" * 80)
            print(f"✅ 処理完了！ 詳細はoutputsディレクトリのJSONファイルを参照してください")
            print("=" * 80)

            sys.exit(0)
        else:
            print("\n⚠️  ネタになる動画が見つかりませんでした")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n中断されました")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ エラー: {str(e)}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
