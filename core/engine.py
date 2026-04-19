"""
core/engine.py
Renders a list of BaseElement objects into a PIL Image at a given DPI.
Supports Text, Barcode (Code128/QR/EAN13/UPC-A/Code39), Image, and Rect elements.
Variable interpolation: any {variable} in text is replaced from a data_row dict.
"""
import io
import re
from PIL import Image, ImageDraw, ImageFont
from typing import List, Optional
from core.elements import (BaseElement, TextElement, BarcodeElement,
                           ImageElement, RectElement,
                           ELEMENT_TEXT, ELEMENT_BARCODE, ELEMENT_IMAGE, ELEMENT_RECT)


DP_MM = 8   # pixels per mm at 203 DPI (203/25.4 ≈ 8)


def mm_to_px(mm: float) -> int:
    return max(1, int(round(mm * DP_MM)))


def _render_text(draw: ImageDraw.Draw, el: TextElement, data_row: dict = None):
    text = el.text
    if data_row:
        text = _interpolate(text, data_row)

    try:
        from PIL import ImageFont
        font = ImageFont.truetype(_resolve_font(el.font_family, el.bold, el.italic), el.font_size)
    except Exception:
        font = ImageFont.load_default()

    x = mm_to_px(el.x)
    y = mm_to_px(el.y)
    w = mm_to_px(el.width)

    fill = el.color or "#000000"
    draw.text((x, y), text, fill=fill, font=font)


def _resolve_font(family: str, bold: bool, italic: bool) -> str:
    """Try to find a system font by family. Falls back gracefully."""
    import os, platform
    system = platform.system()

    candidates = []
    suffix = ""
    if bold and italic:
        suffix = " Bold Italic"
    elif bold:
        suffix = " Bold"
    elif italic:
        suffix = " Italic"

    name = family + suffix

    if system == "Darwin":
        for base in ["/Library/Fonts", "/System/Library/Fonts", "/System/Library/Fonts/Supplemental"]:
            for ext in [".ttf", ".otf"]:
                candidates.append(os.path.join(base, name + ext))
                candidates.append(os.path.join(base, family + ext))
    elif system == "Windows":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        for ext in [".ttf", ".otf"]:
            candidates.append(os.path.join(windir, "Fonts", name + ext))
            candidates.append(os.path.join(windir, "Fonts", family + ext))
    else:
        candidates += [
            f"/usr/share/fonts/truetype/{family.lower()}/{name}.ttf",
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]

    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Font '{family}' not found")


def _render_barcode(img: Image.Image, el: BarcodeElement, data_row: dict = None):
    code = el.code
    if data_row:
        code = _interpolate(code, data_row)

    x = mm_to_px(el.x)
    y = mm_to_px(el.y)
    w = mm_to_px(el.width)
    h = mm_to_px(el.height)

    bc_img = None
    btype = el.barcode_type.lower()

    if btype == "qr":
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=4, border=1)
            qr.add_data(code)
            qr.make(fit=True)
            bc_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        except Exception as e:
            print(f"QR error: {e}")
    else:
        try:
            import barcode as pybarcode
            from barcode.writer import ImageWriter

            # Map friendly name to python-barcode name
            type_map = {
                "code128": "code128",
                "ean13": "ean13",
                "ean8": "ean8",
                "upca": "upc-a",
                "code39": "code39",
            }
            bc_name = type_map.get(btype, "code128")
            bc_class = pybarcode.get_barcode_class(bc_name)
            writer = ImageWriter()
            writer.set_options({
                "module_height": 10.0,
                "font_size": 6 if el.show_text else 0,
                "text_distance": 3.0,
                "quiet_zone": 1.0,
                "write_text": el.show_text,
            })
            bc_img = bc_class(code, writer=writer).render().convert("RGB")
        except Exception as e:
            print(f"Barcode error ({btype}): {e}")

    if bc_img and w > 0 and h > 0:
        bc_img = bc_img.resize((w, h), Image.LANCZOS)
        img.paste(bc_img, (x, y))


def _render_image(img: Image.Image, el: ImageElement):
    if not el.path:
        return
    try:
        logo = Image.open(el.path).convert("RGBA")
        w = mm_to_px(el.width)
        h = mm_to_px(el.height)
        if el.keep_aspect:
            logo.thumbnail((w, h), Image.LANCZOS)
        else:
            logo = logo.resize((w, h), Image.LANCZOS)
        x = mm_to_px(el.x)
        y = mm_to_px(el.y)
        # Paste with alpha mask
        bg = Image.new("RGBA", img.size)
        bg.paste(img.convert("RGBA"), (0, 0))
        bg.paste(logo, (x, y), mask=logo)
        result = bg.convert("RGB")
        img.paste(result)
    except Exception as e:
        print(f"Image render error: {e}")


def _render_rect(draw: ImageDraw.Draw, el: RectElement):
    x0 = mm_to_px(el.x)
    y0 = mm_to_px(el.y)
    x1 = x0 + mm_to_px(el.width)
    y1 = y0 + mm_to_px(el.height)
    fill = el.fill_color if el.filled else None
    outline = el.border_color
    width = max(1, int(el.border_width))
    draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)


def _interpolate(text: str, data: dict) -> str:
    """Replace {key} tokens with values from data dict."""
    def replacer(m):
        key = m.group(1).strip()
        return str(data.get(key, m.group(0)))
    return re.sub(r"\{([^}]+)\}", replacer, text)


class LabelEngine:
    def render(self, elements: List[BaseElement], width_mm: float = 40,
               height_mm: float = 25, data_row: dict = None) -> Image.Image:
        """
        Renders all elements onto a white canvas of the given dimensions.
        data_row: optional dict of variables for interpolation.
        """
        w = mm_to_px(width_mm)
        h = mm_to_px(height_mm)

        img = Image.new("RGB", (w, h), "white")
        draw = ImageDraw.Draw(img)

        # Sort by z_index
        sorted_els = sorted(elements, key=lambda e: e.z_index)

        for el in sorted_els:
            try:
                if el.type == ELEMENT_RECT:
                    _render_rect(draw, el)
                elif el.type == ELEMENT_TEXT:
                    _render_text(draw, el, data_row)
                elif el.type == ELEMENT_BARCODE:
                    _render_barcode(img, el, data_row)
                    draw = ImageDraw.Draw(img)  # re-acquire after paste
                elif el.type == ELEMENT_IMAGE:
                    _render_image(img, el)
                    draw = ImageDraw.Draw(img)
            except Exception as e:
                print(f"Render error on element {el.type}: {e}")

        return img
