# 🎯 YouTube Comment Analyzer

**YouTuberが喋るだけで動画として成立する「ネタパック」を自動生成**

AIが動画検索から分析、品質評価まで全自動で実行。タイムスタンプ付きのツッコミ構文を生成します。

---

## ✨ 特徴

### 🚀 完全自動化
1. **検索ワード自動生成** - ユーザーの1文から最適な検索ワードを生成
2. **動画自動選定** - Creative Commons動画から「ネタになる」動画を選別
3. **早期スクリーニング** - GPT-4oで事前判定し、無駄なコストを70%削減
4. **シーン自動マッチング** - コメントと動画シーンを自動で紐付け
5. **品質自動評価** - GPT-4oがプロディレクター目線で厳しくチェック
6. **自己改善ループ** - 品質基準未達なら自動で再分析（最大2回）

### 💎 高品質保証
- ✅ お笑い芸人のツッコミ脳で構文抽出
- ✅ YouTuberが実際に使えるクオリティ
- ✅ 炎上回避トーン調整
- ✅ タイムスタンプ + シーン説明の両方提供

### 💰 コスト最適化
- GPT-4o（最高性能）+ GPT-4 Turbo + GPT-3.5のハイブリッド戦略
- 早期スクリーニングで無駄な動画を排除
- **1動画あたり約25-60円**で高品質分析

---

## 📦 セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. APIキーの設定

#### YouTube Data API v3 キーの取得:
1. https://console.cloud.google.com/ にアクセス
2. 新規プロジェクト作成
3. 「YouTube Data API v3」を有効化
4. 認証情報 > APIキーを作成

#### OpenAI APIキーの取得:
1. https://platform.openai.com/api-keys にアクセス
2. 「Create new secret key」をクリック
3. キーをコピー

#### `.env`ファイル作成:
```bash
cp .env.example .env
```

`.env`を編集してAPIキーを設定:
```env
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 🚀 使い方

### Streamlit UI版（推奨）

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

#### 使い方:
1. テキストボックスに探したいネタを入力
   - 例: "炎上している女性ドライバーの事故動画"
2. 「分析開始」をクリック
3. 数分待つと結果が表示されます

### CLI版

```bash
python cli.py "炎上している女性ドライバーの事故動画"
```

#### オプション:
```bash
python cli.py "検索ワード" \
  --max-videos 3 \
  --max-comments 200 \
  --quality-threshold 7.0 \
  --max-retry 2 \
  --output outputs \
  --quiet
```

---

## 📊 出力形式

```json
{
  "video_info": {
    "title": "動画タイトル",
    "url": "https://youtube.com/watch?v=xxxxx",
    "channel_title": "チャンネル名"
  },
  "screening_result": {
    "score": 8,
    "reason": "差別的コメント×事故シーンのツッコミネタとして成立"
  },
  "analysis": [
    {
      "元コメント": "だから女は運転するなって言ってんだよ",
      "構文タグ": "差別",
      "いじりポイント": "性別で十把一絡げにしてる時点で無理筋すぎる",
      "ツッコミ例": "まずお前が免許返納してから言え",
      "関連シーン": {
        "タイムスタンプ": "0:32",
        "シーン説明": "女性が左折しようとして曲がり損ねたシーン",
        "関連度": 8
      }
    }
  ],
  "evaluation": {
    "total_score": 7.5,
    "individual_scores": {
      "シーンマッチング": 8,
      "ネタ成立度": 7,
      "実用性": 8,
      "構文の質": 7
    }
  },
  "attempts": 1
}
```

---

## 🏗️ プロジェクト構成

```
youtube-comment/
├── .env                          # APIキー（Gitignore）
├── .env.example                  # 設定サンプル
├── requirements.txt              # 依存パッケージ
├── README.md
├── config/
│   └── prompt_template.py        # プロンプトテンプレート
├── src/
│   ├── search_query_generator.py # 検索ワード生成
│   ├── youtube_search.py         # 動画検索
│   ├── transcript_fetcher.py     # 文字起こし取得
│   ├── comment_fetcher.py        # コメント取得
│   ├── early_screener.py         # 早期スクリーニング
│   ├── comment_filter.py         # コメントフィルタリング
│   ├── comment_analyzer.py       # 構文抽出
│   ├── quality_evaluator.py      # 品質評価
│   ├── orchestrator.py           # 全体統括
│   └── utils.py                  # ユーティリティ
├── app.py                        # Streamlit UI
├── cli.py                        # CLIエントリーポイント
└── outputs/                      # 分析結果保存先
```

---

## 🔄 処理フロー

```
[入力] ユーザーが1文を入力
  ↓
