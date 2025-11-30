# 🔧 技術仕様書

## 📋 目次
1. [システムアーキテクチャ](#システムアーキテクチャ)
2. [モジュール詳細](#モジュール詳細)
3. [データフロー](#データフロー)
4. [API仕様](#api仕様)
5. [環境変数](#環境変数)
6. [エラーハンドリング](#エラーハンドリング)
7. [パフォーマンス最適化](#パフォーマンス最適化)

---

## システムアーキテクチャ

### 全体構成図

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│  ┌──────────────┐              ┌──────────────┐         │
│  │ Streamlit UI │              │  CLI Tool    │         │
│  └──────┬───────┘              └──────┬───────┘         │
│         │                              │                 │
│         └──────────────┬───────────────┘                 │
│                        │                                 │
└────────────────────────┼─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                   Orchestrator                           │
│  (全処理フローの統括 + 自己改善ループ管理)                 │
└────────────────────────┬─────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌───▼────┐ ┌───────▼────────┐
│  Search Query   │ │YouTube │ │ Early Screener │
│   Generator     │ │Searcher│ │   (GPT-4o)     │
│  (GPT-4 Turbo)  │ │        │ │                │
└────────┬────────┘ └───┬────┘ └───────┬────────┘
         │              │               │
         └──────────────┼───────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
┌────────▼────────┐ ┌──▼──────┐ ┌────▼─────────┐
│  Transcript     │ │Comment  │ │Comment Filter│
│   Fetcher       │ │ Fetcher │ │ (GPT-3.5)    │
└────────┬────────┘ └────┬────┘ └────┬─────────┘
         │               │            │
         └───────────────┼────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌───▼──────────┐ ┌─▼──────────┐
│Comment Analyzer │ │   Quality    │ │  Outputs   │
│ (GPT-4 Turbo)   │ │  Evaluator   │ │   (JSON)   │
│                 │ │  (GPT-4o)    │ │            │
└─────────────────┘ └──────────────┘ └────────────┘
```

### レイヤー構成

```
┌─────────────────────────────────────┐
│   Presentation Layer                │
│   - Streamlit UI (app.py)           │
│   - CLI (cli.py)                    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Orchestration Layer               │
│   - Orchestrator (orchestrator.py)  │
│     - フロー制御                      │
│     - 自己改善ループ                  │
│     - エラーハンドリング               │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Business Logic Layer              │
│   - Search Query Generator          │
│   - Early Screener                  │
│   - Comment Analyzer                │
│   - Quality Evaluator               │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Data Access Layer                 │
│   - YouTube Search                  │
│   - Transcript Fetcher              │
│   - Comment Fetcher                 │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   External Services                 │
│   - YouTube Data API v3             │
│   - OpenAI API (GPT-4o/4/3.5)       │
│   - youtube-transcript-api          │
└─────────────────────────────────────┘
```

---

## モジュール詳細

### 1. SearchQueryGenerator
**責務:** ユーザー入力から検索ワードを生成

```python
class SearchQueryGenerator:
    def generate(user_input: str) -> List[str]
```

**使用モデル:** GPT-4 Turbo
**入力:** ユーザーの1文入力
**出力:** 検索ワードリスト（3-5件）
**処理時間:** 約3-5秒
**コスト:** 約5円

---

### 2. YouTubeSearcher
**責務:** YouTube動画検索（CC動画のみ）

```python
class YouTubeSearcher:
    def search_videos(query: str, max_results: int) -> List[Dict]
    def search_multiple_queries(queries: List[str]) -> List[Dict]
```

**API:** YouTube Data API v3
**フィルター:** `videoLicense=creativeCommon`
**取得情報:**
- video_id
- title
- description
- channel_title
- thumbnail
- url

**APIコスト:** 1クエリ = 100ユニット（無料枠内）

---

### 3. EarlyScreener ⭐
**責務:** 動画のネタ化可能性を事前判定

```python
class EarlyScreener:
    def screen_video(
        video_info: Dict,
        transcript_sample: str,
        top_comments: List[str],
        threshold: float = 5.0
    ) -> Dict
```

**使用モデル:** GPT-4o（最高峰）
**入力:**
- 動画情報
- 文字起こしサンプル（最初の3分）
- 上位20コメント

**出力:**
```json
{
  "passed": true/false,
  "score": 8.0,
  "reason": "判定理由",
  "expected_content": "期待できるネタの種類"
}
```

**処理時間:** 約5-10秒
**コスト:** 約3円
**効果:** 無駄な動画を70%削減

---

### 4. TranscriptFetcher
**責務:** YouTube自動字幕の取得

```python
class TranscriptFetcher:
    def fetch_transcript(video_id: str) -> List[Dict]
    def get_transcript_text(video_id: str, max_duration: float) -> str
    def get_transcript_with_timestamps(video_id: str) -> str
```

**データソース:** youtube-transcript-api
**対応言語:** 日本語、英語（優先順）
**出力形式:**
```python
[{
    "text": "テキスト",
    "start": 0.0,
    "duration": 2.5,
    "timestamp": "0:00"
}]
```

**コスト:** 無料

---

### 5. CommentFetcher
**責務:** YouTubeコメントの取得

```python
class CommentFetcher:
    def fetch_comments(
        video_id: str,
        max_results: int = 100,
        order: str = "relevance"
    ) -> List[Dict]
```

**API:** YouTube Data API v3
**取得順序:** relevance（関連度順）
**取得情報:**
- text
- author
- like_count
- published_at
- reply_count

**APIコスト:** 100コメント = 1ユニット

---

### 6. CommentFilter
**責務:** 大量コメントから候補を絞る

```python
class CommentFilter:
    def filter_comments(
        comments: List[str],
        target_count: int = 50
    ) -> List[str]
```

**使用モデル:** GPT-3.5 Turbo（コスト削減）
**処理:** 200件 → 50件
**基準:**
- 論理的矛盾
- 暴走
- 意味不明
- 謎マウント
- 差別的（ツッコミ対象）

**コスト:** 約5円

---

### 7. CommentAnalyzer ⭐
**責務:** 構文抽出とシーンマッチング

```python
class CommentAnalyzer:
    def analyze(
        video_info: Dict,
        transcript: str,
        comments: List[str],
        refinement_feedback: Optional[str] = None
    ) -> List[Dict]
```

**使用モデル:** GPT-4 Turbo
**入力:**
- 動画情報
- 文字起こし（全文、タイムスタンプ付き）
- フィルタ済みコメント（50件）
- 改善フィードバック（再分析時）

**出力:**
```json
[{
  "元コメント": "コメント本文",
  "構文タグ": "差別/暴走/意味不明/etc",
  "いじりポイント": "矛盾点の指摘",
  "ツッコミ例": "短く鋭い一言",
  "関連シーン": {
    "タイムスタンプ": "0:32",
    "シーン説明": "動画内容の説明",
    "関連度": 8
  }
}]
```

**処理時間:** 30-60秒
**コスト:** 約20円

---

### 8. QualityEvaluator ⭐
**責務:** 分析結果の品質評価

```python
class QualityEvaluator:
    def evaluate(
        analysis_result: List[Dict],
        threshold: float = 7.0
    ) -> Dict
```

**使用モデル:** GPT-4o（最高峰）
**評価軸:**
1. シーンマッチング精度（最重要）
2. ネタとしての成立度
3. 実用性
4. 構文の質

**出力:**
```json
{
  "passed": true/false,
  "total_score": 7.5,
  "individual_scores": {
    "シーンマッチング": 8,
    "ネタ成立度": 7,
    "実用性": 8,
    "構文の質": 7
  },
  "improvements": ["改善点1", "改善点2"],
  "feedback": "次回への指示",
  "strengths": ["良い点1", "良い点2"]
}
```

**処理時間:** 10-15秒
**コスト:** 約5円

---

### 9. Orchestrator ⭐
**責務:** 全処理フローの統括

```python
class YouTubeCommentOrchestrator:
    def process(user_input: str) -> List[Dict]

    # 内部メソッド
    def _screen_videos(videos: List[Dict]) -> List[Dict]
    def _analyze_video(video_data: Dict) -> Optional[Dict]
```

**主要機能:**
1. 各モジュールの初期化
2. 処理フローの制御
3. 自己改善ループの管理
4. エラーハンドリング
5. ログ出力
6. 結果の保存

**自己改善ループ:**
```python
attempt = 1
while attempt <= max_retry:
    analysis = analyzer.analyze(...)
    evaluation = evaluator.evaluate(analysis)

    if evaluation['passed']:
        return result  # 成功
    else:
        refinement_feedback = evaluation['feedback']
        attempt += 1  # 再試行
```

---

## データフロー

### 完全なデータフロー図

```
[ユーザー入力]
  "炎上している女性ドライバーの事故動画"
    ↓
┌─────────────────────────────────────┐
│ 1. 検索ワード生成 (GPT-4 Turbo)     │
│    Input: ユーザー入力               │
│    Output: ["女性ドライバー 事故",   │
│             "煽り運転 女",           │
│             "運転 下手"]             │
│    Time: 3-5秒                       │
│    Cost: ~5円                        │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 2. YouTube検索 (YT Data API)        │
│    Input: 検索ワード × 3            │
│    Output: 9件の候補動画             │
│    Filter: Creative Commons のみ    │
│    Time: 2-3秒                       │
│    Cost: 無料（API枠内）             │
└─────────────────┬───────────────────┘
                  │
      ┌───────────┴───────────┐
      │  各動画につき以下実行   │
      └───────────┬───────────┘
                  │
┌─────────────────▼───────────────────┐
│ 3. 早期スクリーニング (GPT-4o) ⭐    │
│    Input:                            │
│      - 動画情報                      │
│      - 文字起こし（最初3分）         │
│      - コメント上位20件              │
│    Output:                           │
│      - スコア: 8/10                  │
│      - 判定: continue/skip           │
│    Time: 5-10秒                      │
│    Cost: ~3円                        │
└─────────────────┬───────────────────┘
                  │
            スコア≥5？
              ├─ No → Skip（8円で終了）
              └─ Yes ↓
                  │
┌─────────────────▼───────────────────┐
│ 4. 詳細データ取得                    │
│    - 全文字起こし取得（無料）        │
│    - コメント200件取得（無料）       │
│    Time: 5-10秒                      │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 5. コメントフィルタリング (GPT-3.5)  │
│    Input: 200件                      │
│    Output: 50件                      │
│    基準: いじれるコメントのみ        │
│    Time: 10-15秒                     │
│    Cost: ~5円                        │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 6. 構文抽出 (GPT-4 Turbo)           │
│    Input:                            │
│      - 動画情報                      │
│      - 全文字起こし                  │
│      - フィルタ済みコメント50件      │
│    Output:                           │
│      - 構文タグ                      │
│      - いじりポイント                │
│      - ツッコミ例                    │
│      - 関連シーン + タイムスタンプ   │
│    Time: 30-60秒                     │
│    Cost: ~20円                       │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 7. 品質評価 (GPT-4o) ⭐              │
│    Input: 分析結果                   │
│    Output:                           │
│      - 総合スコア: 7.5/10            │
│      - 個別スコア                    │
│      - 改善ポイント                  │
│      - 次回への指示                  │
│    Time: 10-15秒                     │
│    Cost: ~5円                        │
└─────────────────┬───────────────────┘
                  │
          スコア≥7.0？
            ├─ Yes → 出力
            └─ No ↓
                  │
┌─────────────────▼───────────────────┐
│ 8. 再分析（最大2回まで）             │
│    前回のフィードバックを反映        │
│    Step 6-7 を繰り返し              │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 9. 最終出力                          │
│    - ネタパック（JSON）              │
│    - 品質スコア                      │
│    - 試行回数                        │
│    Time: 即座                        │
└─────────────────────────────────────┘
```

### データサイズ推移

```
ユーザー入力
  ↓ 30文字
検索ワード
  ↓ 3-5個
動画候補
  ↓ 9件
スクリーニング合格
  ↓ 2-3件
コメント
  ↓ 200件 × 平均50文字 = 10,000文字
フィルタリング
  ↓ 50件 × 平均50文字 = 2,500文字
文字起こし
  ↓ 10分動画 = 約3,000文字
分析結果
  ↓ 50件 × 200文字 = 10,000文字
最終出力（JSON）
  ↓ 約15KB
```

---

## API仕様

### YouTube Data API v3

#### 使用エンドポイント

**1. 動画検索**
```
GET https://www.googleapis.com/youtube/v3/search
Parameters:
  - part: "id,snippet"
  - q: 検索ワード
  - type: "video"
  - videoLicense: "creativeCommon"
  - maxResults: 3-5
  - order: "relevance"
  - relevanceLanguage: "ja"
```

**2. コメント取得**
```
GET https://www.googleapis.com/youtube/v3/commentThreads
Parameters:
  - part: "snippet"
  - videoId: 動画ID
  - maxResults: 100
  - order: "relevance"
  - textFormat: "plainText"
```

#### 割当量
- 1日あたり: 10,000ユニット
- 検索: 100ユニット
- コメント取得: 1ユニット

---

### OpenAI API

#### 使用モデル

**GPT-4o（最高峰）**
```python
model="gpt-4o"
使用箇所:
  - 早期スクリーニング
  - 品質評価
料金:
  - Input: $0.0025/1K tokens
  - Output: $0.010/1K tokens
```

**GPT-4 Turbo**
```python
model="gpt-4-turbo-preview"
使用箇所:
  - 検索ワード生成
  - 構文抽出
料金:
  - Input: $0.01/1K tokens
  - Output: $0.03/1K tokens
```

**GPT-3.5 Turbo**
```python
model="gpt-3.5-turbo"
使用箇所:
  - コメントフィルタリング
料金:
  - Input: $0.0005/1K tokens
  - Output: $0.0015/1K tokens
```

---

## 環境変数

### 必須設定

```env
# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key_here

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
```

### オプション設定

```env
# 検索設定
MAX_SEARCH_RESULTS=3              # 各クエリあたりの検索結果数
MAX_COMMENTS_PER_VIDEO=200        # 取得するコメント数
EARLY_SCREENING_COMMENTS=20       # スクリーニング用コメント数
FILTERED_COMMENTS=50              # フィルタリング後のコメント数

# 品質設定
QUALITY_THRESHOLD=7.0             # 品質スコア合格ライン
MAX_RETRY_ATTEMPTS=2              # 最大再試行回数

# 言語設定
DEFAULT_LANGUAGE=ja               # デフォルト言語
```

---

## エラーハンドリング

### エラー分類

| エラー種別 | ハンドリング | リトライ |
|-----------|-------------|---------|
| **YouTube API エラー** | ログ出力 + 次の動画へ | あり（3回） |
| **文字起こし取得失敗** | 動画スキップ | なし |
| **コメント取得失敗** | 動画スキップ | あり（3回） |
| **OpenAI API エラー** | ログ出力 + リトライ | あり（5回） |
| **JSON パースエラー** | フォールバック処理 | あり（2回） |
| **品質評価不合格** | 再分析ループ | 最大2回 |

### エラーログ形式

```python
[HH:MM:SS] [ERROR] モジュール名: エラーメッセージ
例:
[18:30:45] [ERROR] TranscriptFetcher: 字幕が見つかりませんでした: video_id=abc123
```

---

## パフォーマンス最適化

### 処理時間の最適化

| 最適化項目 | Before | After | 改善率 |
|-----------|--------|-------|--------|
| 早期スクリーニング | なし | 導入 | 時間90%削減 |
| 並列処理 | なし | 計画中 | 期待50%短縮 |
| キャッシング | なし | 将来対応 | 期待30%短縮 |

### コストの最適化

| 最適化項目 | Before | After | 削減率 |
|-----------|--------|-------|--------|
| 早期スクリーニング | なし | 導入 | 70%削減 |
| GPT-3.5活用 | なし | 導入 | 15%削減 |
| ハイブリッド戦略 | オールGPT-4 | 実装済み | 50%削減 |

### メモリ使用量

```
最大メモリ使用量: 約200MB
  - 文字起こしデータ: ~50MB
  - コメントデータ: ~20MB
  - AIレスポンス: ~100MB
  - その他: ~30MB
```

---

## セキュリティ

### APIキー管理
- ✅ `.env`ファイルで管理
- ✅ `.gitignore`に追加済み
- ✅ 環境変数から読み込み
- ❌ ハードコード禁止

### データ保護
- コメント・文字起こしはローカルのみ保存
- 外部への送信はOpenAI APIのみ
- 個人情報は収集しない

---

## テスト

### テスト方針
```
各モジュールに`__main__`ブロックでテストコード実装済み
```

### テスト実行例
```bash
# 個別モジュールテスト
python src/search_query_generator.py
python src/early_screener.py

# 統合テスト
python src/orchestrator.py
```

---

## デプロイ

### 現在（MVP版）
- ローカル実行のみ
- Python 3.10+必須

### 将来（SaaS版）
```
Frontend: Vercel
Backend: Vercel Serverless Functions
Database: Supabase
Auth: Supabase Auth
Payment: Stripe
```

---

**Last Updated**: 2024-11-28
**Version**: 1.0.0
