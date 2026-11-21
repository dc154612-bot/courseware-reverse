#!/usr/bin/env python3
"""采集网页课件：每页截图、文字、可操作控件和技术线索，供拆解设计使用。

用法：
  python3 capture_web.py https://example.com/lesson            # 默认最多走 5 个同站页面
  python3 capture_web.py https://example.com/h5 --mobile       # 手机尺寸，适合 H5 课件
  python3 capture_web.py 本地课件.html --max-pages 1

需要 Playwright：pip install playwright
电脑装了 Chrome 就能直接用；没有时再运行 playwright install chromium。

只采集公开页面：遵守 robots.txt，不登录、不填表、不点按钮。
单页应用里要点击才出现的内容，报告会列出控件，由使用者或 AI 在浏览器里接着操作。
"""
import argparse
import json
import sys
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urldefrag, urlparse

PROBE = r"""() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 };
  const label = e => (e.innerText || e.value || e.getAttribute('aria-label') || e.title || e.placeholder || '')
      .trim().replace(/\s+/g, ' ').slice(0, 40);
  const uniq = a => [...new Set(a)];
  const body = document.body ? document.body.innerText : '';
  const canv = [...document.querySelectorAll('canvas')].filter(vis);
  const meta = n => (document.querySelector(`meta[name="${n}"]`) || {}).content || '';
  const LIBS = {THREE: 'Three.js', PIXI: 'PixiJS', Phaser: 'Phaser', BABYLON: 'Babylon.js', createjs: 'CreateJS',
                p5: 'p5.js', d3: 'D3', echarts: 'ECharts', Vue: 'Vue', __VUE__: 'Vue', React: 'React',
                GeoGebra: 'GeoGebra', ggbApplet: 'GeoGebra', MathJax: 'MathJax', katex: 'KaTeX', Howl: 'Howler'};
  return {
    title: document.title,
    headings: [...document.querySelectorAll('h1,h2,h3')].filter(vis).map(e => e.tagName + ' ' + label(e)).slice(0, 40),
    controls: uniq([...document.querySelectorAll('button,[role=button],[role=tab],input,select,textarea,[onclick]')]
      .filter(vis).map(e => e.tagName.toLowerCase() + (e.type && e.tagName !== 'BUTTON' ? ':' + e.type : '') + ' ' + label(e))).slice(0, 80),
    links: [...document.querySelectorAll('a[href]')].map(a => a.href),
    canvas: canv.map(c => c.width + 'x' + c.height),
    // 已有 2D 画布再要 webgl 会返回 null，不会改动页面
    webgl: canv.some(c => { try { return !!(c.getContext('webgl2') || c.getContext('webgl')) } catch (e) { return false } }),
    media: {audio: document.querySelectorAll('audio').length, video: document.querySelectorAll('video').length,
            iframe: document.querySelectorAll('iframe').length, svg: document.querySelectorAll('svg').length},
    libs: uniq(Object.keys(LIBS).filter(k => k in window).map(k => LIBS[k])),
    scripts: [...document.scripts].map(s => s.src).filter(Boolean).slice(0, 20),
    meta: {author: meta('author'), copyright: meta('copyright'), description: meta('description'), generator: meta('generator')},
    login: !!document.querySelector('input[type=password]'),
    zeroWidth: /[​-‍⁠﻿]/.test(body),
    text: body
  };
}"""

