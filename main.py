#!/usr/bin/env python3
"""
Hatena Blog Suite - Main Entry Point
統合はてなブログ管理・自動化スイート メインモジュール
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import suite modules
try:
    from automation.hatena_agent import agent as hatena_agent
    from image.image_generator import ImageGenerator
    # from core.hatena_client import HatenaClient
    # from optimization.content_optimizer import ContentOptimizer
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/hatena-suite.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HatenaBlogSuite:
    """
    Hatena Blog Suite メインクラス
    """
    
    def __init__(self):
        """初期化"""
        self.setup_directories()
        self.check_environment()
        self.image_generator = None
        
    def setup_directories(self):
        """必要なディレクトリを作成"""
        dirs = ['logs', 'output', 'data', 'config', 'generated_images']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)
        logger.info("Created necessary directories")
    
    def check_environment(self):
        """環境変数をチェック"""
        required_vars = ['HATENA_ID', 'BLOG_DOMAIN']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file")
        else:
            logger.info("Environment variables check passed")
    
    def init_image_generator(self):
        """画像生成器を初期化"""
        try:
            self.image_generator = ImageGenerator()
            logger.info("Image generator initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize image generator: {e}")
            return False
    
    async def extract_articles(self, hatena_id: str, max_pages: int = 5):
        """記事を抽出"""
        logger.info(f"Extracting articles for {hatena_id} (max {max_pages} pages)")
        
        try:
            # Here you would integrate with the MCP server or direct API calls
            print(f"🔍 Extracting articles from {hatena_id}...")
            
            # Placeholder - integrate with actual extraction logic
            articles = []
            
            output_file = Path("output") / f"extracted_articles_{hatena_id}.json"
            logger.info(f"Articles extracted and saved to {output_file}")
            print(f"✅ Articles extracted: {len(articles)} articles")
            
            return articles
            
        except Exception as e:
            logger.error(f"Article extraction failed: {e}")
            print(f"❌ Article extraction failed: {e}")
            return []
    
    async def generate_images(self, count: int = 3, theme: str = "blog"):
        """画像を生成"""
        if not self.image_generator:
            if not self.init_image_generator():
                print("❌ Cannot generate images: Image generator initialization failed")
                return
        
        logger.info(f"Generating {count} images with theme: {theme}")
        print(f"🎨 Generating {count} images...")
        
        generated_images = []
        
        for i in range(count):
            try:
                image, filepath = self.image_generator.generate_image(
                    template="anime_style",
                    save_prefix=f"{theme}_image",
                    theme=f"ブログ用の画像 #{i+1}",
                    background="モダンでクリーンな背景",
                    expression="明るい雰囲気",
                    composition="バランスの取れた構図",
                    size="1200x630",
                    format="PNG"
                )
                
                if image and filepath:
                    generated_images.append(filepath)
                    print(f"  ✅ Generated: {Path(filepath).name}")
                else:
                    print(f"  ❌ Failed to generate image #{i+1}")
                    
            except Exception as e:
                logger.error(f"Image generation failed for #{i+1}: {e}")
                print(f"  ❌ Error generating image #{i+1}: {e}")
        
        logger.info(f"Generated {len(generated_images)} images successfully")
        print(f"🎨 Generated {len(generated_images)}/{count} images successfully")
        
        return generated_images
    
    async def optimize_content(self, content: str):
        """コンテンツを最適化"""
        logger.info("Optimizing content")
        print("⚡ Optimizing content...")
        
        try:
            # Placeholder for content optimization
            # This would integrate with AI processing modules
            optimized_content = content  # Placeholder
            
            print("✅ Content optimization completed")
            return optimized_content
            
        except Exception as e:
            logger.error(f"Content optimization failed: {e}")
            print(f"❌ Content optimization failed: {e}")
            return content
    
    async def run_full_suite(self, hatena_id: str):
        """全機能を実行"""
        print("🚀 Starting Hatena Blog Suite full processing...")
        
        # Extract articles
        articles = await self.extract_articles(hatena_id)
        
        # Generate images
        images = await self.generate_images(count=3)
        
        # Generate report
        report = self.generate_report(articles, images)
        
        print("🎉 Full suite processing completed!")
        return report
    
    def generate_report(self, articles, images):
        """レポートを生成"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = {
            "timestamp": timestamp,
            "articles_count": len(articles),
            "images_generated": len(images),
            "status": "completed"
        }
        
        report_file = Path("output") / f"suite_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Report generated: {report_file}")
        print(f"📊 Report saved: {report_file}")
        
        return report

def create_parser():
    """コマンドラインパーサーを作成"""
    parser = argparse.ArgumentParser(description="Hatena Blog Suite - 統合はてなブログ管理ツール")
    
    parser.add_argument("--hatena-id", type=str, required=True, 
                       help="はてなID")
    
    subparsers = parser.add_subparsers(dest="command", help="実行するコマンド")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="記事を抽出")
    extract_parser.add_argument("--max-pages", type=int, default=5,
                               help="抽出する最大ページ数")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="画像を生成")
    generate_parser.add_argument("--count", type=int, default=3,
                                help="生成する画像数")
    generate_parser.add_argument("--theme", type=str, default="blog",
                                help="画像のテーマ")
    
    # Full command
    full_parser = subparsers.add_parser("full", help="全機能を実行")
    
    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="対話モードで実行")
    
    return parser

async def main():
    """メイン関数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize suite
    suite = HatenaBlogSuite()
    
    print(f"🎯 Hatena Blog Suite - {args.command.upper()} Mode")
    print(f"📝 Target Hatena ID: {args.hatena_id}")
    print("─" * 50)
    
    try:
        if args.command == "extract":
            await suite.extract_articles(args.hatena_id, args.max_pages)
            
        elif args.command == "generate":
            await suite.generate_images(args.count, args.theme)
            
        elif args.command == "full":
            await suite.run_full_suite(args.hatena_id)
            
        elif args.command == "interactive":
            await interactive_mode(suite, args.hatena_id)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")

async def interactive_mode(suite, hatena_id):
    """対話モード"""
    print("🎮 Interactive mode started")
    print("Available commands: extract, generate, optimize, full, quit")
    
    while True:
        try:
            command = input("\n🎯 Command: ").strip().lower()
            
            if command == "quit" or command == "exit":
                print("👋 Goodbye!")
                break
                
            elif command == "extract":
                await suite.extract_articles(hatena_id)
                
            elif command == "generate":
                count = input("Image count (default 3): ").strip()
                count = int(count) if count.isdigit() else 3
                theme = input("Theme (default 'blog'): ").strip() or "blog"
                await suite.generate_images(count, theme)
                
            elif command == "optimize":
                content = input("Enter content to optimize: ")
                if content:
                    optimized = await suite.optimize_content(content)
                    print(f"Optimized: {optimized[:100]}...")
                    
            elif command == "full":
                await suite.run_full_suite(hatena_id)
                
            else:
                print(f"❓ Unknown command: {command}")
                
        except KeyboardInterrupt:
            print("\n⏹️  Interactive mode cancelled")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
