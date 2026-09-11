import asyncio
import logging
import aiohttp
import aiosqlite
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ================= CONFIG =================
BOT_TOKEN = "8820422773:AAEfv_WkjdDcKlf0YUwxoRDYDZ-7xiHOwp0"
OPERATOR_ID = 8974638307
OPERATOR_USERNAME = "@VLADIMIR_BTC_MD"
DB_NAME = "exchange_bot.db"

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance_pmr REAL DEFAULT 0.0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                deal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pair TEXT,
                amount REAL,
                status TEXT
            )
        """)
        await db.commit()

# ================= BINANCE API =================
async def get_binance_price(symbol: str) -> float:
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['price'])
    except Exception:
        pass
    return 0.0

# ================= STATES =================
class ExchangeStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()

# ================= ROUTER & HANDLERS =================
router = Router()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💱 Обменять валюту", callback_data="start_exchange")],
        [InlineKeyboardButton(text="👤 Профиль / Баланс", callback_data="profile")],
        [InlineKeyboardButton(text="💬 Связаться с оператором", url=f"https://t.me/{OPERATOR_USERNAME.replace('@', '')}")]
    ])

@router.message(Command("start"))
async def cmd_start(message: Message):
    try:
        photo = FSInputFile("image_0.png")
        await message.answer_photo(
            photo=photo,
            caption=(
                "👋 Добро пожаловать в официальный обменный сервис!\n\n"
                "Надежный обмен криптовалюты и фиата (ПМР/РФ рубли, MDL, USDT, BTC, LTC)."
            ),
            reply_markup=main_menu()
        )
    except Exception:
        await message.answer(
            "👋 Добро пожаловать в официальный обменный сервис!\n\n"
            "Надежный обмен криптовалюты и фиата.",
            reply_markup=main_menu()
        )

@router.callback_query(F.data == "start_exchange")
async def choose_pair(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 ПМР Рубль ➡️ USDT", callback_data="pair_pmr_usdt")],
        [InlineKeyboardButton(text="🟢 USDT ➡️ ПМР Рубль", callback_data="pair_usdt_pmr")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    await callback.message.edit_caption(caption="Выберите направление обмена:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "pair_pmr_usdt")
async def process_pmr_usdt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ExchangeStates.waiting_for_amount)
    await state.update_data(pair="PMR -> USDT")
    await callback.message.edit_caption(caption="Введите сумму в ПМР рублях, которую хотите обменять:")
    await callback.answer()

@router.message(ExchangeStates.waiting_for_amount)
async def get_amount(message: Message, state: FSMContext, bot: Bot):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")
        return

    calculated = round(amount / 16.5, 2)

    await state.update_data(amount=amount, total=calculated)
    await state.set_state(ExchangeStates.waiting_for_receipt)

    await message.answer(
        f"📝 **Детали заявки:**\n"
        f"Сумма: {amount} ПМР\n"
        f"К получению: ~{calculated} USDT\n\n"
        f"Пожалуйста, сделайте перевод на наши реквизиты и отправьте сюда скриншот чека (квитанцию)."
    )

@router.message(ExchangeStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    
    operator_text = (
        f"🔥 **Новая заявка на обмен!**\n\n"
        f"От пользователя: @{message.from_user.username} (ID: `{message.from_user.id}`)\n"
        f"Направление: {data.get('pair')}\n"
        f"Сумма: {data.get('amount')}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить перевод", callback_data=f"approve_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"cancel_{message.from_user.id}")]
    ])

    await bot.send_photo(chat_id=OPERATOR_ID, photo=photo_id, caption=operator_text, reply_markup=kb)
    await message.answer("✅ Ваша квитанция принята! Ожидайте проверки оператором.", reply_markup=main_menu())
    await state.clear()

@router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_caption(caption="Главное меню:", reply_markup=main_menu())
    await callback.answer()

# ================= MAIN RUN =================
async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
