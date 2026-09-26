"""
สคริปต์สำหรับลงทะเบียน slash command กับ Discord
รันครั้งเดียวบนเครื่องตัวเอง (ไม่ต้องรันบน Vercel) ทุกครั้งที่เพิ่ม/แก้ไขคำสั่ง

วิธีใช้:
  1. pip install requests
  2. แก้ APPLICATION_ID และ BOT_TOKEN ด้านล่าง
  3. รัน: python register_commands.py
"""

import requests

APPLICATION_ID = "YOUR_APPLICATION_ID_HERE"  # หาได้จากหน้า General Information ใน Developer Portal
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

URL = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/commands"
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}

commands = [
    {"name": "ping", "description": "เช็คว่าบอทตอบสนองไหม"},
    {"name": "hello", "description": "ให้บอททักทาย"},
    {"name": "dice", "description": "ทอยลูกเต๋า 1-6"},
    {"name": "coin", "description": "โยนเหรียญ หัว/ก้อย"},
    {
        "name": "choose",
        "description": "ให้บอทช่วยเลือกจากตัวเลือกที่ให้ (คั่นด้วยจุลภาค)",
        "options": [
            {
                "name": "choices",
                "description": "ตัวเลือก คั่นด้วยจุลภาค เช่น กินข้าว, กินก๋วยเตี๋ยว",
                "type": 3,  # STRING
                "required": True,
            }
        ],
    },
    {
        "name": "kick",
        "description": "เตะสมาชิกออกจากเซิร์ฟเวอร์",
        "default_member_permissions": "2",  # ต้องมีสิทธิ์ Kick Members
        "options": [
            {"name": "member", "description": "สมาชิกที่จะเตะ", "type": 6, "required": True},  # USER
            {"name": "reason", "description": "เหตุผล", "type": 3, "required": False},
        ],
    },
    {
        "name": "ban",
        "description": "แบนสมาชิกออกจากเซิร์ฟเวอร์",
        "default_member_permissions": "4",  # ต้องมีสิทธิ์ Ban Members
        "options": [
            {"name": "member", "description": "สมาชิกที่จะแบน", "type": 6, "required": True},
            {"name": "reason", "description": "เหตุผล", "type": 3, "required": False},
        ],
    },
    {
        "name": "clear",
        "description": "ลบข้อความล่าสุดในห้อง",
        "default_member_permissions": "8192",  # ต้องมีสิทธิ์ Manage Messages
        "options": [
            {"name": "amount", "description": "จำนวนข้อความที่จะลบ", "type": 4, "required": False},  # INTEGER
        ],
    },
]

for cmd in commands:
    resp = requests.post(URL, headers=HEADERS, json=cmd)
    if resp.status_code in (200, 201):
        print(f"✅ ลงทะเบียนคำสั่ง /{cmd['name']} สำเร็จ")
    else:
        print(f"❌ ลงทะเบียนคำสั่ง /{cmd['name']} ไม่สำเร็จ: {resp.status_code} {resp.text}")
