import os
import requests
from typing import List, Dict, Optional, Tuple
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from datetime import datetime
import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

# Attempt to import bingart
try:
    from bingart import BingArt
    BINGART_AVAILABLE = True
except ImportError:
    BINGART_AVAILABLE = False
    logger.warning("bingart library not found. Image generation with Bing Image Creator will not be available. "
                   "Install with: pip install bingart")

class ImageGenerator:
    """
    Generates and processes images, primarily using Bing Image Creator via the 'bingart' library.
    Also includes utilities for downloading, saving, and optimizing images.
    """
    def __init__(self, bing_auth_cookie_U: Optional[str] = None, output_dir: str = "./generated_images"):
        """
        Initializes the ImageGenerator.

        Args:
            bing_auth_cookie_U: The '_U' authentication cookie for Bing Image Creator.
                                Required for image generation with Bing.
            output_dir: Directory to save generated and processed images.
        """
        self.bing_auth_cookie_U = bing_auth_cookie_U
        self.output_dir = output_dir
        self.bing_art_instance: Optional[BingArt] = None

        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except OSError as e:
                logger.error(f"Failed to create output directory {self.output_dir}: {e}")
                # Fallback to a temporary directory or handle error as appropriate
                # For now, will proceed and operations requiring dir will fail individually.

        if BINGART_AVAILABLE and self.bing_auth_cookie_U:
            try:
                self.bing_art_instance = BingArt(auth_cookie_U=self.bing_auth_cookie_U)
                logger.info("BingArt instance initialized successfully.")
            except Exception as e: # Catching general exception as bingart might raise various things
                logger.error(f"Failed to initialize BingArt: {e}. Bing image generation will be unavailable.")
                self.bing_art_instance = None
        elif not self.bing_auth_cookie_U and BINGART_AVAILABLE:
             logger.warning("BingArt is available, but auth cookie was not provided. Bing image generation disabled.")


    def generate_images_with_bing(self, prompt: str, timeout_sec: int = 300) -> List[str]:
        """
        Generates images using Bing Image Creator based on a prompt.

        Args:
            prompt: The text prompt to generate images from.
            timeout_sec: Timeout in seconds for the image generation process.

        Returns:
            A list of URLs of the generated images. Empty if generation fails.
        """
        if not self.bing_art_instance:
            logger.error("BingArt instance is not available. Cannot generate images.")
            return []
        if not prompt:
            logger.warning("Image generation prompt is empty.")
            return []

        try:
            logger.info(f"Requesting image generation from Bing with prompt: '{prompt[:100]}...'")
            # The bingart library's generate_images might return None or raise an exception on failure
            generated_image_urls = self.bing_art_instance.generate_images(prompt, timeout=timeout_sec)

            if generated_image_urls and isinstance(generated_image_urls, list):
                logger.info(f"Successfully generated {len(generated_image_urls)} image(s) from Bing.")
                return generated_image_urls
            else:
                logger.warning(f"Bing image generation returned no URLs for prompt: '{prompt[:100]}...'")
                return []
        except Exception as e:
            logger.error(f"Error during Bing image generation for prompt '{prompt[:100]}...': {e}")
            return []

    def download_image(self, image_url: str) -> Optional[BytesIO]:
        """Downloads an image from a URL."""
        if not image_url:
            return None
        try:
            response = requests.get(image_url, timeout=20)
            response.raise_for_status()
            return BytesIO(response.content)
        except requests.RequestException as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return None

    def save_image(self, image_data: BytesIO, filename_prefix: str = "image") -> Optional[str]:
        """
        Saves image data (from BytesIO) to a file in the output directory.
        The filename will be unique using a timestamp.
        It tries to save in PNG format.

        Args:
            image_data: Image data as BytesIO object.
            filename_prefix: Prefix for the image filename.

        Returns:
            The full path to the saved image file, or None if saving fails.
        """
        if not image_data:
            return None

        try:
            image = Image.open(image_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            # Ensure filename is safe
            safe_prefix = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in filename_prefix)
            filename = f"{safe_prefix}_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)

            image.save(filepath, "PNG")
            logger.info(f"Image saved successfully to {filepath}")
            return filepath
        except UnidentifiedImageError:
            logger.error("Cannot identify image file (possibly corrupt or unsupported format).")
            return None
        except IOError as e:
            logger.error(f"IOError saving image to {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error saving image: {e}")
            return None


    def generate_and_save_bing_image(self, prompt: str, filename_prefix: str = "bing_gen") -> Optional[str]:
        """Convenience method to generate an image with Bing and save the first result."""
        image_urls = self.generate_images_with_bing(prompt)
        if image_urls:
            image_data = self.download_image(image_urls[0])
            if image_data:
                return self.save_image(image_data, filename_prefix)
        return None

    def create_featured_image_for_article(
        self, article_title: str, article_summary: Optional[str] = None,
        style_preference: str = "modern blog header, digital art"
    ) -> Optional[str]:
        """
        Creates a featured image for a blog article using its title and summary.

        Args:
            article_title: The title of the article.
            article_summary: A short summary of the article (optional).
            style_preference: Preferred style for the image (e.g., "minimalist", "photo-realistic").

        Returns:
            Path to the saved featured image, or None on failure.
        """
        if not article_title:
            logger.warning("Article title is required to generate a featured image.")
            return None

        prompt_parts = [f"Featured header image for a blog article titled '{article_title}'."]
        if article_summary:
            prompt_parts.append(f"The article is about: '{article_summary[:200]}'.") # Limit summary length
        prompt_parts.append(f"Style: {style_preference}.")
        prompt_parts.append("The image should be eye-catching, professional, and relevant to the topic.")

        prompt = " ".join(prompt_parts)

        safe_title_prefix = "".join(c if c.isalnum() else '_' for c in article_title[:30])
        return self.generate_and_save_bing_image(prompt, filename_prefix=f"featured_{safe_title_prefix}")


    def optimize_image_for_web(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        max_width: int = 1200,
        quality: int = 85,
        output_format: str = "JPEG" # JPEG or WEBP typically
    ) -> Optional[str]:
        """
        Optimizes an image for web use: resizes, converts format, and adjusts quality.

        Args:
            image_path: Path to the source image.
            output_path: Path to save the optimized image. If None, appends '_optimized'
                         to the original filename (with new extension).
            max_width: Maximum width for the resized image. Aspect ratio is maintained.
            quality: Quality setting for JPEG/WEBP (0-100, higher is better).
            output_format: Desired output format ("JPEG", "PNG", "WEBP").

        Returns:
            Path to the optimized image, or None on failure.
        """
        if not os.path.exists(image_path):
            logger.error(f"Source image not found for optimization: {image_path}")
            return None

        try:
            image = Image.open(image_path)

            # Resize if wider than max_width
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Determine output path and format
            if output_path is None:
                base, orig_ext = os.path.splitext(image_path)
                new_ext = f".{output_format.lower()}"
                output_path = f"{base}_optimized{new_ext}"

            # Convert to RGB if saving as JPEG (handles RGBA PNGs)
            if output_format.upper() == "JPEG" and image.mode != 'RGB':
                image = image.convert('RGB')

            # Save with optimization
            if output_format.upper() == "WEBP":
                image.save(output_path, output_format.upper(), quality=quality, method=6) # method 6 is slowest, best compression
            else: # JPEG, PNG
                image.save(output_path, output_format.upper(), quality=quality, optimize=True)

            logger.info(f"Image optimized and saved to {output_path}")
            return output_path

        except FileNotFoundError: # Should be caught by os.path.exists, but as fallback
            logger.error(f"Source image not found (during open): {image_path}")
            return None
        except UnidentifiedImageError:
            logger.error(f"Cannot identify image file for optimization: {image_path}")
            return None
        except Exception as e:
            logger.error(f"Error optimizing image {image_path}: {e}")
            return None

    def close_bing_session(self):
        """Closes the BingArt session if it's open."""
        if self.bing_art_instance:
            try:
                self.bing_art_instance.close_session()
                logger.info("BingArt session closed.")
            except Exception as e:
                logger.warning(f"Error closing BingArt session: {e}")


