# เพิ่มงานใหม่ลงเว็บพอร์ต: เลือกไฟล์วิดีโอ → หาช่วงไฮไลท์อัตโนมัติ → ตัดคลิปสั้น/ภาพปก/ภาพนิ่ง → เขียนลง content.js → อัปขึ้น GitHub
# ใช้แค่ Python (มาตรฐาน) + ffmpeg/ffprobe ไม่ต้องลงอะไรเพิ่ม
import glob, json, os, re, shutil, statistics, subprocess, sys, tempfile, time
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "media")
CONTENT = os.path.join(ROOT, "content.js")
PREFIX = "window.CONTENT = "


def find_tool(name):
    p = shutil.which(name)
    if p:
        return p
    hits = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\*FFmpeg*\*\bin\\" + name + ".exe"))
    if hits:
        return hits[0]
    sys.exit(f"หา {name} ไม่เจอ — ติดตั้งด้วยคำสั่ง: winget install Gyan.FFmpeg")


FFMPEG, FFPROBE = find_tool("ffmpeg"), find_tool("ffprobe")


def run(args, **kw):
    return subprocess.run(args, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def ask(q, default=""):
    a = input(f"{q}{f' [{default}]' if default else ''}: ").strip()
    return a or default


def yes(q):
    return input(f"{q} (y/n): ").strip().lower().startswith("y")


def fmt_len(sec):
    sec = int(round(sec))
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_time(t):
    parts = [float(x) for x in t.strip().split(":")]
    v = 0.0
    for x in parts:
        v = v * 60 + x
    return v


def yt_id(link):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", link or "")
    return m.group(1) if m else (link if re.fullmatch(r"[\w-]{11}", link or "") else "")


def load_content():
    s = open(CONTENT, encoding="utf-8").read().strip()
    return json.loads(s[len(PREFIX):].rstrip(";"))


def save_content(c):
    with open(CONTENT, "w", encoding="utf-8", newline="\n") as f:
        f.write(PREFIX + json.dumps(c, ensure_ascii=False, indent=2) + ";\n")


def probe(path):
    out = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "json", path]).stdout
    j = json.loads(out)
    st = j["streams"][0]
    return float(j["format"]["duration"]), int(st["width"]), int(st["height"])


def pick_highlights(path, dur, n, win):
    """Same method used for the first version of the site: loud seconds + dense cuts score highest."""
    print("กำลังวิเคราะห์เสียงและจังหวะการตัด (คลิปยาวอาจใช้เวลาหลายนาที)...")
    with tempfile.TemporaryDirectory() as tmp:
        # filter file paths must be relative: a "C:" in the path breaks ffmpeg's filter parser
        run([FFMPEG, "-v", "error", "-i", path, "-vn", "-af",
             "aresample=8000,asetnsamples=n=8000:p=0,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=rms.txt",
             "-f", "null", "-"], cwd=tmp)
        run([FFMPEG, "-v", "error", "-skip_frame", "nokey", "-i", path, "-an", "-vf",
             "scale=160:-2,select='gt(scene,0.35)',metadata=print:file=scn.txt", "-f", "null", "-"], cwd=tmp)
        rms, t = {}, None
        for line in open(os.path.join(tmp, "rms.txt"), encoding="utf-8", errors="replace"):
            m = re.search(r"pts_time:([\d.]+)", line)
            if m:
                t = int(float(m.group(1)))
            m = re.search(r"RMS_level=(-?[\d.]+|-inf)", line)
            if m and t is not None:
                rms[t] = max(float(m.group(1)) if m.group(1) != "-inf" else -90, -60)
        cuts = [float(m.group(1)) for line in open(os.path.join(tmp, "scn.txt"), encoding="utf-8", errors="replace")
                for m in [re.search(r"pts_time:([\d.]+)", line)] if m]
    if not rms:
        return [dur * (i + 1) / (n + 1) for i in range(n)]
    mu, sd = statistics.mean(rms.values()), statistics.pstdev(rms.values()) or 1
    edge = min(20, dur * 0.05)
    cands = []
    for s in range(int(edge), int(dur - edge - win)):
        a = statistics.mean(rms.get(s + i, mu) for i in range(int(win)))
        c = sum(1 for x in cuts if s <= x < s + win)
        cands.append(((a - mu) / sd + 0.6 * min(c, 3), s))
    cands.sort(reverse=True)
    gap, pick = dur / (n + 2), []
    for _, s in cands:
        if all(abs(s - p) > gap for p in pick):
            pick.append(s)
        if len(pick) == n:
            break
    return sorted(pick)


def cut_clip(src, start, length, out, vertical=False):
    scale = "scale=-2:960" if vertical else "scale=960:-2"
    run([FFMPEG, "-v", "error", "-ss", str(start), "-t", str(length), "-i", src, "-vf", scale + ",fps=30",
         "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
         "-movflags", "+faststart", "-y", out])


