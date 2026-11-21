"""脚本自检：python3 -m unittest discover tests（不需要浏览器和第三方库）。"""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract_slides import parse_pptx  # noqa: E402

A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


def slide(texts, extra=""):
    paras = "".join(f"<a:p><a:r><a:t>{t}</a:t></a:r></a:p>" for t in texts)
    return f'<p:sld {A}><p:cSld><p:spTree><p:sp><p:txBody>{paras}</p:txBody></p:sp></p:spTree></p:cSld>{extra}</p:sld>'


TRIGGER = ('<p:timing><p:tnLst><p:par><p:cTn><p:stCondLst><p:cond evt="onClick" delay="0"><p:tgtEl><p:spTgt spid="4"/>'
           '</p:tgtEl></p:cond></p:stCondLst><p:childTnLst><p:par><p:cTn presetClass="entr"/></p:par></p:childTnLst>'
           '</p:cTn></p:par></p:tnLst></p:timing>')
JUMP = '<a:hlinkClick r:id="" action="ppaction://hlinksldjump"/>'


class PptxTest(unittest.TestCase):
    def test_text_notes_media_and_interaction(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "t.pptx"
            with zipfile.ZipFile(f, "w") as z:
                z.writestr("ppt/slides/slide1.xml", slide(["哪个数大？", "0.5 和 0.25"], TRIGGER + JUMP))
                z.writestr("ppt/slides/slide2.xml", slide(["第二页"]))
                z.writestr("ppt/slides/slide10.xml", slide(["第十页"]))
                z.writestr("ppt/slides/_rels/slide1.xml.rels",
                           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                           f'<Relationship Id="rId1" Type="{REL}notesSlide" Target="../notesSlides/notesSlide1.xml"/>'
                           f'<Relationship Id="rId2" Type="{REL}image" Target="../media/image1.png"/>'
                           f'<Relationship Id="rId3" Type="{REL}hyperlink" Target="https://example.com" TargetMode="External"/>'
                           '</Relationships>')
                z.writestr("ppt/notesSlides/notesSlide1.xml", slide(["先让学生猜"]))
                z.writestr("ppt/media/image1.png", b"png")
            s = parse_pptx(f)
        self.assertEqual([x["text"][0] for x in s], ["哪个数大？", "第二页", "第十页"])  # 按页码数字排序
        self.assertEqual(s[0]["notes"], ["先让学生猜"])
        self.assertEqual(s[0]["media"], ["ppt/media/image1.png"])
        self.assertEqual((s[0]["triggers"], s[0]["jumps"], s[0]["links"], s[0]["anim"]), (1, 1, 1, 1))
        self.assertEqual((s[1]["triggers"], s[1]["media"], s[1]["notes"]), (0, [], []))


class WebTest(unittest.TestCase):
    def test_same_site(self):
        try:
            from capture_web import same_site
        except ImportError:
            self.skipTest("capture_web 无法导入")
        root = urlparse("https://a.com/lab")
        self.assertTrue(same_site("https://a.com/lab/2", root))
        self.assertFalse(same_site("https://b.com/lab", root))
        self.assertFalse(same_site("https://a.com/file.pdf", root))


if __name__ == "__main__":
    unittest.main()
