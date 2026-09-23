import os
import asyncio
import discord
from google import genai
from aiohttp import web

# 環境変数
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.getenv("PORT", 8080))

if not DISCORD_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("環境変数 DISCORD_BOT_TOKEN または GEMINI_API_KEY が見つかりません。")

ai_client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user.name}")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    is_mentioned = bot.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)

    if not (is_mentioned or is_dm):
        return

    prompt = message.clean_content.replace(f"@{bot.user.name}", "").strip()
    if not prompt:
        await message.reply("メッセージを入力してください。")
        return

    async with message.channel.typing():
        try:
            response = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            reply_text = response.text or "返答を生成できませんでした。"

            if len(reply_text) <= 2000:
                await message.reply(reply_text)
            else:
                for i in range(0, len(reply_text), 1900):
                    await message.reply(reply_text[i : i + 1900])
        except Exception as e:
            print(f"エラー: {e}")
            await message.reply(f"エラーが発生しました: {e}")

# Renderの無料枠（Web Service）として動かすためのヘルスチェック用Webサーバー
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/healthz", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    await start_web_server()
    await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