SKIP_EXT = (".pdf", ".zip", ".rar", ".7z", ".exe", ".dmg", ".apk", ".jpg", ".jpeg", ".png", ".gif",
            ".mp3", ".mp4", ".mov", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx")


def same_site(url, root):
    u = urlparse(url)
    return u.scheme == root.scheme and u.netloc == root.netloc and not u.path.lower().endswith(SKIP_EXT)


def robots_for(ctx, url):
    """用浏览器读 robots.txt；部分网站会拦截 Python 自带的请求。读不到（4xx 等）时按无限制处理。"""
    u = urlparse(url)
    if u.scheme not in ("http", "https"):
        return None
    try:
        r = ctx.request.get(f"{u.scheme}://{u.netloc}/robots.txt", timeout=15000)
    except Exception:
        return None
    if r.status != 200:
        return None
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(r.text().splitlines())
    return rp


def launch(p):
    for kw in ({"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception:
            continue
    sys.exit("打不开浏览器。请安装 Chrome，或运行：playwright install chromium")


def capture(start, out, max_pages, mobile):
    from playwright.sync_api import sync_playwright
    root = urlparse(start)
    queue, seen, pages, skipped = [start], {start}, [], []
    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(**(p.devices["iPhone 13"] if mobile else {"viewport": {"width": 1366, "height": 800}}))
        page = ctx.new_page()
        rp = robots_for(ctx, start)
        while queue and len(pages) < max_pages:
            url = queue.pop(0)
            if rp and not rp.can_fetch("*", url):
                skipped.append(f"{url}（robots.txt 不允许）")
                continue
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                try:
                    page.goto(url, wait_until="load", timeout=30000)
                except Exception as e:
                    skipped.append(f"{url}（打不开：{str(e).splitlines()[0][:80]}）")
                    continue
            page.wait_for_timeout(1500)  # 等开场动画和 3D 场景画出来
            n = len(pages) + 1
            page.screenshot(path=str(out / f"p{n:02d}_first.png"))
            page.screenshot(path=str(out / f"p{n:02d}_full.png"), full_page=True)
            info = page.evaluate(PROBE)
            (out / f"p{n:02d}.txt").write_text(info.pop("text"), encoding="utf-8")
            links = info.pop("links")
            info["url"] = page.url
            pages.append(info)
            if not info["login"]:
                for link in links:
                    link = urldefrag(link)[0]
                    if link not in seen and same_site(link, root):
                        seen.add(link)
                        queue.append(link)
            time.sleep(1)  # 对网站礼貌一些
        browser.close()
    return pages, skipped, len(queue)


def report(pages, skipped, left, out, start, mobile):
    L = [f"# 网页采集报告", "", f"- 起始地址：{start}", f"- 视角：{'手机' if mobile else '电脑'}",
         f"- 采集页面：{len(pages)} 个" + (f"，还有 {left} 个同站链接未采集（可调大 --max-pages）" if left else "")]
    flags = []
    if any(p["zeroWidth"] for p in pages):
        flags.append("页面文字里有零宽字符，可能是作者的隐形水印：说明作者在保护作品，只学设计，不要复制文字和代码。")
    if any(p["meta"]["copyright"] or p["meta"]["author"] for p in pages):
        flags.append("页面声明了作者或版权，见各页“署名”。")
    if any(p["login"] for p in pages):
        flags.append("有页面需要登录，登录后的内容不采集。")
    if flags:
        L += ["", "## 注意"] + [f"- {f}" for f in flags]
    for i, p in enumerate(pages, 1):
        sig = []
        if p["webgl"]:
            sig.append("WebGL（3D 或高性能 2D）")
        elif p["canvas"]:
            sig.append("Canvas 画布 " + "、".join(p["canvas"]))
        if p["libs"]:
            sig.append("可识别的库：" + "、".join(p["libs"]))
        sig += [f"{k} ×{v}" for k, v in p["media"].items() if v]
        m = p["meta"]
        L += ["", f"## 第 {i} 页：{p['title'] or '（无标题）'}", "",
              f"- 地址：{p['url']}",
              f"- 截图：p{i:02d}_first.png（首屏），p{i:02d}_full.png（整页）；文字：p{i:02d}.txt",
              f"- 技术线索：{'；'.join(sig) or '普通网页'}"]
        if m["author"] or m["copyright"]:
            L.append(f"- 署名：{m['author']} {m['copyright']}".rstrip())
        if p["headings"]:
            L += ["- 标题结构："] + [f"  - {h}" for h in p["headings"]]
        if p["controls"]:
            L += ["- 可操作控件（需要在浏览器里逐个试）："] + [f"  - {c}" for c in p["controls"]]
    if skipped:
        L += ["", "## 未采集"] + [f"- {s}" for s in skipped]
    L += ["", "提示：报告只记录打开页面时看到的内容。点击、拖动后才出现的效果，请在浏览器里按“可操作控件”逐个操作并记录。"]
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="网页课件采集")
    ap.add_argument("url", help="网址，或本地 .html 文件路径")
    ap.add_argument("--max-pages", type=int, default=5)
    ap.add_argument("--mobile", action="store_true", help="用手机尺寸打开（H5 课件）")
    ap.add_argument("--out", default="web_capture")
    a = ap.parse_args()
    url = a.url
    if not urlparse(url).scheme:
        f = Path(url).expanduser().resolve()
        if not f.is_file():
            sys.exit(f"找不到文件：{f}")
        url = f.as_uri()
    if urlparse(url).scheme not in ("http", "https", "file") or a.max_pages < 1:
        sys.exit("只支持 http/https 网址或本地 html 文件，--max-pages 至少为 1")
    try:
        import playwright  # noqa: F401
    except ImportError:
        sys.exit("需要先安装 Playwright：pip install playwright")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pages, skipped, left = capture(url, out, a.max_pages, a.mobile)
    if not pages:
        sys.exit("一个页面也没采集到：" + "；".join(skipped))
    report(pages, skipped, left, out, url, a.mobile)
    print(f"采集了 {len(pages)} 个页面 → {out / 'report.md'}")


if __name__ == "__main__":
    main()
