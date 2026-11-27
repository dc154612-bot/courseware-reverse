"""3D 生成工具的自检：python3 -m unittest discover tests"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_assembler  # noqa: E402
from inline_three import inline, load_lib  # noqa: E402

NEED = ["SCENE", "buildSubject", "fresh", "render", "ACTIONS"]


class Test3D(unittest.TestCase):
    def test_inline_replaces_cdn_tag(self):
        html = (ROOT / "assets" / "3d-template.html").read_text(encoding="utf-8")
        out, n = inline(html, load_lib())
        self.assertEqual(n, 1)
        self.assertNotIn("cdn.jsdelivr.net", out)
        self.assertNotIn("deprecated with r150", out)
        self.assertIn('REVISION', out)

    def test_template_has_one_content_block(self):
        head, example, tail = build_assembler.split_template()
        self.assertIn(build_assembler.START, head)
        self.assertIn(build_assembler.END, tail)
        self.assertIn("start();", tail)
        for name in NEED:
            self.assertRegex(example, rf"\b{name}\b")

    def test_sample_reply_meets_contract(self):
        text = (ROOT / "tests" / "sample-reply-circuit.md").read_text(encoding="utf-8")
        code = re.search(r"```javascript\n([\s\S]*?)```", text).group(1)
        for name in NEED:
            self.assertRegex(code, rf"\b{name}\b")
        self.assertNotIn("<script", code)

    @unittest.skipUnless(shutil.which("node"), "需要 node 做语法检查")
    def test_assembled_scripts_parse(self):
        head, example, tail = build_assembler.split_template()
        html = head + example + tail
        for i, code in enumerate(re.findall(r"<script>([\s\S]*?)</script>", html)):
            with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as f:
                f.write(code)
                f.flush()
                r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"第 {i + 1} 段脚本：{r.stderr[:300]}")


if __name__ == "__main__":
    unittest.main()
