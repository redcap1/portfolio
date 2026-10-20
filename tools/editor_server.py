# โหมดแก้เว็บ: เปิดเว็บในเครื่อง (http://localhost) ให้คลิกแก้ข้อความบนหน้าเว็บได้เลย → บันทึกลง content.js → อัปขึ้น GitHub
# เปิดด้วย แก้เว็บ.bat — ปิดหน้าต่างดำเพื่อเลิกใช้
import http.server, json, os, shutil, subprocess, webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content.js")
PREFIX = "window.CONTENT = "


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")  # always show the latest content.js
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
            if self.path == "/save":
                data = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
                if not isinstance(data, dict) or "profile" not in data:
                    return self.reply(400, {"ok": False, "msg": "ข้อมูลไม่ถูกต้อง"})
                shutil.copyfile(CONTENT, CONTENT + ".bak")  # undo: rename content.js.bak back
                with open(CONTENT, "w", encoding="utf-8", newline="\n") as f:
                    f.write(PREFIX + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")
                return self.reply(200, {"ok": True})
            if self.path == "/publish":
                run = lambda *c: subprocess.run(["git", *c], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
                run("add", "-A")
                run("commit", "-m", "Edit site text")
                p = run("push")
                return self.reply(200, {"ok": p.returncode == 0, "msg": (p.stdout + p.stderr).strip()[-400:]})
            self.reply(404, {"ok": False})
        except Exception as e:
            self.reply(500, {"ok": False, "msg": str(e)})

    def log_message(self, *a):
        pass


for port in range(8765, 8785):
    try:
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
        break
    except OSError:
        continue
url = f"http://localhost:{port}/?edit"
print("โหมดแก้เว็บเปิดอยู่ที่", url)
print("คลิกข้อความบนหน้าเว็บเพื่อแก้ → กด บันทึก → กด อัปขึ้นเว็บ")
print("เลิกใช้: ปิดหน้าต่างนี้")
if not os.environ.get("NO_BROWSER"):
    webbrowser.open(url)
srv.serve_forever()
