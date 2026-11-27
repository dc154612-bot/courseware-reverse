#!/usr/bin/env python3
"""由 3d-template.html 生成 3d-拼装器.html（老师离线使用的拼装网页），并把示例代码同步进 3d-提示词.md。

用法：python3 build_assembler.py
改了骨架模板或 three.js 版本后重新运行一次。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inline_three import inline, load_lib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
START = "/* ===== 学科内容开始 ===== */"
END = "/* ===== 学科内容结束 ===== */"


def split_template():
    html = (ROOT / "assets" / "3d-template.html").read_text(encoding="utf-8")
    html, n = inline(html, load_lib())
    assert n == 1, "模板里没找到 three.js 的 script 标签"
    a, b = html.index(START), html.index(END)
    return html[: a + len(START)] + "\n", html[a + len(START):b].strip("\n"), "\n" + html[b:]


PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>3D 课件拼装器</title>
<style>
:root{--ink:#1d2a33;--soft:#56646e;--main:#1f5a7a;--bad:#a63c2e;--ok:#2f7a3a}
*{box-sizing:border-box}
body{margin:0;font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;color:var(--ink);background:linear-gradient(180deg,#bcd7ea,#eee6d3);min-height:100vh;line-height:1.65}
main{max-width:60rem;margin:0 auto;padding:2rem 1.2rem 3rem}
h1{font-family:"Songti SC","STSong","SimSun",serif;font-size:2.2rem;margin:0 0 .3rem}
ol{padding-left:1.3rem;margin:.4rem 0 1rem}
textarea{width:100%;min-height:22rem;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;border:1.5px solid rgba(29,42,51,.25);border-radius:12px;padding:.8rem;background:rgba(255,255,255,.9)}
.row{display:flex;gap:.6rem;flex-wrap:wrap;margin:.8rem 0}
button{font:inherit;font-size:1rem;padding:.55rem 1.2rem;min-height:44px;border-radius:999px;border:1.5px solid rgba(29,42,51,.25);background:#fff;cursor:pointer}
button.primary{background:var(--main);border-color:var(--main);color:#fff}
button:disabled{opacity:.45;cursor:not-allowed}
#out{padding:.7rem 1rem;border-radius:12px;background:rgba(255,255,255,.8);border-left:4px solid var(--main)}
#out.bad{border-color:var(--bad)}#out.ok{border-color:var(--ok)}
#out:empty{display:none}
iframe{width:100%;height:42rem;border:0;border-radius:14px;box-shadow:0 20px 60px rgba(20,30,40,.25);margin-top:1rem;background:#fff}
.hint{color:var(--soft);font-size:.92rem}
</style>
</head>
<body>
<main>
<h1>3D 课件拼装器</h1>
<p class="hint">不联网也能用。画面质量（光影、镜头、标注、面板）由这里的骨架负责，AI 只需要写“学科内容”那一段。</p>
<ol>
  <li>把 <b>3d-提示词.md</b> 发给 AI，让它写出学科内容代码。</li>
  <li>把 AI 回复里的代码整段粘贴到下面（带不带 ``` 都可以）。</li>
  <li>点“生成并预览”。没问题就点“下载课件”，得到一个断网也能打开的 HTML 文件。</li>
</ol>
<textarea id="code" spellcheck="false" placeholder="在这里粘贴 AI 写的学科内容代码……"></textarea>
<div class="row">
  <button class="primary" id="buildBtn">生成并预览</button>
  <button id="dlBtn" disabled>下载课件</button>
  <button id="exBtn">载入示例（水循环）</button>
</div>
<div id="out"></div>
<iframe id="pv" title="课件预览" hidden></iframe>
</main>
<script type="application/json" id="parts">__PARTS__</script>
<script>
const P = JSON.parse(document.getElementById('parts').textContent), $ = id => document.getElementById(id);
const NEED = [['SCENE', /\b(const|let|var)\s+SCENE\s*=/], ['buildSubject', /function\s+buildSubject\s*\(/], ['fresh', /function\s+fresh\s*\(/], ['render', /function\s+render\s*\(/], ['ACTIONS', /\b(const|let|var)\s+ACTIONS\s*=/]];
let html = '', title = '课件';
function clean(t) {
  const s = t.indexOf('学科内容开始'), e = t.indexOf('学科内容结束');
  if (s >= 0 && e > s) t = t.slice(t.indexOf('\n', s) + 1, t.lastIndexOf('\n', e));
  const fence = [...t.matchAll(/```[a-zA-Z]*\n([\s\S]*?)```/g)].map(m => m[1]);
  if (fence.length) t = fence.sort((a, b) => b.length - a.length)[0];
  return t.replace(/<\/?script[^>]*>/gi, '').replace(/^\s*start\(\);?\s*$/m, '').trim();
}
function say(cls, h) { $('out').className = cls; $('out').innerHTML = h; }
$('exBtn').onclick = () => { $('code').value = P.example; say('', '已载入示例。点“生成并预览”看看效果。'); };
$('buildBtn').onclick = () => {
  const code = clean($('code').value);
  if (!code) return say('bad', '还没有粘贴代码。');
  const miss = NEED.filter(([, re]) => !re.test(code)).map(([n]) => n);
  if (miss.length) return say('bad', `代码缺少：<b>${miss.join('、')}</b>。可能是 AI 没写全，或者被截断了。请对 AI 说：“请按骨架约定完整输出学科内容代码，必须包含 ${miss.join('、')}。”`);
  try { new Function(code); } catch (e) {
    return say('bad', `代码有语法错误：<b>${e.message}</b>。常见原因是 AI 输出被截断。请对 AI 说：“代码不完整或有语法错误（${e.message}），请重新完整输出。”`);
  }
  title = (code.match(/title:\s*['"`]([^'"`]+)/) || [, '课件'])[1];
  html = P.head + code + P.tail;
  $('pv').hidden = false; $('pv').srcdoc = html; $('dlBtn').disabled = false;
  say('ok', '已生成。先在下面预览：点“开始”，把每道题都做一遍，拖动场景看看。页面顶部如果出现红色提示条，把那句话发给 AI 修改。');
};
$('dlBtn').onclick = () => {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([html], { type: 'text/html' }));
  a.download = title + '.html'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
};
</script>
</body>
</html>
"""


def main():
    head, example, tail = split_template()
    parts = json.dumps({"head": head, "example": example, "tail": tail}, ensure_ascii=False).replace("</", "<\\/")
    out = PAGE.replace("__PARTS__", parts)
    dst = ROOT / "assets" / "3d-拼装器.html"
    dst.write_text(out, encoding="utf-8")
    print(f"已生成 {dst.name}（{len(out.encode()) // 1024} KB）")
    pm = ROOT / "assets" / "3d-提示词.md"
    text = pm.read_text(encoding="utf-8")
    a, b = "<!-- 示例开始 -->", "<!-- 示例结束 -->"
    i, j = text.index(a) + len(a), text.index(b)
    pm.write_text(text[:i] + "\n```javascript\n" + example + "\n```\n" + text[j:], encoding="utf-8")
    print(f"已把示例同步进 {pm.name}")


if __name__ == "__main__":
    main()
