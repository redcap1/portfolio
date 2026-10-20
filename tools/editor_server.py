# โหมดแก้เว็บ: เปิดเว็บในเครื่อง (http://localhost) ให้คลิกแก้ข้อความ เปลี่ยนวิดีโอ/รูป/ลิงก์บนหน้าเว็บได้เลย → บันทึกลง content.js → อัปขึ้น GitHub
# เปิดด้วย แก้เว็บ.bat — ปิดหน้าต่างดำเพื่อเลิกใช้
import http.server, json, os, shutil, subprocess, threading, time, webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content.js")
PREFIX = "window.CONTENT = "
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".m4v", ".webm"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
dialog_lock = threading.Lock()


def tools():
    """ffmpeg helpers from add_work.py, loaded only when a video or picture is changed."""
    import add_work
    return add_work


def write_content(c):
    shutil.copyfile(CONTENT, CONTENT + ".bak")  # undo: rename content.js.bak back
    with open(CONTENT, "w", encoding="utf-8", newline="\n") as f:
        f.write(PREFIX + json.dumps(c, ensure_ascii=False, indent=2) + ";\n")


def pick(kind):
    """Open the Windows file dialog on this computer (no upload needed, works for huge footage)."""
    import tkinter as tk
    from tkinter import filedialog
    types = {"video": [("วิดีโอ", "*.mp4 *.mov *.mkv *.m4v *.webm")],
             "image": [("รูป", "*.jpg *.jpeg *.png *.gif *.webp")],
             "any": [("วิดีโอ / รูป", "*.mp4 *.mov *.mkv *.m4v *.webm *.jpg *.jpeg *.png *.gif *.webp")]}[kind]
    with dialog_lock:
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
        p = filedialog.askopenfilename(parent=r, title="เลือกไฟล์", filetypes=types + [("ทุกไฟล์", "*.*")])
        r.destroy()
    return p


def to_jpg(aw, src, out, width=1800):
    aw.run([aw.FFMPEG, "-v", "error", "-i", src, "-frames:v", "1", "-vf", f"scale='min({width},iw)':-2", "-q:v", "3", "-y", out])


def drop_unused(old, c):
    """Delete replaced media files that nothing in content.js points to any more (keeps the repo small)."""
    used = json.dumps(c, ensure_ascii=False)
    for p in old:
        if isinstance(p, str) and p.startswith("media/") and f'"{p}"' not in used:
            try:
                os.remove(os.path.join(ROOT, p))
            except OSError:
                pass