if __name__ == '__main__':
    # Basic logging setup for the example
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print(f"--- Testing ImageGenerator (BingArt available: {BINGART_AVAILABLE}) ---")

    # IMPORTANT: For Bing generation tests, you need to set the BING_AUTH_COOKIE_U environment variable.
    bing_cookie = os.getenv("BING_AUTH_COOKIE_U")

    if not bing_cookie and BINGART_AVAILABLE:
        print("BING_AUTH_COOKIE_U environment variable not set. Skipping Bing generation tests.")
        print("Set it to your Bing '_U' cookie value to run these tests.")

    generator = ImageGenerator(bing_auth_cookie_U=bing_cookie, output_dir="./test_generated_images")

    if generator.bing_art_instance:
        print("\\n--- Test 1: Generate and Save Image with Bing ---")
        bing_prompt = "A cute cat programmer writing Python code, digital art"
        saved_bing_image_path = generator.generate_and_save_bing_image(bing_prompt, "cute_cat_prog")
        if saved_bing_image_path:
            print(f"Bing image generated and saved to: {saved_bing_image_path}")

            print("\\n--- Test 2: Optimize the generated image ---")
            optimized_path = generator.optimize_image_for_web(saved_bing_image_path, max_width=800, output_format="WEBP")
            if optimized_path:
                print(f"Image optimized and saved to: {optimized_path}")
        else:
            print(f"Failed to generate or save Bing image for prompt: {bing_prompt}")

        print("\\n--- Test 3: Create Featured Image for Article ---")
        featured_image_path = generator.create_featured_image_for_article(
            article_title="The Future of AI in Software Development",
            article_summary="Exploring how artificial intelligence is reshaping the landscape of coding and software engineering.",
            style_preference="futuristic, abstract, blue and silver tones"
        )
        if featured_image_path:
            print(f"Featured image created and saved to: {featured_image_path}")
        else:
            print("Failed to create featured image.")

        generator.close_bing_session()
    else:
        print("BingArt instance not available, skipping Bing-dependent tests.")

    # Test image download and save with a public placeholder image
    print("\\n--- Test 4: Download and Save Public Image (Placeholder) ---")
    placeholder_url = "https://via.placeholder.com/300/09f/fff.png" # A public placeholder service
    img_data = generator.download_image(placeholder_url)
    if img_data:
        saved_placeholder_path = generator.save_image(img_data, "placeholder_test")
        if saved_placeholder_path:
            print(f"Placeholder image downloaded and saved to: {saved_placeholder_path}")

            print("\\n--- Test 5: Optimize the placeholder image (to JPEG) ---")
            optimized_placeholder_jpeg = generator.optimize_image_for_web(
                saved_placeholder_path, max_width=150, output_format="JPEG"
            )
            if optimized_placeholder_jpeg:
                 print(f"Placeholder image optimized to JPEG: {optimized_placeholder_jpeg}")
        else:
            print("Failed to save downloaded placeholder image.")
    else:
        print(f"Failed to download placeholder image from {placeholder_url}")


    print("\\nImageGenerator tests finished. Check the 'test_generated_images' directory.")
