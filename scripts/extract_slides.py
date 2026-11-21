#!/usr/bin/env python3
"""从 PPT / PDF 课件中提取每页的文字、备注、媒体和交互线索，供拆解设计使用。

用法：
  python3 extract_slides.py 课件.pptx      # 只用 Python 自带库；附带的图片、音视频复制到 media/
  python3 extract_slides.py 课件.pdf       # 需要 pip install pymupdf；导出每页图片并拼总览图

.ppt / .key / 希沃白板 .enbx 等格式：先在原软件里“另存为”PDF 或 PPTX 再处理。
PPTX 不渲染画面；想看版面时，另存一份 PDF 一起处理。
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/package/2006/relationships"}
MEDIA_TYPES = ("/image", "/audio", "/video", "/media")


def paragraphs(xml):
    root = ET.fromstring(xml)
    out = []
    for para in root.iter(f"{{{NS['a']}}}p"):
        t = "".join(x.text or "" for x in para.iter(f"{{{NS['a']}}}t")).strip()
        if t:
            out.append(t)
    return out


def rels(z, part):
    """读取某个部件的关系表：{rId: (类型, 包内路径)}。"""
    p = PurePosixPath(part)
    rp = str(p.parent / "_rels" / (p.name + ".rels"))
    if rp not in z.namelist():
        return {}
    out = {}
    for r in ET.fromstring(z.read(rp)):
        target = r.get("Target", "")
        if r.get("TargetMode") != "External":
            parts = []
            for seg in (p.parent / target).parts:  # 规整 "../media/x.png"
                if seg == "..":
                    parts.pop()
                else:
                    parts.append(seg)
            target = "/".join(parts)
        out[r.get("Id")] = (r.get("Type", ""), target)
    return out


def parse_pptx(path):
    with zipfile.ZipFile(path) as z:
        found = [(re.fullmatch(r"ppt/slides/slide(\d+)\.xml", n), n) for n in z.namelist()]
        order = [n for _, n in sorted((int(m[1]), n) for m, n in found if m)]  # 按页码数字排，slide10 在 slide2 之后
        slides = []
        for i, part in enumerate(order, 1):
            xml = z.read(part).decode("utf-8")
            rs = rels(z, part)
            notes = next((paragraphs(z.read(t)) for ty, t in rs.values() if ty.endswith("/notesSlide") and t in z.namelist()), [])
            media = [t for ty, t in rs.values() if ty.endswith(MEDIA_TYPES) and t in z.namelist()]
            slides.append({
                "n": i, "text": paragraphs(xml), "notes": notes, "media": media,
                "anim": xml.count("presetClass="),
                # 触发器：点击某个形状才播放动画，是老师做互动 PPT 最常用的手法
                "triggers": len(re.findall(r'evt="onClick"[^>]*>\s*<p:tgtEl>', xml)),
                "jumps": xml.count("ppaction://hlinksldjump") + xml.count("ppaction://hlinkshowjump"),
                "links": len([1 for ty, t in rs.values() if ty.endswith("/hyperlink")]),
            })
        return slides


def write_pptx(path, out):
    slides = parse_pptx(path)
    mdir = out / "media"
    with zipfile.ZipFile(path) as z:
        for s in slides:
            for t in s["media"]:
                mdir.mkdir(exist_ok=True)
                (mdir / f"slide{s['n']:02d}_{PurePosixPath(t).name}").write_bytes(z.read(t))
    total = lambda k: sum(s[k] for s in slides)
    L = ["# PPT 提取报告", "", f"- 文件：{Path(path).name}", f"- 共 {len(slides)} 页",
         f"- 交互线索：动画 {total('anim')} 处，触发器 {total('triggers')} 个，页内跳转 {total('jumps')} 个，外部链接 {total('links')} 个"]
    if total("triggers") or total("jumps"):
        L.append("- 有触发器或跳转：这份 PPT 不是线性翻页，拆解时重点看“点哪里、跳到哪”的结构")
    for s in slides:
        clues = [f"{k} {s[v]}" for k, v in (("动画", "anim"), ("触发器", "triggers"), ("跳转", "jumps"), ("链接", "links")) if s[v]]
        L += ["", f"## 第 {s['n']} 页" + (f"（{'，'.join(clues)}）" if clues else "")]
        L += [f"- {t}" for t in s["text"]] or ["- （无文字）"]
        if s["notes"]:
            L += ["- 备注：" + " / ".join(s["notes"])]
        if s["media"]:
            L += ["- 媒体：" + "、".join(PurePosixPath(t).name for t in s["media"])]
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return len(slides)


def write_pdf(path, out):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("处理 PDF 需要先安装：pip install pymupdf")
    doc = fitz.open(path)
    L = ["# PDF 提取报告", "", f"- 文件：{Path(path).name}", f"- 共 {doc.page_count} 页"]
    for i, page in enumerate(doc, 1):
        zoom = min(2.0, 1200 / max(page.rect.width, 1))
        page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(str(out / f"f{i:04d}_p{i:03d}.jpg"))
        text = [t.strip() for t in page.get_text().splitlines() if t.strip()]
        links = len(page.get_links())
        L += ["", f"## 第 {i} 页" + (f"（链接 {links} 个）" if links else ""), f"- 图片：f{i:04d}_p{i:03d}.jpg"]
        L += [f"- {t}" for t in text[:60]] or ["- （无文字，可能是图片，请看页面图片）"]
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    sys.path.insert(0, str(Path(__file__).parent))
    from extract_frames import contact_sheets  # 复用抽帧脚本的拼图
    contact_sheets(out)
    return doc.page_count


def main():
    ap = argparse.ArgumentParser(description="PPT / PDF 课件提取")
    ap.add_argument("file")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    f = Path(a.file).expanduser().resolve()
    if not f.is_file():
        sys.exit(f"找不到文件：{f}")
    ext = f.suffix.lower()
    if ext not in (".pptx", ".pdf"):
        sys.exit("只支持 .pptx 和 .pdf。其他格式（.ppt、.key、希沃 .enbx）请先在原软件里另存为 PDF 或 PPTX。")
    out = Path(a.out) if a.out else f.with_name(f.stem + "_slides")
    out.mkdir(parents=True, exist_ok=True)
    try:
        n = write_pptx(f, out) if ext == ".pptx" else write_pdf(f, out)
    except (zipfile.BadZipFile, ET.ParseError):
        sys.exit("文件打不开，可能已损坏或加密。请在原软件里重新另存一份。")
    print(f"提取了 {n} 页 → {out / 'report.md'}")


if __name__ == "__main__":
    main()
