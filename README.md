# DesktopDuck

DesktopDuck คือ desktop pet สำหรับ Windows เป็ดจะเดิน พัก หลับ พูด และตอบสนองต่อเมาส์อยู่เหนือหน้าต่างบนหน้าจอ ภาพเคลื่อนไหวใช้ sprite โปร่งใสและแสดงผลด้วย PySide6

## ความสามารถ

- เดินแบบเร่งและชะลออย่างนุ่มนวล พร้อมสุ่มพักหรือเปลี่ยนทิศ
- วิ่งหนีเมาส์เมื่อเคอร์เซอร์เข้าใกล้
- animation สำหรับเดิน ยืน หลับ และดีใจ
- ลากเป็ดด้วยคลิกซ้าย และดับเบิลคลิกเพื่อเล่นกับเป็ด
- เมนูคลิกขวาและ system tray
- รองรับพื้นที่ใช้งานเหนือ taskbar และหลายหน้าจอ
- บันทึกค่าที่ `%APPDATA%\DesktopDuck\config.json`
- ไม่มี network code, registry modification หรือ autostart

## รันจาก source

ต้องใช้ Python 3.10 ขึ้นไปบน Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

หรือดับเบิลคลิก `run_duck.bat` หลังติดตั้ง dependencies แล้ว

## การควบคุม

- คลิกซ้ายค้าง: ลากเป็ด
- ดับเบิลคลิก: ทำให้เป็ดดีใจและพูด
- คลิกขวา: เปิดเมนู
- `Esc`: ออกจากโปรแกรม

## สร้าง .exe

ค่าเริ่มต้นสร้างแบบ `onedir` ซึ่งเปิดเร็วและเหมาะกับการทดสอบ:

```powershell
.\build_exe.bat
```

สร้างไฟล์เดียวสำหรับนำไปแจก:

```powershell
.\build_exe.bat -OneFile
```

ผลลัพธ์อยู่ในโฟลเดอร์ `dist` ควรทดสอบบนเครื่อง Windows ที่ไม่มี Python ก่อนเผยแพร่
