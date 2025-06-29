# Content Enhancement スニペット (`content_enhancement`)

このカテゴリには、既存のブログ記事コンテンツをより魅力的で効果的なものにするための機能を提供するスニペットが含まれています。
アフィリエイトリンクの管理・最適化や、AIを利用した画像生成などが主な機能です。

## 概要

良質なコンテンツはブログの価値を高めます。これらのスニペットは、コンテンツの収益性向上（アフィリエイト）、視覚的な魅力向上（画像生成）、読者のエンゲージメント向上などを支援します。
`content_processing` スニペットで抽出・整形されたデータを入力として利用することが多いです。

## 含まれるスニペット

*   **`affiliate.py` (Class: `AffiliateLinkManager`)**:
    *   機能: アフィリエイトリンクの管理と処理を行います。
        *   設定に基づいてURLが特定のアフィリエイトサービス（例: 楽天、Amazon）のものかを判定します。
        *   URLにアフィリエイトトラッキングIDを自動的に付与・更新します。
        *   HTMLコンテンツ全体をスキャンし、含まれるアフィリエイト対象URLにトラッキングIDを付与します。
        *   商品名、商品URL、価格、画像URLなどから、整形された商品紹介HTMLブロック（アフィリエイトリンク付き）を生成します。
    *   主要メソッド:
        *   `set_tracking_id(service_name: str, tracking_id: str)`
        *   `get_affiliate_service_for_url(url: str) -> Optional[str]`
        *   `add_tracking_to_url(url: str, ... ) -> str`
        *   `process_html_content(html_content: str) -> Tuple[str, List[Dict[str, str]]]`
        *   `generate_product_link_html(...) -> str`
    *   主要な依存: `re`, `urllib.parse`

*   **`image_generation.py` (Class: `ImageGenerator`)**:
    *   機能: 主にBing Image Creator（`bingart`ライブラリ経由）を利用して、テキストプロンプトから画像を生成します。また、画像のダウンロード、保存、Web向けの最適化（リサイズ、フォーマット変換）といったユーティリティも提供します。
    *   主要メソッド:
        *   `generate_images_with_bing(prompt: str, ...) -> List[str]`
        *   `download_image(image_url: str) -> Optional[BytesIO]`
        *   `save_image(image_data: BytesIO, ...) -> Optional[str]`
        *   `generate_and_save_bing_image(prompt: str, ...) -> Optional[str]`
        *   `create_featured_image_for_article(article_title: str, ... ) -> Optional[str]`
        *   `optimize_image_for_web(image_path: str, ... ) -> Optional[str]`
        *   `close_bing_session()`
    *   主要な依存: `bingart` (オプション、Bing利用時), `requests`, `Pillow (PIL)`

## 利用例

アフィリエイトリンクの処理例：

```python
from snippets.content_enhancement.affiliate import AffiliateLinkManager

# マネージャーを初期化（デフォルト設定を使用）
manager = AffiliateLinkManager()
manager.set_tracking_id('rakuten', 'YOUR_RAKUTEN_ID-001')
manager.set_tracking_id('amazon', 'YOUR_AMAZON_TAG-22')

html_before = '<p>楽天で見つけた面白い商品: <a href="http://hb.afl.rakuten.co.jp/hgc/someproduct">コレ</a></p>'
html_after, processed_links = manager.process_html_content(html_before)

print("処理前HTML:", html_before)
print("処理後HTML:", html_after)
for link_info in processed_links:
    print(f"処理されたリンク: {link_info['original_url']} -> {link_info['modified_url']}")

# 商品リンクHTML生成
product_html = manager.generate_product_link_html(
    product_name="すごいガジェット",
    product_url="https://www.amazon.co.jp/dp/EXAMPLEID",
    service_name="amazon",
    image_url="https://example.com/image.jpg",
    price="¥12,000"
)
print("\\n商品リンクHTML:\\n", product_html)
```

AIによる画像生成の例：

```python
import os
from snippets.utils.env_loader import load_env
from snippets.content_enhancement.image_generation import ImageGenerator

load_env() # BING_AUTH_COOKIE_U を .env から読み込む想定

bing_cookie = os.getenv("BING_AUTH_COOKIE_U")

if not bing_cookie:
    print("環境変数 BING_AUTH_COOKIE_U が設定されていません。Bing画像生成はスキップされます。")
else:
    img_gen = ImageGenerator(bing_auth_cookie_U=bing_cookie, output_dir="./generated_images_example")

    prompt = "A futuristic cityscape at sunset, digital painting"
    image_path = img_gen.generate_and_save_bing_image(prompt, filename_prefix="cityscape")

    if image_path:
        print(f"画像が生成・保存されました: {image_path}")
        optimized_path = img_gen.optimize_image_for_web(image_path, max_width=800, output_format="WEBP")
        if optimized_path:
            print(f"最適化された画像: {optimized_path}")
    else:
        print(f"画像の生成に失敗しました。プロンプト: {prompt}")

    img_gen.close_bing_session() # セッションを閉じる
```

## 注意点

*   **アフィリエイト**:
    *   各アフィリエイトサービス（楽天、Amazonなど）の利用規約、リンク改変に関するポリシーを遵守してください。
    *   トラッキングIDは正確に設定してください。
*   **画像生成**:
    *   `image_generation.py` でBing Image Creatorを利用するには、`bingart`ライブラリのインストールと、有効なBingの`_U`認証クッキーが必要です。認証クッキーは環境変数 (`BING_AUTH_COOKIE_U`) から読み込むことを推奨します。
    *   AIによる画像生成は、プロンプトの内容やサービスの状況によって結果が大きく変わることがあります。また、生成された画像の使用権利についても各サービスの規約を確認してください。
    *   生成処理には時間がかかる場合があります。
*   生成されたコンテンツ（HTML、画像パスなど）を実際にブログ記事に組み込む処理は、これらのスニペットの範囲外です。`hatena_api.client` などを利用して別途実装する必要があります。