[AI] 検索ワード生成 (GPT-4 Turbo)
  ↓
[YouTube] 動画検索（Creative Commons動画のみ）
  ↓
[AI] 早期スクリーニング (GPT-4o) ⭐
  - 冒頭3分の文字起こし
  - 上位20コメント
  - ネタ化可能性を10秒で判定
  ↓
合格動画のみ詳細分析へ
  ↓
[1] 全文字起こし取得
[2] コメント200件取得
[3] GPT-3.5でフィルタリング (200件→50件)
[4] GPT-4で構文抽出 + シーンマッチング
[5] GPT-4oで品質評価 ⭐
  ↓
品質スコア < 7.0？
  └─ 改善指示を反映して再分析（最大2回）
  ↓
[出力] ネタパック生成
```

---

## 💰 コスト目安

### API使用料金
- **YouTube Data API**: 1日10,000ユニット無料（約10,000回検索可能）
- **OpenAI API**:
  - GPT-4o: 入力 $0.0025/1K tokens, 出力 $0.010/1K tokens
  - GPT-4 Turbo: 入力 $0.01/1K tokens, 出力 $0.03/1K tokens
  - GPT-3.5 Turbo: 入力 $0.0005/1K tokens, 出力 $0.0015/1K tokens

### 1動画あたりのコスト
- **初回合格の場合**: 約25-30円
- **1回再試行**: 約50-60円
- **スクリーニングでスキップ**: 約8円（無駄コスト削減）

### 月間運用例
```
1日10動画分析 × 30日 = 300動画/月
コスト: 300動画 × 40円 = 12,000円/月
```

---

## 🎯 想定ユースケース

### 1. YouTuberのネタ探し
- コメント紹介動画の台本作成
- 炎上コメントへのツッコミ動画
- 反応系コンテンツの素材収集

### 2. 動画制作の効率化
- 1動画30分かかるネタ探しが2分に短縮
- タイムスタンプ付きで編集が楽
- 品質保証されたネタのみ提供

### 3. コンテンツアイデア発掘
- トレンド把握
- 視聴者の反応分析
- 新しい切り口の発見

---

## 🛠️ カスタマイズ

### プロンプトの調整
`config/prompt_template.py` でプロンプトをカスタマイズ可能

### パラメータ調整
`.env`ファイルで以下を設定:
```env
MAX_SEARCH_RESULTS=3          # 検索動画数
MAX_COMMENTS_PER_VIDEO=200    # 取得コメント数
QUALITY_THRESHOLD=7.0         # 品質スコア閾値
MAX_RETRY_ATTEMPTS=2          # 最大再試行回数
```

---

## ⚠️ 注意事項

### 法的事項
- このツールは検索・分析のみを行います
- 実際にコメントや動画を使用する場合は、著作権・肖像権を確認してください
- Creative Commons動画のみを対象としていますが、使用時は利用規約を確認してください

### 倫理的配慮
- 差別的コメントは「批判」の文脈でツッコミを生成します
- 炎上回避のトーン調整を行っていますが、最終判断は人間が行ってください
- 個人を特定できる情報は使用しないでください

---

## 📝 ライセンス

MIT License

---

## 🤝 貢献

Issue、Pull Requestは歓迎します！

---

## 📧 お問い合わせ

バグ報告や機能要望は GitHub Issues へ

---

## 🎉 謝辞

このツールは以下の技術を使用しています:
- OpenAI GPT-4o / GPT-4 Turbo / GPT-3.5
- YouTube Data API v3
- youtube-transcript-api
- Streamlit

---

**Made with ❤️ for YouTubers**
