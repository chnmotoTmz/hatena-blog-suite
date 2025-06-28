import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import json
import traceback
import logging

class ImageGenerator:
    def __init__(self, output_dir: str = "generated_images"):
        """
        画像生成クラスの初期化
        
        Args:
            output_dir (str): 生成した画像の保存ディレクトリ
        """
        # 環境変数の読み込み
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEYが設定されていません")

        # Gemini APIクライアントの初期化
        self.client = genai.Client(api_key=self.api_key)
        
        # 出力ディレクトリの設定
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ログの設定
        self._setup_logging()
        
        # 生成履歴の初期化
        self.history_file = self.output_dir / "generation_history.json"
        self.history = self._load_history()

    def _setup_logging(self):
        """ロギングの設定"""
        log_file = self.output_dir / "image_generation.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_history(self) -> List[Dict]:
        """生成履歴の読み込み"""
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_history(self):
        """生成履歴の保存"""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def _create_prompt(self, template: str, **kwargs) -> str:
        """
        プロンプトテンプレートの作成
        
        Args:
            template (str): テンプレート名
            **kwargs: テンプレートに埋め込むパラメータ
            
        Returns:
            str: 生成されたプロンプト
        """
        templates = {
            "anime_style": """
            以下の仕様で画像を生成してください：
            テーマ：{theme}
            スタイル：アニメ調
            背景：{background}
            表情：{expression}
            構図：{composition}
            サイズ：{size}
            フォーマット：{format}
            """,
            "watercolor": """
            以下の仕様で水彩画風の画像を生成してください：
            テーマ：{theme}
            色調：{color_tone}
            背景：{background}
            構図：{composition}
            サイズ：{size}
            フォーマット：{format}
            """
        }
        
        if template not in templates:
            raise ValueError(f"未知のテンプレート: {template}")
            
        return templates[template].format(**kwargs)

    def generate_image(
        self,
        template: str,
        save_prefix: str,
        **kwargs
    ) -> Tuple[Optional[Image.Image], str]:
        """
        画像の生成
        
        Args:
            template (str): 使用するプロンプトテンプレート
            save_prefix (str): 保存ファイル名のプレフィックス
            **kwargs: テンプレートに渡すパラメータ
            
        Returns:
            Tuple[Optional[Image.Image], str]: 生成された画像とファイルパス
        """
        try:
            # プロンプトの生成
            prompt = self._create_prompt(template, **kwargs)
            self.logger.info(f"プロンプト: {prompt}")
            
            # 画像生成リクエスト
            response = self.client.models.generate_content(
                model="models/gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['Text', 'Image']
                )
            )
            
            # 生成された画像の処理
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text is not None:
                        self.logger.info(f"テキストレスポンス: {part.text}")
                    
                    if part.inline_data is not None:
                        # 画像データの取得と処理
                        image_data = part.inline_data.data
                        image = Image.open(BytesIO(image_data))
                        
                        # 画像情報のログ
                        self.logger.info(f"画像フォーマット: {image.format}")
                        self.logger.info(f"画像サイズ: {image.size}")
                        
                        # リサイズと保存
                        target_size = tuple(map(int, kwargs.get("size", "1200x630").split("x")))
                        resized_image = image.resize(target_size)
                        
                        # ファイル名の生成
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{save_prefix}_{timestamp}.png"
                        filepath = self.output_dir / filename
                        
                        # 画像の保存
                        resized_image.save(filepath, format='PNG')
                        self.logger.info(f"画像を保存しました: {filepath}")
                        
                        # 生成履歴の更新
                        history_entry = {
                            "timestamp": timestamp,
                            "template": template,
                            "parameters": kwargs,
                            "prompt": prompt,
                            "filepath": str(filepath)
                        }
                        self.history.append(history_entry)
                        self._save_history()
                        
                        return resized_image, str(filepath)
            
            self.logger.error("画像の生成に失敗しました")
            return None, ""
            
        except Exception as e:
            self.logger.error(f"エラーが発生しました: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None, ""

    def get_history(self, limit: int = None) -> List[Dict]:
        """
        生成履歴の取得
        
        Args:
            limit (int, optional): 取得する履歴の数
            
        Returns:
            List[Dict]: 生成履歴のリスト
        """
        if limit is None:
            return self.history
        return self.history[-limit:]

def main():
    """使用例"""
    generator = ImageGenerator()
    
    # アニメ調の画像生成
    image, filepath = generator.generate_image(
        template="anime_style",
        save_prefix="anime_cat",
        theme="赤いリボンの黒猫が東京の空を飛んでいる",
        background="夕焼け空と東京タワーのシルエット",
        expression="楽しそうな表情",
        composition="猫が画面中央に配置され、背景に東京タワーが映っている",
        size="1200x630",
        format="PNG"
    )
    
    if image:
        print(f"画像が生成されました: {filepath}")
        image.show()
    
    # 水彩画風の画像生成
    image, filepath = generator.generate_image(
        template="watercolor",
        save_prefix="watercolor_fuji",
        theme="富士山の山頂からの日の出の眺め",
        color_tone="暖かみのある色調",
        background="空に薄い雲、遠くに街の明かり",
        composition="富士山を中心に、周囲の風景が広がる",
        size="1200x630",
        format="PNG"
    )
    
    if image:
        print(f"画像が生成されました: {filepath}")
        image.show()

if __name__ == "__main__":
    main() 
