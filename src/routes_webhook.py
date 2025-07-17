"""
LINE Webhook ルート - バッチ処理強化版
従来版をベースにバッチ処理とフォトライフ統合を追加
"""

from flask import Blueprint, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, VideoMessage
from src.services.line_service import LineService
from src.services.gemini_service import GeminiService
from src.services.hatena_service import HatenaService
from src.database import db, Message, Article
from src.config import Config
import os
import json
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict

import logging
from typing import List, Dict, Any

# ログファイル出力設定（logs/app.log, INFO以上, ローテーションなし）
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# バッチ処理用のグローバル変数
user_message_buffer = defaultdict(list)  # user_id -> [messages]
user_batch_timers = {}  # user_id -> timer_thread
BATCH_INTERVAL = int(os.getenv('BATCH_INTERVAL_MINUTES', '2')) * 60  # デフォルト2分

webhook_bp = Blueprint('webhook', __name__)

# LINE Bot API の初期化
line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)

# サービスの初期化
line_service = LineService()
gemini_service = GeminiService()
hatena_service = HatenaService()

# 検索サービスの初期化（Web検索機能）
try:
    from src.services.search_service import SearchService
    search_service = SearchService()
    logger.info(f"検索サービス初期化: {'有効' if search_service.enabled else '無効'}")
except ImportError:
    search_service = None
    logger.warning("検索サービスが利用できません")


