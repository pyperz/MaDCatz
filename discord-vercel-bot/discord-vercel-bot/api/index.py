"""
Discord Bot แบบ HTTP Interactions - รันบน Vercel ได้
ต่างจากแบบเดิม (discord.py) ตรงที่ไม่ต้องเชื่อมต่อค้างไว้ตลอดเวลา
Discord จะยิง HTTP request มาหาไฟล์นี้ทุกครั้งที่มีคนใช้ slash command

รองรับเฉพาะ slash command เท่านั้น (ทำ !prefix command หรือ welcome message ไม่ได้)
"""

import os
import json
import random
import requests
from http.server import BaseHTTPRequestHandler
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# ----------------- ค่าที่ต้องตั้งใน Environment Variables ของ Vercel -----------------
DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

# Interaction types
PING = 1
APPLICATION_COMMAND = 2

# Response types
PONG = 1
CHANNEL_MESSAGE_WITH_SOURCE = 4


def verify_signature(signature: str, timestamp: str, body: str) -> bool:
    """เช็คว่า request นี้มาจาก Discord จริงๆ (ทุกโปรเจกต์ HTTP bot ต้องมีขั้นตอนนี้)"""
    try:
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        return False


def discord_api(method, path, **kwargs):
    """เรียก Discord REST API ด้วย Bot Token (ใช้สำหรับ kick/ban/clear)"""
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
    return requests.request(method, f"https://discord.com/api/v10{path}", headers=headers, **kwargs)


def handle_command(data, guild_id, channel_id, member):
    """จัดการแต่ละคำสั่งแล้วคืนค่าข้อความที่จะตอบกลับ"""
    name = data.get("name")
    options = {opt["name"]: opt["value"] for opt in data.get("options", [])}

    if name == "ping":
        return "🏓 Pong! (บอทออนไลน์อยู่)"

    if name == "hello":
        user_id = member["user"]["id"]
        return f"สวัสดีครับคุณ <@{user_id}> 👋"

    if name == "dice":
        return f"🎲 คุณทอยได้ {random.randint(1, 6)}"

    if name == "coin":
        return f"ผลลัพธ์: {random.choice(['หัว 🪙', 'ก้อย 🪙'])}"

    if name == "choose":
        choices_text = options.get("choices", "")
        choices = [c.strip() for c in choices_text.split(",") if c.strip()]
        if len(choices) < 2:
            return "พิมพ์ตัวเลือกอย่างน้อย 2 อย่าง คั่นด้วยจุลภาค เช่น `กินข้าว, กินก๋วยเตี๋ยว`"
        return f"🤔 ฉันเลือก... **{random.choice(choices)}**"

    if name == "kick":
        target_user_id = options.get("member")
        reason = options.get("reason", "ไม่ระบุเหตุผล")
        resp = discord_api(
            "DELETE",
            f"/guilds/{guild_id}/members/{target_user_id}",
            params={"reason": reason},
        )
        if resp.status_code == 204:
            return f"👢 เตะ <@{target_user_id}> ออกแล้ว เหตุผล: {reason}"
        return f"❌ เตะไม่สำเร็จ: {resp.text}"

    if name == "ban":
        target_user_id = options.get("member")
        reason = options.get("reason", "ไม่ระบุเหตุผล")
        resp = discord_api(
            "PUT",
            f"/guilds/{guild_id}/bans/{target_user_id}",
            json={"reason": reason},
        )
        if resp.status_code == 204:
            return f"🔨 แบน <@{target_user_id}> แล้ว เหตุผล: {reason}"
        return f"❌ แบนไม่สำเร็จ: {resp.text}"

    if name == "clear":
        amount = int(options.get("amount", 5))
        # ต้องดึงข้อความล่าสุดมาก่อน แล้วค่อยลบเป็นชุด (bulk delete)
        msgs_resp = discord_api("GET", f"/channels/{channel_id}/messages", params={"limit": amount})
        message_ids = [m["id"] for m in msgs_resp.json()]
        if message_ids:
            discord_api(
                "POST",
                f"/channels/{channel_id}/messages/bulk-delete",
                json={"messages": message_ids},
            )
        return f"🧹 ลบข้อความไปแล้ว {len(message_ids)} ข้อความ"

    return "❌ ไม่รู้จักคำสั่งนี้"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        signature = self.headers.get("X-Signature-Ed25519", "")
        timestamp = self.headers.get("X-Signature-Timestamp", "")

        if not verify_signature(signature, timestamp, body):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"invalid request signature")
            return

        interaction = json.loads(body)

        if interaction["type"] == PING:
            response = {"type": PONG}
        elif interaction["type"] == APPLICATION_COMMAND:
            message = handle_command(
                interaction["data"],
                interaction.get("guild_id"),
                interaction.get("channel_id"),
                interaction.get("member"),
            )
            response = {
                "type": CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": message},
            }
        else:
            response = {"type": CHANNEL_MESSAGE_WITH_SOURCE, "data": {"content": "❌ ไม่รองรับ"}}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Discord bot endpoint is running")