def media_op(req):
    """Change a video or picture. Returns {"ok": True} or {"ask": "time", ...} when a frame time is needed."""
    op, i = req["op"], req.get("index")
    kind = {"photo": "image", "resume": "image", "poster": "image", "still": "any", "graphic": "any"}.get(op, "video")
    src = req.get("file") or pick(kind)
    if not src:
        return {"ok": False, "msg": "ไม่ได้เลือกไฟล์"}
    aw = tools()
    c = aw.load_content()
    ext = os.path.splitext(src)[1].lower()
    is_vid = ext in VIDEO_EXT
    slug = "w" + time.strftime("%y%m%d%H%M%S")
    media = lambda name: os.path.join(ROOT, "media", name)
    old = []

    if op in ("photo", "resume"):
        out = media(f"{op}-{slug}.jpg")
        to_jpg(aw, src, out, 900 if op == "photo" else 1600)
        old.append(c["profile"].get(op))
        c["profile"][op] = aw.rel(out)

    elif op == "showreel":
        dur, _, _ = aw.probe(src)
        out, poster = media(f"showreel-{slug}.mp4"), media(f"showreel-{slug}-poster.jpg")
        aw.run([aw.FFMPEG, "-v", "error", "-i", src, "-vf", "scale=1280:-2", "-c:v", "libx264", "-preset", "slow", "-crf", "25",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-y", out])
        aw.grab(src, min(1.2, dur / 2), poster)
        reel = c.get("showreel") or {"title": "Showreel"}
        old += [reel.get("src"), reel.get("poster")]
        reel.update({"src": aw.rel(out), "poster": aw.rel(poster), "length": aw.fmt_len(dur)})
        c["showreel"] = reel

    elif op in ("work", "addwork"):
        dur, _, _ = aw.probe(src)
        if "times" not in req:
            return {"ask": "times", "file": src, "dur": aw.fmt_len(dur)}
        manual = req["times"].strip()
        starts = [aw.parse_time(x) for x in manual.split(",") if x.strip()] if manual else aw.pick_highlights(src, dur, 6, 4)
        clips = []
        for k, s in enumerate(starts, 1):
            out = media(f"{slug}-h{k}.mp4")
            aw.cut_clip(src, s, 4, out)
            clips.append(aw.rel(out))
        poster = media(slug + "-poster.jpg")
        aw.grab(src, starts[len(starts) // 2] + 2, poster)
        if op == "addwork":
            c.setdefault("works", []).append({"tab": "งานใหม่", "title": "ชื่องานใหม่", "type": "ประเภท · ลูกค้า", "length": aw.fmt_len(dur),
                                              "year": time.localtime().tm_year, "roles": ["Edit"], "desc": "คำอธิบายงาน",
                                              "poster": aw.rel(poster), "clips": clips, "yt": "", "file": "", "url": ""})
        else:
            w = c["works"][i]
            old += w.get("clips", []) + [w.get("poster")]
            w.update({"clips": clips, "poster": aw.rel(poster), "length": aw.fmt_len(dur)})

    elif op == "poster":
        out = media(slug + "-poster.jpg")
        to_jpg(aw, src, out, 1600)
        old.append(c["works"][i].get("poster"))
        c["works"][i]["poster"] = aw.rel(out)

    elif op in ("short", "addshort"):
        dur, _, _ = aw.probe(src)
        if "t" not in req:
            return {"ask": "time", "file": src, "dur": aw.fmt_len(dur)}
        start = aw.parse_time(req["t"]) if str(req["t"]).strip() else aw.pick_highlights(src, dur, 1, 8)[0]
        length = min(8, dur - start)
        clip, poster = media(slug + ".mp4"), media(slug + "-poster.jpg")
        aw.cut_clip(src, start, length, clip, vertical=True)
        aw.grab(src, start + length / 2, poster, vertical=True)
        if op == "addshort":
            c.setdefault("shorts", []).append({"title": "ชื่อคลิป", "platform": "Reels", "clip": aw.rel(clip), "poster": aw.rel(poster), "url": ""})
        else:
            s = c["shorts"][i]
            old += [s.get("clip"), s.get("poster")]
            s.update({"clip": aw.rel(clip), "poster": aw.rel(poster)})

    elif op in ("still", "addstill"):
        out = media(slug + ".jpg")
        if is_vid:
            if "t" not in req:
                dur, _, _ = aw.probe(src)
                return {"ask": "time", "file": src, "dur": aw.fmt_len(dur)}
            aw.grab(src, aw.parse_time(req["t"] or "0"), out)
        else:
            to_jpg(aw, src, out)
        w, h = aw.img_size(out)
        if op == "addstill":
            c.setdefault("stills", []).append({"title": "คำบรรยายภาพ", "src": aw.rel(out), "wide": w / h > 2})
        else:
            old.append(c["stills"][i].get("src"))
            c["stills"][i]["src"] = aw.rel(out)

    elif op in ("graphic", "addgraphic"):
        if is_vid:
            dur, w, h = aw.probe(src)
            start = aw.parse_time(req.get("t") or "0")
            length = min(15, dur - start)
            out, poster = media(slug + ".mp4"), media(slug + "-poster.jpg")
            scale = "scale=-2:720" if h > w else "scale=960:-2"
            aw.run([aw.FFMPEG, "-v", "error", "-ss", str(start), "-t", str(length), "-i", src, "-an", "-vf", scale + ",fps=30",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", out])
            aw.grab(src, start + length / 2, poster, vertical=h > w)
            item = {"src": aw.rel(out), "poster": aw.rel(poster), "ratio": f"{w}/{h}"}
        else:
            w, h = aw.img_size(src)
            if ext in (".gif", ".webp"):
                out = media(slug + ext)
                shutil.copyfile(src, out)  # keep the animation
            else:
                out = media(slug + ".jpg")
                to_jpg(aw, src, out)
            item = {"src": aw.rel(out), "ratio": f"{w}/{h}"}
        if op == "addgraphic":
            c.setdefault("graphics", []).append({"title": "ชื่อผลงาน", **item})
        else:
            g = c["graphics"][i]
            old += [g.get("src"), g.get("poster")]
            g.pop("poster", None)
            g.update(item)
    else:
        return {"ok": False, "msg": "ไม่รู้จักคำสั่ง"}

    write_content(c)
    drop_unused(old, c)
    return {"ok": True}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")  # always show the latest content.js and media
        super().end_headers()

    def reply(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            if self.path == "/save":
                if not isinstance(data, dict) or "profile" not in data:
                    return self.reply(400, {"ok": False, "msg": "ข้อมูลไม่ถูกต้อง"})
                old = media_paths(read_content())
                write_content(data)
                drop_unused(old, data)  # files of deleted items go too
                return self.reply(200, {"ok": True})
            if self.path == "/media":
                return self.reply(200, media_op(data))
            if self.path == "/publish":
                run = lambda *c: subprocess.run(["git", *c], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
                run("add", "-A")
                run("commit", "-m", "Edit site in edit mode")
                p = run("push")
                return self.reply(200, {"ok": p.returncode == 0, "msg": (p.stdout + p.stderr).strip()[-400:]})
            self.reply(404, {"ok": False})
        except SystemExit as e:  # add_work exits when ffmpeg is missing
            self.reply(500, {"ok": False, "msg": str(e)})
        except Exception as e:
            self.reply(500, {"ok": False, "msg": f"{type(e).__name__}: {e}"})

    def log_message(self, *a):
        pass


def read_content():
    s = open(CONTENT, encoding="utf-8").read().strip()
    return json.loads(s[len(PREFIX):].rstrip(";"))


def media_paths(o):
    if isinstance(o, dict):
        return [p for v in o.values() for p in media_paths(v)]
    if isinstance(o, list):
        return [p for v in o for p in media_paths(v)]
    return [o] if isinstance(o, str) and o.startswith("media/") else []


if __name__ == "__main__":
    for port in range(8765, 8785):
        try:
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    url = f"http://localhost:{port}/?edit"
    print("โหมดแก้เว็บเปิดอยู่ที่", url)
    print("คลิกข้อความบนหน้าเว็บเพื่อแก้ / ปุ่มบนวิดีโอและรูปเพื่อเปลี่ยน → กด บันทึก → กด อัปขึ้นเว็บ")
    print("เลิกใช้: ปิดหน้าต่างนี้")
    if not os.environ.get("NO_BROWSER"):
        webbrowser.open(url)
    srv.serve_forever()
