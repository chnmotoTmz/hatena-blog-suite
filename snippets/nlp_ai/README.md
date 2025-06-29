# NLP & AI スニペット (`nlp_ai`)

このカテゴリには、自然言語処理（NLP）技術や、外部のAIサービス（大規模言語モデルAPIなど）を利用して、テキストデータの高度な分析、理解、生成を行うためのスニペットが含まれています。

## 概要

テキストデータからより深い洞察を得たり、コンテンツ作成を支援したりするために、NLPやAIの技術は非常に有効です。
このカテゴリのスニペットは、以下のような機能を提供します：

*   テキストのベクトル化と比較（類似記事検索など）
*   VectorStore（ChromaDBなど）を利用したセマンティック検索基盤の構築
*   外部LLM API（Google Gemini, Cohereなど）との連携による、要約、キーワード抽出、応答生成
*   簡易的な文体分析と、それに基づくコンテンツの個人化（文体調整）
*   記事間の関連性に基づいた知識グラフの構築と分析、可視化

これらの機能は、ブログ記事の推薦、関連情報提示、執筆支援、データ分析など、多岐にわたる応用が可能です。

## 含まれるスニペット

*   **`text_vectorization.py` (Class: `TextVectorizer`)**:
    *   機能: テキストデータをTF-IDFアルゴリズムを用いてベクトル化し、ベクトル間のコサイン類似度を計算します。記事間の類似度比較や、特定のテキストに類似した記事の検索などに利用できます。
    *   主要メソッド: `fit_transform_texts(...)`, `transform_texts(...)`, `calculate_cosine_similarity_matrix(...)`, `get_similarity_for_text(...)`
    *   主要な依存: `scikit-learn`

*   **`vector_store.py` (Class: `ChromaVectorStoreManager`)**:
    *   機能: LangchainライブラリとChromaDBを利用して、テキストドキュメント（記事など）のVectorStoreを管理します。ドキュメントの追加（チャンキング、エンベディング処理を含む）、類似度検索（セマンティック検索）機能を提供します。デフォルトではOpenAIのEmbeddingsを利用します。
    *   主要メソッド: `add_articles(...)`, `load_store()`, `similarity_search(...)`
    *   主要な依存: `langchain`, `openai` (Embeddings用), `chromadb`, `tiktoken`

*   **`llm_integration.py`**:
    *   機能: Google Gemini APIおよびCohere APIと連携するための関数群を提供します。
        *   `summarize_chat_history_google(...)`: Gemini APIでチャット履歴を要約します。
        *   `generate_response_google(...)`: Gemini APIでチャット応答を生成します。
        *   `generate_summary_cohere(...)`: Cohere APIでテキストを要約します。
        *   `extract_keywords_cohere(...)`: Cohere APIでテキストからキーワードを抽出します。
        *   `generate_response_cohere(...)`: Cohere APIでチャット応答を生成します。
    *   主要な依存: `requests`

*   **`style_analyzer.py` (Class: `BasicStyleAnalyzer`)**:
    *   機能: 日本語テキストの基本的な文体特徴（文長、段落構造、文末表現の傾向、文字種比率、句読点利用頻度など）を簡易的に分析します。高度なNLPモデルは使用せず、ルールベースの分析が中心です。
    *   主要メソッド: `analyze_texts(texts: List[str]) -> Dict[str, Any]`
    *   主要な依存: `re`

*   **`content_personalizer.py` (Class: `ContentPersonalizer`)**:
    *   機能: 指定されたスタイルプロファイル（文体、語彙の好みなど）に基づいて、入力テキストの文末表現や語彙を調整し、コンテンツを個人化（特定のスタイルに寄せる）します。`style_analyzer.py` の分析結果をプロファイルとして利用することを想定できます。
    *   主要メソッド: `personalize_text(text: str, ... ) -> str`
    *   主要な依存: `re`

