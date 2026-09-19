#!/usr/bin/env python3
"""兼容入口：转发到 jewelry-auto-listing Skill 的实现。"""

from __future__ import annotations

import runpy
from pathlib import Path


TARGET = Path(__file__).resolve().parent / "skills" / "jewelry-auto-listing" / "scripts" / "auto_listing.py"


if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