@webhook_bp.route('/line', methods=['POST'])
def line_webhook():
    """LINE Webhook エンドポイント"""
    # デバッグ情報をログに出力
    logger.info(f"Received webhook request. Headers: {dict(request.headers)}")

    # 署名検証
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    logger.info(f"Signature: {signature}")
    logger.info(f"Body length: {len(body) if body else 'None'}")
    logger.info(f"Body content: {body[:200] if body else 'None'}")

    # 署名が存在しない場合の処理
    if not signature:
        logger.error('X-Line-Signature header is missing')
        return jsonify({'error': 'X-Line-Signature header is missing'}), 400

    # リクエストボディが空の場合の処理
    if not body:
        logger.error('Request body is empty')
        return jsonify({'error': 'Request body is empty'}), 400

    try:
        # 一時的に署名検証をスキップ（デバッグ用）
        logger.warning("DEBUGGING: Skipping signature validation")

        # 手動でイベントを処理
        import json
        webhook_body = json.loads(body)



        # eventsが存在し、空でない場合のみ処理
        if 'events' in webhook_body and webhook_body['events']:
            for event_data in webhook_body['events']:
                logger.info(f"Processing event: {event_data}")
                # ここで手動でイベントを処理
                if event_data.get('type') == 'message':
                    process_message_event_with_batch(event_data)
        else:
            logger.info("No events to process (webhook verification or empty events)")

        logger.info('Webhook handled successfully')
    except Exception as e:
        logger.error(f'Webhook handling error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

    return 'OK'

def process_message_event_with_batch(event_data):
    """メッセージイベントをバッチ処理対応で処理"""
    try:
        message_info = event_data.get('message', {})
        message_type = message_info.get('type')
        user_id = event_data.get('source', {}).get('userId')
        line_message_id = message_info.get('id')
        
        if not user_id or not line_message_id:
            logger.warning("Missing user_id or message_id")
            return
        
        logger.info(f"Processing {message_type} message from {user_id} (batch mode)")
        
        # メッセージをデータベースに保存
        message_data = {
            'line_message_id': line_message_id,
            'user_id': user_id,
            'message_type': message_type,
            'timestamp': datetime.now(),
            'processed': False
        }
        
        if message_type == 'text':
            text = message_info.get('text', '')
            message_data['content'] = text
            
            # データベースに保存
            message = Message(
                line_message_id=line_message_id,
                user_id=user_id,
                message_type='text',
                content=text
            )
            db.session.add(message)
            db.session.commit()
            
        elif message_type == 'image':
            # 画像コンテンツを取得・保存
            message_content = line_bot_api.get_message_content(line_message_id)
            
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            image_path = f"{upload_dir}/{line_message_id}.jpg"
            
            with open(image_path, 'wb') as f:
                for chunk in message_content.iter_content():
                    f.write(chunk)
            
            logger.info(f"画像保存完了: {image_path}")
            
            # 【1回目Gemini】画像をGeminiで即座に解析してテキスト化
            try:
                logger.info(f"Gemini画像解析開始: {image_path}")
                image_analysis = gemini_service.analyze_image(
                    image_path, 
                    "この画像について詳しく説明してください。写っているもの、場所、状況、色彩、雰囲気などを具体的に記述してください。"
                )
                
                if image_analysis and image_analysis.strip():
                    analyzed_text = f"【画像解析結果】{image_analysis.strip()}"
                    logger.info(f"Gemini画像解析成功: {len(analyzed_text)}文字")
                else:
                    analyzed_text = "【画像】画像が投稿されました（解析失敗）"
                    logger.warning("Gemini画像解析が空の結果を返しました")
                    
            except Exception as e:
                logger.error(f"Gemini画像解析エラー: {e}")
                analyzed_text = "【画像】画像が投稿されました（解析エラー）"
            
            # 改良版自作MCPでImgurにアップロード（OAuth対応）
            imgur_url = None
            try:
                import asyncio
                import sys
                sys.path.append('/home/moto/line-gemini-hatena-integration')
                from src.mcp_servers.imgur_server_fastmcp import upload_image
                
                # OAuth認証で個人アカウントにアップロード
                upload_result = asyncio.run(upload_image(
                    image_path=image_path,
                    title=f"LINE_Image_{line_message_id}",
                    description="LINE Bot経由画像（個人アカウント）",
                    privacy="hidden"  # 個人アカウントの非公開画像
                ))
                
                if upload_result.get('success'):
                    imgur_url = upload_result.get('url')
                    logger.info(f"Imgur アップロード成功: {imgur_url}")
                    if os.getenv('IMGUR_ACCESS_TOKEN'):
                        logger.info(f"✅ 個人アカウントに紐付け完了: {upload_result.get('imgur_id')}")
                    else:
                        logger.warning("⚠️  匿名アップロード（IMGUR_ACCESS_TOKEN未設定）")
                else:
                    logger.error(f"Imgur アップロード失敗: {upload_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Imgur アップロードエラー: {e}")
            
            # データベースに保存（解析結果をcontentに、Imgur URLも保存）
            message_data['content'] = analyzed_text
            message_data['file_path'] = image_path
            message_data['imgur_url'] = imgur_url
            
            message = Message(
                line_message_id=line_message_id,
                user_id=user_id,
                message_type='image',
                content=analyzed_text,  # 解析結果をテキストとして保存
                file_path=image_path
            )
            # Imgur URLを追加フィールドに保存（必要に応じてDBスキーマ拡張）
            if hasattr(message, 'imgur_url'):
                message.imgur_url = imgur_url
                
            db.session.add(message)
            db.session.commit()
            
        elif message_type == 'video':
            # 動画コンテンツを取得・保存
            message_content = line_bot_api.get_message_content(line_message_id)
            
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            video_path = f"{upload_dir}/{line_message_id}.mp4"
            
            with open(video_path, 'wb') as f:
                for chunk in message_content.iter_content():
                    f.write(chunk)
            
            message_data['content'] = f"Video: {video_path}"
            message_data['file_path'] = video_path
            
            # データベースに保存
            message = Message(
                line_message_id=line_message_id,
                user_id=user_id,
                message_type='video',
                content=f"Video: {video_path}",
                file_path=video_path
            )
            db.session.add(message)
            db.session.commit()
        
        else:
            logger.info(f"Unsupported message type: {message_type}")
            return
        
        # バッチに追加
        add_message_to_batch(user_id, message_data)
        
    except Exception as e:
        logger.error(f"Error processing message event with batch: {str(e)}")
        import traceback
        traceback.print_exc()

def add_message_to_batch(user_id: str, message_data: Dict[str, Any]):
    """メッセージをバッチに追加し、タイマーを設定"""
    global user_message_buffer, user_batch_timers
    
    # メッセージをバッファに追加
    user_message_buffer[user_id].append(message_data)
    logger.info(f"Added message to batch for user {user_id}. Total: {len(user_message_buffer[user_id])}")
    
    # 既存のタイマーをキャンセル
    if user_id in user_batch_timers:
        user_batch_timers[user_id].cancel()
    
    # 新しいタイマーを設定
    timer = threading.Timer(BATCH_INTERVAL, process_user_batch, [user_id])
    timer.start()
    user_batch_timers[user_id] = timer
    
    logger.info(f"Set batch timer for user {user_id} ({BATCH_INTERVAL} seconds)")

def process_user_batch(user_id: str):
    """ユーザーのバッチを処理（Flask アプリケーションコンテキスト対応）"""
    global user_message_buffer, user_batch_timers
    
    try:
        # Flask アプリケーションコンテキストを作成
        from flask import current_app
        from main import create_app
        
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            app = create_app()
        
        with app.app_context():
            if user_id not in user_message_buffer or not user_message_buffer[user_id]:
                logger.info(f"No messages in batch for user {user_id}")
                return
            
            messages = user_message_buffer[user_id].copy()
            
            # バッファをクリア
            user_message_buffer[user_id] = []
            if user_id in user_batch_timers:
                del user_batch_timers[user_id]
            
            logger.info(f"Processing batch for user {user_id} with {len(messages)} messages")
            
            # メッセージを種類別に分類
            text_messages = [msg for msg in messages if msg['message_type'] == 'text']
            image_messages = [msg for msg in messages if msg['message_type'] == 'image']
            video_messages = [msg for msg in messages if msg['message_type'] == 'video']
            
            # 統合コンテンツを作成（修正版）
            title, integrated_content = create_integrated_content_fixed(text_messages, image_messages, video_messages)
            
            if integrated_content and title:
                # 【画像URL挿入】投稿直前にImgur URLをルールベースで挿入
                final_content = insert_imgur_urls_to_content(integrated_content, image_messages)
                
                # はてなブログに投稿
                article_url = hatena_service.post_article(
                    title=title,
                    content=final_content  # 画像URL挿入済みコンテンツ
                )
                
                if article_url:
                    # ユーザーに通知
                    content_summary = f"テキスト{len(text_messages)}件、画像{len(image_messages)}件、動画{len(video_messages)}件"
                    line_service.send_message(
                        user_id,
                        f"📝 統合記事を投稿しました！\\n\\n💫 {content_summary}を組み合わせました\\n🔗 {article_url}"
                    )
                    
                    # 記事情報をデータベースに保存
                    article = Article(
                        title=title,
                        content=final_content,
                        hatena_url=article_url,
                        published=True,
                        status='published'
                    )
                    
                    # ソースメッセージIDを記録
                    source_message_ids = [msg['line_message_id'] for msg in messages]
                    article.set_source_messages_list(source_message_ids)
                    
                    # 画像パスを記録
                    image_paths = [msg.get('file_path') for msg in image_messages if msg.get('file_path')]
                    if image_paths:
                        article.set_image_paths_list(image_paths)
                    
                    # 動画パス（最初のもののみ）
                    video_paths = [msg.get('file_path') for msg in video_messages if msg.get('file_path')]
                    if video_paths:
                        article.video_path = video_paths[0]
                    
                    db.session.add(article)
                    db.session.commit()
                    
                    # メッセージを処理済みにマーク
                    for msg in messages:
                        db_message = Message.query.filter_by(line_message_id=msg['line_message_id']).first()
                        if db_message:
                            db_message.processed = True
                    db.session.commit()
                    
                    logger.info(f"Batch processing completed for user {user_id}. Article ID: {article.id}")
                else:
                    line_service.send_message(
                        user_id,
                        "❌ 統合記事の投稿に失敗しました。"
                    )
            else:
                line_service.send_message(
                    user_id,
                    "❌ コンテンツの生成に失敗しました。"
                )
                
    except Exception as e:
        logger.error(f"Error processing batch for user {user_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        try:
            line_service.send_message(
                user_id,
                f"❌ バッチ処理中にエラーが発生しました: {str(e)}"
            )
        except:
            pass

def create_integrated_content_fixed(text_messages: List[Dict], image_messages: List[Dict], video_messages: List[Dict]) -> tuple:
    """統合コンテンツを作成（タイトルと本文を分けて返す）"""

    try:
        # すべてのテキスト情報を統合
        all_texts = []
        if text_messages:
            for msg in text_messages:
                all_texts.append(f"【メッセージ】{msg['content']}")
        if image_messages:
            for msg in image_messages:
                if msg.get('content'):
                    all_texts.append(f"【画像説明】{msg['content']}")
        if video_messages:
            for msg in video_messages:
                if msg.get('content'):
                    all_texts.append(f"【動画説明】{msg['content']}")

        combined_all_text = '\n'.join(all_texts)

        # メインプロンプトを外部ファイルから読み込む
    
        blog_prompt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'blog_main_prompt.txt'))
        if not os.path.exists(blog_prompt_path):
            logger.error(f"メインプロンプトファイルが見つかりません: {blog_prompt_path}")
            blog_prompt_template = ""  # 空文字でフォールバック
        else:
            try:
                with open(blog_prompt_path, 'r', encoding='utf-8') as f:
                    blog_prompt_template = f.read()
            except Exception as e:
                logger.error(f"メインプロンプトファイルの読み込みエラー: {e}")
                blog_prompt_template = ""  # 空文字でフォールバック

        # プロンプトに入力情報を埋め込む
        blog_prompt = blog_prompt_template.replace('{combined_all_text}', combined_all_text)

        # --- Web検索の自動判定・引用元リンク付与 ---
        # 1. メインテーマから検索クエリを抽出
        search_queries = extract_search_queries_from_content(combined_all_text)
        logger.info(f"Web検索自動判定: {search_queries}")

        # 2. AIにWeb検索の必要性を判定させる
        should_search = False
        if search_service and search_queries:
            try:
                search_judge_prompt_template = (
                    "以下はブログ記事の下書き情報です。\n"
                    "この内容を読者にとって十分有益な記事にするには、Web検索による追加情報（例：公式情報、最新データ、第三者の評価など）が必要ですか？\n"
                    "\n【記事下書き】\n"
                    "{combined_all_text}\n"
                    "---\n"
                    "必要な場合はYes、不要ならNoとだけ1行で答えてください。"
                )
                search_judge_prompt = search_judge_prompt_template.replace('{combined_all_text}', combined_all_text)
                judge_result = gemini_service.generate_content(search_judge_prompt)
                logger.info(f"Web検索要否AI判定: {judge_result}")
                if judge_result and judge_result.strip().lower().startswith('y'):
                    should_search = True
            except Exception as e:
                logger.error(f"Web検索要否判定エラー: {e}")

        basic_content = gemini_service.generate_content(blog_prompt)
        enhanced_content = basic_content
        source_links = []
        if should_search:
            try:
                # メソッド名を確認し、なければ仮でsearch_and_enhance_contentに変更
                if hasattr(search_service, 'enhance_content_with_search_and_links'):
                    enhanced_content, links = search_service.enhance_content_with_search_and_links(
                        basic_content, search_queries
                    )
                elif hasattr(search_service, 'search_and_enhance_content'):
                    enhanced_content, links = search_service.search_and_enhance_content(
                        basic_content, search_queries
                    )
                elif hasattr(search_service, 'enhance_content'):
                    enhanced_content, links = search_service.enhance_content(
                        basic_content, search_queries
                    )
                else:
                    logger.error("SearchServiceにWeb検索強化用のメソッドが見つかりません")
                    enhanced_content, links = basic_content, []
                logger.info(f"Web検索強化・引用元取得: {links}")
                source_links = links
            except Exception as e:
                logger.error(f"Web検索エラー: {e}")

        # 3. 記事末尾に引用元リンクを必ず追加
        if source_links:
            links_section = '\n\n---\n\n参考・引用元:\n' + '\n'.join(f'- {url}' for url in source_links)
            enhanced_content = f"{enhanced_content}{links_section}"

        integrated_content = enhanced_content

        # タイトル抽出: 本文中の一番印象的な見出し（Markdown見出し or 太字 or タイトル:）を優先
        import re
        title = None
        content = integrated_content

        # 1. <p>タイトル: ...</p> 形式や タイトル: ... で始まる場合
        m = re.match(r'<p>\s*タイトル[:：]\s*(.+?)</p>', integrated_content)
        if m:
            title = m.group(1).strip()
            content = re.sub(r'<p>\s*タイトル[:：].+?</p>\s*', '', integrated_content, count=1).lstrip('\n').strip()
        else:
            m2 = re.match(r'タイトル[:：]\s*(.+)', integrated_content)
            if m2:
                title = m2.group(1).strip()
                content = re.sub(r'タイトル[:：].+\n?', '', integrated_content, count=1).lstrip('\n').strip()
            else:
                # 2. Markdown見出し（##, ###, #）を探す
                headings = re.findall(r'^(#+)\s*(.+)', integrated_content, re.MULTILINE)
                if headings:
                    title = headings[0][1].strip()
                    content = integrated_content.replace(headings[0][0] + ' ' + title, '', 1).lstrip('\n').strip()
                else:
                    # 3. 太字（**タイトル**）を探す
                    bolds = re.findall(r'\*\*(.+?)\*\*', integrated_content)
                    if bolds:
                        title = bolds[0].strip()
                        content = integrated_content.replace('**' + title + '**', '', 1).lstrip('\n').strip()
                    else:
                        # 4. フォールバック: 先頭行
                        first_line = integrated_content.split('\n', 1)[0].strip()
                        title = re.sub(r'[\s\u200b\u3000\uFFFD]+', '', first_line)
                        content = integrated_content[len(first_line):].lstrip('\n').strip()

        # 変な文字（ゼロ幅スペース、全角空白、制御文字など）を除去
        title = re.sub(r'[\u200b\u3000\uFFFD]+', '', title)
        content = re.sub(r'[\u200b\u3000\uFFFD]+', '', content)

        logger.info(f"抽出されたタイトル: {title}")
        # --- ここから画像のHTMLタグを末尾に追加 ---
        if image_messages:
            image_html_tags = []
            def is_valid_imgur_url(url):
                import re
                if not url:
                    return False
                if not url.startswith('https://'):
                    return False
                if 'imgur.com' not in url:
                    return False
                if not re.search(r'\.(jpg|jpeg|png|gif)$', url, re.IGNORECASE):
                    return False
                return True

            for i, img_msg in enumerate(image_messages, 1):
                imgur_url = img_msg.get('imgur_url')
                if is_valid_imgur_url(imgur_url):
                    html_tag = f'<p><img src="{imgur_url}" alt="画像{i}" style="max-width: 80%; height: auto; display: block; margin: 20px auto; border: 1px solid #ddd; border-radius: 8px;"></p>'
                    image_html_tags.append(html_tag)
                else:
                    logger.warning(f"画像URLが無効または非推奨: {imgur_url}")
            if image_html_tags:
                content += "\n\n" + "\n".join(image_html_tags)
        # --- ここまで画像末尾追加 ---
        logger.info(f"抽出されたタイトル: {title}")
        return title, content

    except Exception as e:
        logger.error(f"統合コンテンツ作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def insert_imgur_urls_to_content(content: str, image_messages: List[Dict]) -> str:
    '''ブログ記事にImgur URLをルールベースで挿入'''
    import re
    try:
        if not image_messages:
            return content

        logger.info(f"画像URL挿入開始: {len(image_messages)}枚の画像")

        # 画像URLを収集し、本文末尾にまとめて埋め込む
        # 画像説明文の直後に画像タグを挿入。なければ末尾にまとめて追加。
        import re
        new_content = content
        used_urls = set()
        image_html_tags = []
        # 画像説明文とURLのペアを作成
        imgur_pairs = []
        unmatched_urls = []
        for img_msg in image_messages:
            imgur_url = img_msg.get('imgur_url')
            desc = img_msg.get('content')
            if imgur_url:
                if desc and desc.strip():
                    imgur_pairs.append((desc.strip(), imgur_url))
                else:
                    unmatched_urls.append(imgur_url)
                logger.info(f"挿入予定URL: {imgur_url}")

        # 本文中の画像説明文の直後に画像タグを挿入（最初の一致のみ）
        for i, (desc, url) in enumerate(imgur_pairs, 1):
            html_tag = f'<p><img src="{url}" alt="画像{i}" style="max-width: 80%; height: auto; display: block; margin: 20px auto; border: 1px solid #ddd; border-radius: 8px;"></p>'
            pattern = re.escape(desc)
            if url in used_urls:
                continue
            new_content, count = re.subn(pattern, desc + '\n' + html_tag, new_content, count=1)
            if count > 0:
                used_urls.add(url)

        # 説明文に紐づかない画像は末尾にまとめて挿入
        if unmatched_urls:
            for i, url in enumerate(unmatched_urls, 1):
                html_tag = f'<p><img src="{url}" alt="画像(末尾){i}" style="max-width: 80%; height: auto; display: block; margin: 20px auto; border: 1px solid #ddd; border-radius: 8px;"></p>'
                image_html_tags.append(html_tag)
            new_content += "\n\n" + "\n".join(image_html_tags)

        logger.info(f"画像URL挿入完了: {len(image_messages)}枚挿入, 最終コンテンツサイズ: {len(new_content)}文字")
        return new_content

    except Exception as e:
        logger.error(f"画像URL挿入エラー: {e}")
        import traceback
        traceback.print_exc()
        return content  # エラー時は元のコンテンツを返す

def extract_fallback_queries(content: str) -> List[str]:
    '''Gemini等が失敗した場合の簡易キーワード抽出フォールバック'''
    import re
    # ひらがな・カタカナ・漢字・英数字の単語を抽出
    words = re.findall(r'[\w\u3040-\u30ff\u4e00-\u9fff]{2,}', content)
    # 頻出上位3件を返す
    from collections import Counter
    common = [w for w, _ in Counter(words).most_common(3)]
    return common

def extract_search_queries_from_content(content: str) -> List[str]:
    '''コンテンツからWeb検索用のクエリをAIで動的に抽出'''
    try:
        # RAGでジャンル特化プロンプトを取得
        rag_prompt = None
        try:
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from src.rag import predict_with_model
            query_text = content[:100]
            rag_results = predict_with_model(query_text, 'genre_prompts', top_n=1)
            if rag_results and len(rag_results) > 0:
                rag_prompt = rag_results[0]['text']
                logger.info(f"RAG抽出プロンプト: {rag_prompt[:60]}...")
        except Exception as e:
            logger.error(f"RAGプロンプト抽出エラー: {e}")

        # Geminiで検索クエリ抽出
        extraction_prompt_template = (
            "{rag_prompt}\n"
            "以下のコンテンツを分析して、読者にとって有益な追加情報を得るためのWeb検索クエリを3つまで抽出してください。\n"
            "\nコンテンツ:\n"
            "{content}\n"
            "\n出力形式:\n"
            "検索クエリ1\n"
            "検索クエリ2\n"
            "検索クエリ3\n"
            "\n※各クエリは30文字以内で、検索しやすい形にしてください\n"
            "※関連性の高い順に並べてください\n"
            "※クエリが3つ未満の場合は、その分だけ出力してください"
        )
        extraction_prompt = extraction_prompt_template.replace('{rag_prompt}', rag_prompt if rag_prompt else '').replace('{content}', content)
        queries = []
        try:
            logger.info("Geminiによる検索クエリ抽出を開始")
            extraction_result = gemini_service.generate_content(extraction_prompt)
            if extraction_result and extraction_result.strip():
                lines = extraction_result.strip().split('\n')
                import re
                for line in lines:
                    line = line.strip()
                    # HTMLタグ除去
                    line = re.sub(r'<.*?>', '', line)
                    clean_line = re.sub(r'^[\d\.\-\*\+]?\s*', '', line)
                    clean_line = re.sub(r'^[「『]|[」』]$', '', clean_line)
                    if clean_line and len(clean_line) > 3 and len(clean_line) <= 50:
                        queries.append(clean_line)
        except Exception as e:
            logger.error(f"Gemini検索クエリ抽出エラー: {e}")
        if queries:
            final_queries = queries[:3]
            logger.info(f"Gemini抽出クエリ: {final_queries}")
            return final_queries
        else:
            # Geminiが失敗した場合のフォールバック
            logger.info("フォールバック：基本キーワード抽出を実行")
            return extract_fallback_queries(content)
    except Exception as e:
        logger.error(f"検索クエリ抽出エラー: {e}")
        return []

# バッチ処理状況確認用エンドポイント