*   **`knowledge_graph.py` (Class: `KnowledgeGraphManager`)**:
    *   機能: NetworkXライブラリを利用して、ノード（記事やエンティティ）とエッジ（関係性）からなる知識グラフを構築、分析、可視化します。ノード間の関連性（例: `text_vectorization.py`による類似度スコア）をエッジの重みとして利用できます。中心性分析やコミュニティ検出などの基本的なグラフ分析機能も提供します。
    *   主要メソッド: `add_node(...)`, `add_edge(...)`, `calculate_basic_stats()`, `calculate_centrality_measures(...)`, `find_communities(...)`, `visualize_graph(...)`, `export_to_json(...)`
    *   主要な依存: `networkx`, `matplotlib`

## 利用例

テキスト類似度検索の例（`TextVectorizer` と `ChromaVectorStoreManager` の組み合わせイメージ）：

```python
# 0. 準備 (環境変数にOPENAI_API_KEYを設定)
# from snippets.utils.env_loader import load_env
# load_env()
# openai_key = os.getenv("OPENAI_API_KEY")

# 1. VectorStoreManagerの初期化 (実際にはAPIキーが必要)
# manager = ChromaVectorStoreManager(openai_api_key=openai_key, persist_directory="./my_chroma_db")

# 2. 記事データの準備 (contentとmetadataを持つ辞書のリスト)
# articles_to_add = [
#    {"id": "art001", "content": "Pythonはデータ分析に強いです。", "metadata": {"category": "Python"}},
#    {"id": "art002", "content": "機械学習の基礎とPythonでの実装。", "metadata": {"category": "ML"}},
# ]
# manager.add_articles(articles_to_add) # これでVectorStoreに記事が登録される

# 3. 類似記事の検索
# query = "Pythonを使ったデータ処理"
# results = manager.similarity_search(query, k=1)
# if results:
#    doc, score = results[0]
#    print(f"最も類似した記事 (スコア: {score:.4f}): {doc.metadata.get('id')}")
#    print(f"内容抜粋: {doc.page_content[:50]}...")
```

LLM APIを利用したキーワード抽出の例：

```python
# from snippets.utils.env_loader import load_env
# from snippets.nlp_ai.llm_integration import extract_keywords_cohere
# load_env()
# cohere_api_key = os.getenv("COHERE_API_KEY")

# if cohere_api_key:
#    text = "この文章は、AIと自然言語処理の未来について考察しています。特にトランスフォーマーモデルの進化が鍵となります。"
#    keywords = extract_keywords_cohere(text, api_key=cohere_api_key, num_keywords=3)
#    print(f"Cohereによる抽出キーワード: {keywords}")
# else:
#    print("COHERE_API_KEYが設定されていません。")
```

## 注意点

*   **APIキー管理**: 外部AIサービスを利用するスニペットは、それぞれのサービスプロバイダが発行するAPIキーが必要です。これらのキーは機密情報として、環境変数などを利用して安全に管理してください。
*   **コスト**: 外部AI APIの利用には、リクエスト数や処理量に応じたコストが発生する場合があります。各サービスの料金体系を確認し、予算内で利用するよう注意してください。
*   **ライブラリ依存**: `scikit-learn`, `langchain`, `openai`, `chromadb`, `tiktoken`, `networkx`, `matplotlib` など、多くの外部ライブラリに依存しています。これらは事前にインストールが必要です。
*   **計算資源**: 特にVectorStoreの構築や知識グラフの大規模な分析は、相応の計算資源（メモリ、CPU時間）を必要とする場合があります。
*   **日本語処理の特性**: 日本語の自然言語処理は、わかち書き（単語分割）が重要となる場合があります。`TextVectorizer` や `BasicStyleAnalyzer` は基本的な処理を行いますが、より高度な日本語処理のためには、MeCab, SudachiPy, GiNZAなどの形態素解析器との連携を検討する必要があるかもしれません（`content_processing.keyword_extractor`ではMeCabの利用を試みます）。
*   **倫理的配慮**: AIによって生成されたコンテンツや分析結果を利用する際は、倫理的な側面（バイアス、誤情報、著作権など）に十分配慮してください。
