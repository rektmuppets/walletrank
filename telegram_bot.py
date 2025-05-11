import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, WebAppInfo
from aiohttp import web
from dotenv import load_dotenv
import os
from data_loader import load_data
from templates import get_copy_trade_template, get_domain_rankings_template, get_meme_trade_template, get_network_rankings_template, get_domain_copy_trade_template, get_landing_page_template

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher using the token from .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Load data
all_candidates, domain_rankings, network_rankings, domain_copy_trade_all = load_data()

# Web app route for copy trade candidates
async def serve_webapp(request):
    html = get_copy_trade_template(all_candidates)
    return web.Response(text=html, content_type='text/html')

# Web app route for domain wallet rankings
async def serve_domain_rankings(request):
    html = get_domain_rankings_template(domain_rankings)
    return web.Response(text=html, content_type='text/html')

# Web app route for meme trade candidates (using domain_copy_trade_all)
async def serve_meme_trade_candidates(request):
    html = get_meme_trade_template(domain_copy_trade_all)
    return web.Response(text=html, content_type='text/html')

# Web app route for network-wide wallet rankings
async def serve_network_rankings(request):
    html = get_network_rankings_template(network_rankings)
    return web.Response(text=html, content_type='text/html')

# Web app route for domain-specific copy trade candidates
async def serve_domain_copy_trade(request):
    html = get_domain_copy_trade_template(domain_copy_trade_all)
    return web.Response(text=html, content_type='text/html')

# Landing page for selecting rankings
async def serve_landing_page(request):
    html = get_landing_page_template()
    return web.Response(text=html, content_type='text/html')

# Set up aiohttp web server
app = web.Application()
app.router.add_get('/', serve_landing_page)
app.router.add_get('/webapp', serve_webapp)
app.router.add_get('/domain_rankings', serve_domain_rankings)
app.router.add_get('/meme_trade_candidates', serve_meme_trade_candidates)
app.router.add_get('/network_rankings', serve_network_rankings)
app.router.add_get('/domain_copy_trade', serve_domain_copy_trade)

async def start_web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# Command handler to open the mini-app
@dp.message(Command("start"))
async def start_command(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open Rankings", web_app=WebAppInfo(url="https://lumenbro.com/"))]
    ])
    await message.reply("Welcome to LumenBro Rankings! Click below to view wallet rankings:", reply_markup=keyboard)

# Main function to run both the bot and the web server
async def main():
    # Start the web server in a separate task
    asyncio.create_task(start_web_server())
    
    # Start the bot polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
