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
        # 【2回目Gemini】すべてのテキスト情報を統合してブログ記事を生成
        all_texts = []
        
        # テキストメッセージを追加
        if text_messages:
            for msg in text_messages:
                all_texts.append(f"【メッセージ】{msg['content']}")
        
        # 画像メッセージのテキスト化された内容を追加
        if image_messages:
            for msg in image_messages:
                # message['content']には既にGeminiで解析されたテキストが保存されている
                if msg.get('content'):
                    all_texts.append(msg['content'])  # 【画像解析結果】が含まれる
        
        # 動画メッセージがあれば追加
        if video_messages:
            for msg in video_messages:
                all_texts.append(f"【動画】{msg.get('content', '動画が投稿されました')}")
        
        if not all_texts:
            logger.warning("統合するテキストコンテンツがありません")
            return None, None
        
        # すべてのテキストを時系列順に結合
        combined_all_text = "\n\n".join(all_texts)
        
        logger.info(f"【2回目Gemini】ブログ記事生成開始 - 統合テキスト: {len(combined_all_text)}文字")
        
        # Geminiでタイトルと本文を分けて生成
        blog_prompt = f"""
以下のテキスト情報から、自然で読みやすいブログ記事を作成してください：

{combined_all_text}

要件:
1. 最初の行にタイトルを記載してください
2. 2行目以降に本文を記載してください
3. 自然で読みやすい文章にしてください
4. 画像解析結果については、ぼやかして抽象化してください
5. 技術的な分析よりも、読者が楽しめる内容にしてください
6. 本文は1500字以内にしてください
https://lifehacking1919.hatenablog.jp/entry/2022/01/30/153627　と口調を合わせてください

フォーマット:
タイトル
本文内容...
"""
        
        integrated_content = gemini_service.generate_content(blog_prompt)
        
        if integrated_content and integrated_content.strip():
            logger.info(f"【2回目Gemini】ブログ記事生成成功: {len(integrated_content)}文字")
            
            # タイトルと本文を分離
            lines = integrated_content.split('\n', 1)
            if len(lines) > 1:
                title = lines[0].strip()
                content = lines[1].strip()
            else:
                title = lines[0].strip()
                content = integrated_content
            
            logger.info(f"抽出されたタイトル: {title}")
            return title, content
        else:
            logger.error("【2回目Gemini】ブログ記事生成が空の結果を返しました")
            return None, None
        
    except Exception as e:
        logger.error(f"統合コンテンツ作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def insert_imgur_urls_to_content(content: str, image_messages: List[Dict]) -> str:
    """ブログ記事にImgur URLをルールベースで挿入"""
    try:
        if not image_messages:
            return content
        
        logger.info(f"画像URL挿入開始: {len(image_messages)}枚の画像")
        
        # 画像URLを収集
        imgur_urls = []
        for img_msg in image_messages:
            imgur_url = img_msg.get('imgur_url')
            if imgur_url:
                imgur_urls.append(imgur_url)
                logger.info(f"挿入予定URL: {imgur_url}")
        
        if not imgur_urls:
            logger.warning("挿入可能なImgur URLがありません")
            return content
        
        # 記事の最後に画像を追加
        image_html_tags = []
        for i, url in enumerate(imgur_urls, 1):
            html_tag = f'<p><img src="{url}" alt="画像{i}" style="max-width: 80%; height: auto; display: block; margin: 20px auto; border: 1px solid #ddd; border-radius: 8px;"></p>'
            image_html_tags.append(html_tag)
        
        # 記事本文 + 改行 + 画像セクション + 画像HTML
        final_content = f"""{content}

## 📸 投稿画像

{chr(10).join(image_html_tags)}"""
        
        logger.info(f"画像URL挿入完了: {len(imgur_urls)}枚挿入, 最終コンテンツサイズ: {len(final_content)}文字")
        return final_content
        
    except Exception as e:
        logger.error(f"画像URL挿入エラー: {e}")
        import traceback
        traceback.print_exc()
        return content  # エラー時は元のコンテンツを返す

# バッチ処理状況確認用エンドポイント
