import io
from typing import Tuple

import numpy as np
from PIL import Image
from PIL import ImageOps


class ImageProcessor:
    """画像処理・最適化サービス"""

    @staticmethod
    async def optimize_image(image_data: bytes, max_size: Tuple[int, int] = (1920, 1080), quality: int = 85) -> bytes:
        """画像最適化"""
        # バイナリデータから画像を開く
        img = Image.open(io.BytesIO(image_data))

        # EXIF情報を保持しながら向きを修正
        img = ImageOps.exif_transpose(img)

        # リサイズ（アスペクト比を保持）
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 最適化して保存
        output = io.BytesIO()
        if img.mode == "RGBA":
            # 透過PNGの場合、背景を白にしてJPEGに変換
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            background.save(output, "JPEG", quality=quality, optimize=True)
        else:
            # RGB画像はそのままJPEGで保存
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(output, "JPEG", quality=quality, optimize=True)

        return output.getvalue()

    @staticmethod
    async def create_webp(image_data: bytes, quality: int = 80) -> bytes:
        """WebP形式に変換"""
        img = Image.open(io.BytesIO(image_data))
        output = io.BytesIO()
        img.save(output, "WebP", quality=quality, method=6)
        return output.getvalue()

    @staticmethod
    async def extract_dominant_colors(image_data: bytes, num_colors: int = 5) -> list:
        """主要な色を抽出"""
        img = Image.open(io.BytesIO(image_data))
        img = img.convert("RGB")
        img = img.resize((150, 150))  # 計算速度のため縮小

        # NumPy配列に変換
        pixels = np.array(img)
        pixels = pixels.reshape(-1, 3)

        # K-means風の簡易クラスタリング
        from collections import Counter

        pixel_counts = Counter(map(tuple, pixels))
        most_common = pixel_counts.most_common(num_colors)

        return [{"rgb": color, "hex": "#{:02x}{:02x}{:02x}".format(*color)} for color, _ in most_common]

    @staticmethod
    async def add_watermark(image_data: bytes, watermark_text: str, position: str = "bottom-right") -> bytes:
        """ウォーターマーク追加"""
        from PIL import ImageDraw
        from PIL import ImageFont

        img = Image.open(io.BytesIO(image_data))
        draw = ImageDraw.Draw(img)

        # フォントサイズを画像サイズに応じて調整
        font_size = max(20, min(img.width, img.height) // 20)

        # デフォルトフォントを使用
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # テキストサイズを取得
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # 位置計算
        margin = 10
        if position == "bottom-right":
            x = img.width - text_width - margin
            y = img.height - text_height - margin
        elif position == "bottom-left":
            x = margin
            y = img.height - text_height - margin
        elif position == "top-right":
            x = img.width - text_width - margin
            y = margin
        else:  # top-left
            x = margin
            y = margin

        # 半透明の背景
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([x - 5, y - 5, x + text_width + 5, y + text_height + 5], fill=(0, 0, 0, 128))
        overlay_draw.text((x, y), watermark_text, fill=(255, 255, 255, 255), font=font)

        # 合成
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")

        # 保存
        output = io.BytesIO()
        img.save(output, "JPEG", quality=90)
        return output.getvalue()
