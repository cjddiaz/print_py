"""
core/elements.py
Defines the data model for all label elements (layers).
Each element is fully serializable to/from a dict for .agisproj persistence.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


ELEMENT_TEXT     = "text"
ELEMENT_BARCODE  = "barcode"
ELEMENT_IMAGE    = "image"
ELEMENT_RECT     = "rect"

BARCODE_TYPES = ["code128", "qr", "ean13", "ean8", "upca", "code39"]


@dataclass
class BaseElement:
    type: str
    x: float = 10.0
    y: float = 10.0
    width: float = 50.0
    height: float = 10.0
    z_index: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        raise NotImplementedError


@dataclass
class TextElement(BaseElement):
    type: str = field(default=ELEMENT_TEXT, init=False)
    text: str = "Texto"
    font_family: str = "Arial"
    font_size: int = 14
    bold: bool = False
    italic: bool = False
    color: str = "#000000"
    align: str = "left"   # left | center | right

    @classmethod
    def from_dict(cls, d: dict):
        d.pop("type", None)
        return cls(**d)


@dataclass
class BarcodeElement(BaseElement):
    type: str = field(default=ELEMENT_BARCODE, init=False)
    code: str = "0000000000000"
    barcode_type: str = "code128"    # code128 | qr | ean13 | ean8 | upca | code39
    show_text: bool = True
    height: float = 20.0

    @classmethod
    def from_dict(cls, d: dict):
        d.pop("type", None)
        return cls(**d)


@dataclass
class ImageElement(BaseElement):
    type: str = field(default=ELEMENT_IMAGE, init=False)
    path: str = ""
    keep_aspect: bool = True

    @classmethod
    def from_dict(cls, d: dict):
        d.pop("type", None)
        return cls(**d)


@dataclass
class RectElement(BaseElement):
    type: str = field(default=ELEMENT_RECT, init=False)
    border_color: str = "#000000"
    fill_color: str = "#ffffff"
    border_width: float = 1.0
    filled: bool = False

    @classmethod
    def from_dict(cls, d: dict):
        d.pop("type", None)
        return cls(**d)


def element_from_dict(d: dict) -> BaseElement:
    t = d.get("type")
    if t == ELEMENT_TEXT:
        return TextElement.from_dict(dict(d))
    elif t == ELEMENT_BARCODE:
        return BarcodeElement.from_dict(dict(d))
    elif t == ELEMENT_IMAGE:
        return ImageElement.from_dict(dict(d))
    elif t == ELEMENT_RECT:
        return RectElement.from_dict(dict(d))
    raise ValueError(f"Unknown element type: {t}")