def grab(src, t, out, vertical=False):
    scale = "scale=-2:1600" if vertical else "scale=1600:-2"
    run([FFMPEG, "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", scale, "-q:v", "4", "-y", out])


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def img_size(path):
    out = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", path]).stdout
    st = json.loads(out)["streams"][0]
    return int(st["width"]), int(st["height"])


def add_graphic_image(src, ext, slug, c):
    w, h = img_size(src)
    title = ask("ชื่อผลงานกราฟิก")
    out = os.path.join(MEDIA, slug + ext)
    if ext in (".gif", ".webp"):
        shutil.copyfile(src, out)          # animated files are copied as-is so the animation is kept
        if os.path.getsize(out) > 8_000_000:
            print("คำเตือน: ไฟล์ใหญ่กว่า 8 MB เว็บจะโหลดช้า — ถ้าทำได้ส่งออกเป็น MP4 แล้วเลือกข้อ 3 จะเล็กกว่ามาก")
    else:
        out = os.path.join(MEDIA, slug + ".jpg")
        run([FFMPEG, "-v", "error", "-i", src, "-vf", "scale='min(1800,iw)':-2", "-q:v", "3", "-y", out])
    c.setdefault("graphics", []).append({"title": title, "src": rel(out), "ratio": f"{w}/{h}"})
    save_content(c)
    print("เพิ่มลงหน้า กราฟิก & โมชั่น แล้ว")
    git_publish(f"Add graphic: {title}")


def add_motion(src, dur, w, h, slug, c):
    title = ask("ชื่อผลงานโมชั่น")
    start = parse_time(ask("เริ่มที่วินาที", "0"))
    length = min(15, dur - start)
    out, poster = os.path.join(MEDIA, slug + ".mp4"), os.path.join(MEDIA, slug + "-poster.jpg")
    print("กำลังแปลงไฟล์...")
    scale = "scale=-2:720" if h > w else "scale=960:-2"
    run([FFMPEG, "-v", "error", "-ss", str(start), "-t", str(length), "-i", src, "-an", "-vf", scale + ",fps=30",
         "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", out])
    grab(src, start + length / 2, poster, vertical=h > w)
    c.setdefault("graphics", []).append({"title": title, "src": rel(out), "poster": rel(poster), "ratio": f"{w}/{h}"})
    save_content(c)
    print("เพิ่มลงหน้า กราฟิก & โมชั่น แล้ว (เล่นวนแบบไม่มีเสียง สูงสุด 15 วินาที)")
    git_publish(f"Add motion: {title}")


