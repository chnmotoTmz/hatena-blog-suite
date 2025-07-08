#!/usr/bin/env python3
"""
Production startup script for LINE-Gemini-Hatena MCP AI Agent System
"""

import os
import sys
import logging
from flask import Flask, jsonify

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Flask アプリケーションを作成"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        """ヘルスチェックエンドポイント"""
        return jsonify({
            'status': 'healthy',
            'service': 'LINE-Gemini-Hatena Integration',
            'port': os.getenv('PORT', '8083'),
            'version': '1.0.0'
        })
    
    @app.route('/')
    def index():
        """メインページ"""
        return jsonify({
            'message': 'LINE-Gemini-Hatena MCP AI Agent System',
            'status': 'running',
            'endpoints': ['/health', '/webhook/line']
        })
    @app.route('/webhook/line', methods=['GET'])
    def line_webhook_get():
        return 'OK', 200

    @app.route('/webhook/line', methods=['POST'])
    def line_webhook():
        """LINE Webhook エンドポイント"""
        return jsonify({'message': 'LINE webhook received'})
    
    return app

def main():
    """メイン関数"""
    try:
        # ポートを強制的に8083に設定
        host = os.getenv('HOST', '0.0.0.0')
        port = 8083  # 環境変数を無視して8083に固定
        
        logger.info("=== LINE-Gemini-Hatena統合システム起動 ===")
        logger.info(f"ホスト: {host}")
        logger.info(f"ポート: {port}")
        
        # Flask アプリケーションを作成
        app = create_app()
        
        # アプリケーション起動（ポート8083で固定）
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ アプリケーション起動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()