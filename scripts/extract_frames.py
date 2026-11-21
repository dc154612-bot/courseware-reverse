#!/usr/bin/env python3
"""从课件录屏中抽帧，并拼成总览图，方便逐段拆解。

用法：
  python3 extract_frames.py 录屏.mp4                 # 每 3 秒一帧
  python3 extract_frames.py 录屏.mp4 --every 0.5 --start 10 --end 20
  python3 extract_frames.py 录屏.mp4 --crop 0.27,0.43  # 只保留画面 27%~43% 高度（手机录屏里课件那一条）

依次尝试：ffmpeg 命令 → Python 包 imageio-ffmpeg → macOS 自带的 AVFoundation（需要 swift）。
拼总览图需要 Pillow；没有时只输出单帧。
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SWIFT = r'''
import AVFoundation
import AppKit
let a = CommandLine.arguments
let asset = AVURLAsset(url: URL(fileURLWithPath: a[1]))
let out = a[2], every = Double(a[3])!, start = Double(a[4])!, endArg = Double(a[5])!
let top = Double(a[6])!, bottom = Double(a[7])!, maxH = Double(a[8])!
let dur = CMTimeGetSeconds(asset.duration)
print("DURATION", dur)
let g = AVAssetImageGenerator(asset: asset)
g.appliesPreferredTrackTransform = true
g.requestedTimeToleranceBefore = .zero; g.requestedTimeToleranceAfter = .zero
let end = endArg > 0 ? min(endArg, dur) : dur
var t = start, i = 0
while t < end {
  if var cg = try? g.copyCGImage(at: CMTime(seconds: t, preferredTimescale: 600), actualTime: nil) {
    if top > 0 || bottom < 1 {
      let h = Double(cg.height)
      cg = cg.cropping(to: CGRect(x: 0, y: Int(h * top), width: cg.width, height: Int(h * (bottom - top))))!
    }
    let rep = NSBitmapImageRep(cgImage: cg)
    let s = min(1.0, maxH / Double(cg.height))
    let size = NSSize(width: Double(cg.width) * s, height: Double(cg.height) * s)
    let img = NSImage(size: size); img.lockFocus()
    rep.draw(in: NSRect(origin: .zero, size: size)); img.unlockFocus()
    let r2 = NSBitmapImageRep(data: img.tiffRepresentation!)!
    let d = r2.representation(using: .jpeg, properties: [.compressionFactor: 0.7])!
    try! d.write(to: URL(fileURLWithPath: String(format: "%@/f%04d_%07.1fs.jpg", out, i, t)))
  }
  t += every; i += 1
}
'''


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def with_ffmpeg(ff, video, out, a):
    probe = subprocess.run([ff, "-i", str(video)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe.stderr)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0
    end = min(a.end, dur) if a.end > 0 and dur else (a.end or dur)
    vf = [f"select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,{a.every}-0.001)'"]
    if a.top > 0 or a.bottom < 1:
        vf.append(f"crop=iw:ih*{a.bottom - a.top}:0:ih*{a.top}")
    vf.append(f"scale=-2:'min({a.max_height},ih)'")
    cmd = [ff, "-loglevel", "error", "-i", str(video), "-ss", str(a.start)]
    if end:
        cmd += ["-to", str(end)]
    cmd += [ "-vf", ",".join(vf), "-fps_mode", "vfr", "-q:v", "4", str(out / "raw%04d.jpg")]
    subprocess.run(cmd, check=True)
    # 按时间重命名，便于对照
    for k, f in enumerate(sorted(out.glob("raw*.jpg"))):
        f.rename(out / f"f{k:04d}_{a.start + k * a.every:07.1f}s.jpg")
    return dur


def with_swift(video, out, a):
    if sys.platform != "darwin" or not shutil.which("swift"):
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False) as t:
        t.write(SWIFT)
    r = subprocess.run(["swift", t.name, str(video), str(out), str(a.every), str(a.start),
                        str(a.end), str(a.top), str(a.bottom), str(a.max_height)],
                       capture_output=True, text=True)
    Path(t.name).unlink(missing_ok=True)
    m = re.search(r"DURATION ([\d.]+)", r.stdout)
    if r.returncode != 0 and not m:
        print(r.stderr[-800:], file=sys.stderr)
        return None
    return float(m[1]) if m else 0


def contact_sheets(out, per=12):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("未安装 Pillow，跳过总览图（pip install pillow 后可生成）")
        return []
    frames = sorted(out.glob("f*.jpg"))
    sheets = []
    for k in range(0, len(frames), per):
        group = frames[k:k + per]
        ims = [Image.open(f) for f in group]
        wide = ims[0].width / ims[0].height > 1.3   # 横屏或裁剪后的宽条：每行少放几张、放大
        cols, w = (3, 600) if wide else (6, 300)
        h = max(int(im.height * w / im.width) for im in ims)
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (w * cols, h * rows), "white")
        d = ImageDraw.Draw(sheet)
        for i, (im, f) in enumerate(zip(ims, group)):
            x, y = (i % cols) * w, (i // cols) * h
            sheet.paste(im.resize((w, int(im.height * w / im.width))), (x, y))
            label = f.stem.split("_")[-1]
            d.rectangle([x, y, x + 70, y + 18], fill="black")
            d.text((x + 4, y + 3), label, fill="yellow")
        p = out / f"sheet_{k // per + 1:02d}.jpg"
        sheet.save(p, quality=75)
        sheets.append(p)
    return sheets


def main():
    ap = argparse.ArgumentParser(description="课件录屏抽帧")
    ap.add_argument("video")
    ap.add_argument("--every", type=float, default=3.0, help="每隔几秒抽一帧，默认 3")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=0.0, help="0 表示到结尾")
    ap.add_argument("--crop", default="", help="保留的高度范围，如 0.27,0.43")
    ap.add_argument("--max-height", type=int, default=900)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    a.top, a.bottom = (map(float, a.crop.split(","))) if a.crop else (0.0, 1.0)
    if not (0 <= a.top < a.bottom <= 1) or a.every <= 0:
        sys.exit("参数不对：--crop 需要 0≤上<下≤1，--every 需要大于 0")

    video = Path(a.video).expanduser().resolve()
    if not video.is_file():
        sys.exit(f"找不到视频：{video}")
    out = Path(a.out) if a.out else video.with_name(video.stem + "_frames")
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("f*.jpg")) + list(out.glob("sheet_*.jpg")) + list(out.glob("raw*.jpg")):
        old.unlink()

    ff = find_ffmpeg()
    dur = with_ffmpeg(ff, video, out, a) if ff else with_swift(video, out, a)
    if dur is None:
        sys.exit("没有可用的抽帧工具。请安装 ffmpeg，或运行 pip install imageio-ffmpeg 后重试；"
                 "也可以请老师手动截图。")
    n = len(list(out.glob("f*.jpg")))
    if n == 0:
        sys.exit("没有抽到画面，请检查视频格式或 --start/--end 是否超出时长。")
    sheets = contact_sheets(out)
    print(f"视频时长约 {dur:.0f} 秒，抽出 {n} 帧 → {out}")
    for s in sheets:
        print("总览图：", s)


if __name__ == "__main__":
    main()