def set_showreel(src, dur, c):
    out, poster = os.path.join(MEDIA, "showreel.mp4"), os.path.join(MEDIA, "showreel-poster.jpg")
    print("กำลังแปลง Showreel ให้เหมาะกับเว็บ...")
    run([FFMPEG, "-v", "error", "-i", src, "-vf", "scale=1280:-2", "-c:v", "libx264", "-preset", "slow", "-crf", "25",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-y", out])
    grab(src, min(1.2, dur / 2), poster)
    reel = c.get("showreel") or {}
    reel.update({"title": ask("ชื่อ Showreel", reel.get("title", "Showreel")), "src": rel(out), "poster": rel(poster), "length": fmt_len(dur)})
    c["showreel"] = reel
    save_content(c)
    print(f"เปลี่ยน Showreel แล้ว ({os.path.getsize(out) // 1_000_000} MB)")
    git_publish("Update showreel")


def choose_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
        p = filedialog.askopenfilename(title="เลือกไฟล์วิดีโอหรือรูปที่จะเพิ่มลงพอร์ต",
                                       filetypes=[("Video / Image", "*.mp4 *.mov *.mkv *.m4v *.webm *.jpg *.jpeg *.png *.gif *.webp"), ("All", "*.*")])
        r.destroy()
        return p
    except Exception:
        return ask("วางที่อยู่ไฟล์วิดีโอ (เช่น E:\\Footage\\clip.mp4)").strip('"')


def git_publish(msg):
    if not yes("\nอัปขึ้นเว็บเลยไหม"):
        print("ยังไม่อัป — ถ้าจะอัปทีหลัง ดับเบิลคลิก อัปเดตเว็บ.bat")
        return
    try:
        run(["git", "add", "-A"], cwd=ROOT)
        run(["git", "commit", "-m", msg], cwd=ROOT)
        run(["git", "push"], cwd=ROOT)
        print("อัปแล้ว เว็บจะเปลี่ยนภายใน 1–2 นาที")
    except subprocess.CalledProcessError as e:
        print("อัปไม่สำเร็จ:\n" + (e.stderr or e.stdout))


def main():
    os.makedirs(MEDIA, exist_ok=True)
    print("=== เพิ่มงานลงเว็บพอร์ต ===")
    src = choose_file()
    if not src or not os.path.exists(src):
        sys.exit("ไม่ได้เลือกไฟล์")
    ext = os.path.splitext(src)[1].lower()
    slug = "w" + time.strftime("%y%m%d%H%M%S")
    c = load_content()
    if ext in IMAGE_EXT:
        return add_graphic_image(src, ext, slug, c)
    dur, w, h = probe(src)
    vertical = h > w
    print(f"ไฟล์: {os.path.basename(src)} · ยาว {fmt_len(dur)} · {w}x{h}")
    print("จะใส่ในหน้าไหน?\n  1 = Long-form (งานยาว)\n  2 = Short-form (คลิปแนวตั้ง)\n  3 = กราฟิก & โมชั่น (คลิปโมชั่นสั้นๆ เล่นวน)\n  4 = Showreel (แทนคลิปหน้าแรก)")
    choice = ask("เลือก 1-4", "2" if vertical else ("3" if dur <= 20 else "1"))
    if choice == "3":
        return add_motion(src, dur, w, h, slug, c)
    if choice == "4":
        return set_showreel(src, dur, c)
    vertical = choice == "2"

    if vertical:
        title = ask("ชื่อคลิป")
        platform = ask("แพลตฟอร์ม", "Reels")
        url = ask("ลิงก์คลิปจริง (เว้นว่างได้)")
        manual = ask("วินาทีที่จะใช้เป็นตัวอย่าง (เว้นว่าง = เลือกอัตโนมัติ)")
        start = parse_time(manual) if manual else pick_highlights(src, dur, 1, 8)[0]
        length = min(8, dur - start)
        clip, poster = os.path.join(MEDIA, slug + ".mp4"), os.path.join(MEDIA, slug + "-poster.jpg")
        print("กำลังตัดคลิป...")
        cut_clip(src, start, length, clip, vertical=True)
        grab(src, start + length / 2, poster, vertical=True)
        c.setdefault("shorts", []).append({"title": title, "platform": platform, "clip": rel(clip), "poster": rel(poster), "url": url})
        save_content(c)
        print("เพิ่มลง Short-form แล้ว")
        git_publish(f"Add short: {title}")
        return

    title = ask("ชื่องาน (เช่น Vlog ญี่ปุ่น EP2 — โตเกียว)")
    tab = ask("ชื่อสั้นสำหรับเมนูด้านล่าง", title[:14])
    kind = ask("ประเภท · ลูกค้า (เช่น Gaming · VOICEZAN)")
    year = ask("ปี", str(date.today().year))
    roles = [r.strip() for r in ask("หน้าที่ที่ทำ คั่นด้วยจุลภาค", "Edit, Subtitle, Music, Color").split(",") if r.strip()]
    desc = ask("คำอธิบาย 1–2 บรรทัด")
    yt = yt_id(ask("ลิงก์ YouTube ของคลิปเต็ม (เว้นว่างได้)"))
    n = int(ask("จำนวนช่วงไฮไลท์", "6"))
    manual = ask("นาทีที่อยากใช้เป็นไฮไลท์ คั่นด้วยจุลภาค เช่น 1:23, 5:40 (เว้นว่าง = เลือกอัตโนมัติ)")
    starts = [parse_time(x) for x in manual.split(",") if x.strip()] if manual else pick_highlights(src, dur, n, 4)
    print("ช่วงที่ใช้: " + ", ".join(fmt_len(s) for s in starts))

    clips = []
    for i, s in enumerate(starts, 1):
        out = os.path.join(MEDIA, f"{slug}-h{i}.mp4")
        print(f"กำลังตัดไฮไลท์ {i}/{len(starts)}...")
        cut_clip(src, s, 4, out)
        clips.append(rel(out))
    poster = os.path.join(MEDIA, slug + "-poster.jpg")
    grab(src, starts[len(starts) // 2] + 2, poster)
    c.setdefault("works", []).append({"tab": tab, "title": title, "type": kind, "length": fmt_len(dur), "year": int(year) if year.isdigit() else year,
                                      "roles": roles, "desc": desc, "poster": rel(poster), "clips": clips, "yt": yt, "file": "", "url": ""})
    if yes("เพิ่มภาพนิ่ง 2 ภาพจากงานนี้ในหน้า Stills ด้วยไหม"):
        for i, s in enumerate(starts[:2], 1):
            out = os.path.join(MEDIA, f"{slug}-st{i}.jpg")
            grab(src, s + 1, out)
            c.setdefault("stills", []).append({"title": title, "src": rel(out)})
    save_content(c)
    print(f"\nเพิ่ม \"{title}\" แล้ว (ไฟล์อยู่ในโฟลเดอร์ media)")
    print("ถ้าอยากเปิดดูก่อนอัป: ดับเบิลคลิก index.html")
    git_publish(f"Add work: {title}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nยกเลิกแล้ว")
