"""
core/serializer.py
Save and load label projects as .agisproj (JSON) files.
A project contains: label dimensions, elements list, counter config, and printer settings.
"""
import json
import os
from typing import List, Optional
from core.elements import BaseElement, element_from_dict
from core.counters import SerialCounter


APP_VERSION = "2.0"


def save_project(path: str, elements: List[BaseElement], config: dict,
                 counter: Optional[SerialCounter] = None):
    """
    Serialize the current project to a .agisproj file.
    config: dict with at least 'width_mm', 'height_mm', 'printer_name'.
    """
    data = {
        "version": APP_VERSION,
        "config": config,
        "elements": [el.to_dict() for el in elements],
        "counter": counter.to_dict() if counter else None,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_project(path: str) -> dict:
    """
    Load a .agisproj file. Returns a dict with keys:
    'config', 'elements' (list of BaseElement), 'counter' (SerialCounter or None).
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = [element_from_dict(d) for d in data.get("elements", [])]
    counter_data = data.get("counter")
    counter = SerialCounter.from_dict(counter_data) if counter_data else None

    return {
        "version": data.get("version", "unknown"),
        "config": data.get("config", {}),
        "elements": elements,
        "counter": counter,
    }
