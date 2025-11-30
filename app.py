"""
Streamlit UI
YouTubeコメント構文抽出ツール
"""
import streamlit as st
import json
from src.orchestrator import YouTubeCommentOrchestrator

st.set_page_config(
    page_title="YouTube Comment Analyzer",
    page_icon="🎯",
    layout="wide"
)

# タイトル
st.title("🎯 YouTubeコメント構文抽出ツール")
st.markdown("**YouTuberが喋るだけで動画になる「ネタパック」を自動生成**")

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")

    st.markdown("### API設定")
    st.info("`.env`ファイルでAPIキーを設定してください")

    st.markdown("### 処理設定")
    max_videos = st.slider("検索動画数（クエリあたり）", 1, 5, 3)
    max_comments = st.slider("取得コメント数", 50, 300, 200)
    quality_threshold = st.slider("品質スコア閾値", 5.0, 9.0, 7.0, 0.5)
    max_retry = st.slider("最大再試行回数", 1, 5, 2)

    st.markdown("---")
    st.markdown("### 💡 使い方")
    st.markdown("""
    1. 探したいネタを文章で入力
    2. 「分析開始」をクリック
    3. AIが自動で動画を検索・分析
    4. ネタパックが生成されます！
    """)

# メイン
input_text = st.text_area(
    "探したいネタを入力してください",
    placeholder="例: 炎上している女性ドライバーの事故動画",
    height=100
)

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    analyze_button = st.button("🚀 分析開始", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ クリア", use_container_width=True)

if clear_button:
    st.rerun()

if analyze_button:
    if not input_text:
        st.error("テキストを入力してください")
    else:
        # 環境変数を一時的に上書き
        import os
        os.environ["MAX_SEARCH_RESULTS"] = str(max_videos)
        os.environ["MAX_COMMENTS_PER_VIDEO"] = str(max_comments)
        os.environ["QUALITY_THRESHOLD"] = str(quality_threshold)
        os.environ["MAX_RETRY_ATTEMPTS"] = str(max_retry)

        # プログレスバー
        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.spinner("処理中..."):
            try:
                # オーケストレーター実行
                orchestrator = YouTubeCommentOrchestrator(verbose=False)

                status_text.text("検索ワード生成中...")
                progress_bar.progress(20)

                results = orchestrator.process(input_text)

                progress_bar.progress(100)
                status_text.text("完了！")

                if results:
                    st.success(f"✅ {len(results)}件のネタパックを生成しました！")

                    # 結果表示
                    for i, result in enumerate(results, 1):
                        with st.expander(f"📹 動画 {i}: {result['video_info']['title']}", expanded=True):
                            # 動画情報
                            col_a, col_b = st.columns([2, 1])

                            with col_a:
                                st.markdown(f"**チャンネル:** {result['video_info']['channel_title']}")
                                st.markdown(f"**URL:** {result['video_info']['url']}")

                                # 動画埋め込み
                                video_id = result['video_info']['video_id']
                                st.video(f"https://www.youtube.com/watch?v={video_id}")

                            with col_b:
                                st.markdown("### 📊 スコア")
                                st.metric("スクリーニング", f"{result['screening_result']['score']}/10")
                                st.metric("品質評価", f"{result['evaluation']['total_score']}/10")
                                st.metric("ネタ数", len(result['analysis']))
                                st.metric("試行回数", result['attempts'])

                            # ネタパック表示
                            st.markdown("### 🎯 ネタパック")

                            # 構文タグでグループ化
                            tags = list(set([item['構文タグ'] for item in result['analysis']]))
                            tabs = st.tabs(tags)

                            for tab, tag in zip(tabs, tags):
                                with tab:
                                    filtered_items = [item for item in result['analysis'] if item['構文タグ'] == tag]

                                    for item in filtered_items:
                                        with st.container():
                                            st.markdown(f"**💬 コメント:** {item['元コメント']}")
                                            st.markdown(f"**🎭 いじりポイント:** {item['いじりポイント']}")
                                            st.markdown(f"**💥 ツッコミ例:** _{item['ツッコミ例']}_")

                                            if 'related_scene' in item or '関連シーン' in item:
                                                scene = item.get('関連シーン', item.get('related_scene', {}))
                                                st.markdown(f"**🎬 関連シーン:** [{scene.get('タイムスタンプ', 'N/A')}] {scene.get('シーン説明', '')}")
                                                st.markdown(f"**🔗 関連度:** {scene.get('関連度', 'N/A')}/10")

                                            st.markdown("---")

                            # JSON出力
                            with st.expander("📄 JSON出力"):
                                st.json(result['analysis'])

                else:
                    st.warning("ネタになる動画が見つかりませんでした。別のキーワードで試してください。")

            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.exception(e)

else:
    # 初期表示
    st.info("👆 上のテキストボックスにネタを入力して「分析開始」をクリックしてください")

    # サンプル例
    with st.expander("💡 入力例"):
        st.markdown("""
        - 炎上している女性ドライバーの事故動画
        - ゲーム実況で暴言を吐いている配信者
        - DIY失敗動画
        - 料理の失敗動画
        - 迷惑系YouTuberの動画
        """)
