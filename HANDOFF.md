# HANDOFF — Video Editor Portfolio (ส่งต่อ session)

อัปเดตล่าสุด: 2026-10-20 · ผู้ใช้: เดชนรินทร์ คลอดกลาง (ไก่) — คุยภาษาไทยเสมอ

## ภาพรวม
- เว็บพอร์ตนักตัดต่อ: https://redcap1.github.io/portfolio/ (GitHub Pages, repo สาธารณะ `redcap1/portfolio`, branch `main`)
- โฟลเดอร์ในเครื่อง = git repo: `E:\VIdeoEditorWork\Portfolio` — push แล้ว Pages build เอง 1–2 นาที
- `gh` ติดตั้งแล้ว (`C:\Program Files\GitHub CLI\gh.exe`) ล็อกอินเป็น `redcap1`
- ฟุตเทจต้นฉบับ: `E:\FootagePort` (Koreavlogp1.mp4 30:41, VlogKoreaFullFixFPS.mp4 1:28:23, Work8_1.mp4 11:13, work9AddSpon.mp4 22:35) — งานลูกค้าช่อง VOICEZAN
- Showreel ต้นฉบับ: `E:\FootagePort\Showreel_Detnarin_2026.mp4` (60s, 34 ช็อต ตัดตามบีตเพลง Better Days 92 BPM ด้วย ffmpeg) — สคริปต์ตัดอยู่ใน scratchpad ของ session เก่า (หายได้)

## โครงสร้างเว็บ (หน้าเดียว ไม่มี scroll, เปลี่ยนหน้าแบบสไลด์)
- 6 หน้า: Showreel · Long-form (หน้าเดียว มีรายการเลือกงาน) · Short-form · ภาพนิ่ง · กราฟิก & โมชั่น · ติดต่อ
- เมนูล่างแบบเส้น+เลขหน้า, ลูกศร/ปุ่มคีย์บอร์ด/ล้อเมาส์/ปัด เปลี่ยนหน้า
- ธีมมืดเป็นค่าเริ่มต้น + ปุ่มสลับ (จำค่าใน localStorage)
- Showreel มี ambient glow (canvas เบลอ) แบบ YouTube
- Long-form เล่น "ไฮไลท์สุ่ม" 4 วิ/ช่วง; ปุ่ม "ดูคลิปเต็ม" → กล่องยืนยัน → ฝัง YouTube ในหน้า (ถ้ามี `yt`) / ไฟล์ในเครื่อง (`file`) / เปิดแท็บใหม่ (`url`, fallback = ค้นหา voicezan)
- ระยะขอบเท่ากันทุกด้าน: ตัวแปร CSS `--pad --side --head --nav --avail`; ขนาดสื่อคำนวณจาก `--avail`

## ไฟล์สำคัญ
- `content.js` — **ข้อมูลทั้งหมด** (`window.CONTENT = {...};` เป็น JSON ล้วนหลัง prefix): profile, theme, sections (ชื่อหัวข้อ/เมนู), showreel, works, shorts, stills, graphics
- `index.html` — โค้ด/ดีไซน์ (ไม่ต้องให้ผู้ใช้แก้)
- `tools/add_work.py` + `เพิ่มงาน.bat` — เพิ่มงานเอง: รูป/GIF→กราฟิก, วิดีโอ→เลือก Long/Short/โมชั่น/Showreel, หาไฮไลท์อัตโนมัติ (RMS เสียง + scene cut), เขียน content.js, git push
- `แก้เว็บ.bat` → `tools/editor_server.py` (http.server 127.0.0.1:8765+, เปิด `/?edit`, POST `/save` เขียน content.js + `.bak`, POST `/media` {op,index,file?,t?,times?} เปิด tkinter file dialog บนเครื่อง (ไม่อัปโหลด) แล้วใช้ ffmpeg helper จาก `add_work.py` — ops: photo, resume, showreel, work/addwork (ถาม times), poster, short/addshort (ถาม t), still/addstill (วิดีโอ→ถาม t), graphic/addgraphic; ไฟล์เก่าที่ไม่มีใครอ้างถึงถูกลบ (`drop_unused`), POST `/publish` git push) + `tools/editor.js` (โหลดเฉพาะ localhost + `?edit`; ข้อความ = contenteditable ตาม map id→path, ข้อความในปุ่ม/meta/roles = ดับเบิลคลิก → prompt, ปุ่ม `.edt` ลอยบนสื่อ, ปุ่ม `.ed-add` เพิ่มรายการ, ลิงก์ติดต่อ = คลิก → prompt; การเปลี่ยนโครงสร้าง = save แล้ว reload, จำงาน Long-form ที่เปิดอยู่ใน sessionStorage) — **ทิศทางที่ผู้ใช้ต้องการ: แก้ทุกอย่างบนหน้าเว็บเอง**
- ฟอนต์: **Prompt** (Google Fonts, OFL ใช้เชิงพาณิชย์ได้) ทั้งเว็บ — ผู้ใช้เลือกเอง; `--muted` เข้มขึ้น, ตัวเล็กสุด ~12.5px
- `อัปเดตเว็บ.bat` — git add/commit/push
- `วิธีอัปเดตเว็บ.md` — คู่มือภาษาไทยสำหรับผู้ใช้ (อัปเดตทุกครั้งที่เพิ่มฟีเจอร์)
- `media/` — คลิปไฮไลท์ bh*/mh*/th*, posters, stills, showreel.mp4 (14 MB), me.jpg (รูปตัวอย่าง)

