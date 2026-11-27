#!/usr/bin/env python3
"""把 three.js 内嵌进 HTML，生成断网也能打开的单文件。

用法：python3 inline_three.py <输入.html> [输出.html]
不写输出时，生成 <输入名>-离线版.html。

会替换以下任意一种写法：
  <script src="...three...min.js"></script>   （CDN 或本地文件）
  <script>/*THREE_INLINE*/</script>
"""
import re
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "assets" / "three-r160.min.js"
TAG = re.compile(r'<script[^>]*\bsrc="[^"]*three(?:@[\d.]+)?/build/three(?:\.min)?\.js"[^>]*>\s*</script>|<script[^>]*\bsrc="[^"]*three[^"/]*\.min\.js"[^>]*>\s*</script>', re.I)
PLACEHOLDER = "<script>/*THREE_INLINE*/</script>"


def load_lib():
    lib = LIB.read_text(encoding="utf-8")
    # 去掉 r150+ UMD 版本的弃用提示
    lib = re.sub(r"^console\.warn\([^;]*?deprecated[^;]*?\),", "void 0,", lib, count=1)
    assert "</script" not in lib.lower()
    return lib


def inline(html, lib):
    block = "<script>" + lib + "</script>"
    if PLACEHOLDER in html:
        return html.replace(PLACEHOLDER, block, 1), 1
    out, n = TAG.subn(lambda m: block, html, count=1)
    return out, n


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.stem + "-离线版.html")
    html = src.read_text(encoding="utf-8")
    if "import " in html and 'type="module"' in html and "three/addons" in html:
        print("这个文件用的是 ES 模块写法（three/addons），本脚本只支持 three.min.js 的全局变量写法。")
        return 1
    out, n = inline(html, load_lib())
    if not n:
        print("没找到 three.js 的 <script src> 标签，也没有 /*THREE_INLINE*/ 占位，文件未改动。")
        return 1
    dst.write_text(out, encoding="utf-8")
    print(f"已生成 {dst}（{len(out.encode()) // 1024} KB），断网也能打开。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