## Resume
- `E:\FootagePort\Resume\resume.html` → PDF `Detnarin_Klodklang_Resume_VideoEditor_DRAFT.pdf` (คอลัมน์เดียว ATS-friendly, ลิงก์พอร์ตเป็นข้อความ, QR ท้ายหน้า, รูปมุมขวาบน)
- ยังรอ: ช่วงเวลา 3 งาน (VOICEZAN ฟรีแลนซ์ / mungkonggadet / Goodmood Media ฝึกงาน), รายละเอียดงาน mungkonggadet + Goodmood, ตัวเลขงาน VOICEZAN, รูปจริง
- เบอร์โทรอยู่ใน PDF (ส่งบริษัท) — **ห้ามขึ้นเว็บสาธารณะ**
- รูปโปรไฟล์: ผู้ใช้ทำผ่าน Gemini เอง (แชต "Resume Headshot Photo Editing") — รูปสตูดิโอที่ผู้ใช้ส่งมาใช้เป็น placeholder `media/me.jpg`; ผู้ใช้บอกจะใส่รูปเอง

## สิ่งที่ยังค้าง
1. ลิงก์ YouTube (Unlisted, เปิด embed) ของ 3 งาน → ใส่ `yt` ใน content.js
2. คลิปแนวตั้ง (Short-form ยังว่าง), ผลงานกราฟิก/โมชั่น (ยังว่าง)
3. Resume รูปภาพสำหรับ popover บนเว็บ (`profile.resume`) — ต้องเป็นเวอร์ชันไม่มีเบอร์โทร
4. โหมดแก้ไข: ยังไม่มีการเรียงลำดับงานใหม่ (ต้องแก้ใน content.js); file dialog ทดสอบผ่าน `file` param เท่านั้น ยังไม่ได้ลองกดจริงบนเดสก์ท็อป (เช็ก 1366x768 หลังเปลี่ยนเป็น Prompt แล้ว: ทุกหน้าพอดี ขอบ 46px)
5. ภาพนิ่งบางรูปและช่วงไฮไลท์เลือกจากภาพ+เสียง ไม่ได้ฟังบทพูด — ผู้ใช้อาจอยากเปลี่ยน

## ความชอบของผู้ใช้
- มินิมอล เน้นงาน, ไม่ชอบอะไรที่ "หลุดธีม" (สีจัด/กล่องทึบ)
- คิดแบบ HR: เปิดมาต้องรู้ทันทีว่าคืออะไร, ไม่ต้องให้ดูคลิปเต็ม
- ต้องอัปเดตเองได้หลังหมดโปร Claude — ทุกอย่างต้องแก้ผ่าน content.js / bat ได้
- ฟรีเท่านั้น (ไม่จ่ายค่าเซิร์ฟเวอร์)

## Gotchas (เจอมาแล้ว)
- **ffmpeg filter ที่มี path `C:`** พัง (colon) → ให้ output เป็นชื่อไฟล์ relative แล้วรันใน cwd นั้น
- **drawtext ใน ffmpeg crash** (fontconfig) → ทำการ์ดข้อความด้วย HTML + Edge headless screenshot (`--default-background-color=00000000` ได้ PNG โปร่งใส)
- **Edge headless** หลังอัปเดตเงียบไม่ออกไฟล์ → ใส่ `--user-data-dir=<โฟลเดอร์ใหม่ต่อครั้ง>`; ถ้ายังไม่ได้ ให้เช็กบนเว็บจริงด้วย browser pane
- **Bash heredoc ยาวที่มี backtick/`\n`** พังบ่อย → เขียนสคริปต์ Python ด้วย Write tool แล้วรัน
- หน้า GitHub Pages ไม่มี skeleton แบบ Artifact → ต้องมี `[hidden]{display:none!important}` เอง (มีแล้ว)
- browser pane โดนเลื่อนข้างจาก hash anchor → deck ล็อก scrollLeft/Top=0 (มีแล้ว)
- Gemini บล็อก fetch จาก localhost → อัปรูปด้วยการ copy ลงคลิปบอร์ดจากแท็บ localhost แล้ว Ctrl+V
- `python -X utf8` เวลาพิมพ์ภาษาไทยในคอนโซล
