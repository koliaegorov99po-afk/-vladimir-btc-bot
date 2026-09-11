import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Токен и ID оператора
TOKEN = "8820422773:AAEfv_WkjdDcKlf0YUwxoRDYDZ-7xiHOwp0"
OPERATOR_ID = 8974638307

logging.basicConfig(level=logging.INFO)
router = Router()


class ExchangeState(StatesGroup):
  waiting_for_amount = State()
  waiting_for_receipt = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="💱 Купить / Продать крипту", callback_data="start_exchange"
          )
      ]]
  )
  await message.answer(
      "👋 Добро пожаловать в обменный сервис @VLADIMIR_BTC_MD!\n\n"
      "Здесь вы можете быстро и безопасно обменять валюту через нашего"
      " оператора.",
      reply_markup=kb,
  )


@router.callback_query(F.data == "start_exchange")
async def process_exchange(callback: Message, state: FSMContext):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🇷🇺 Рубли (СБП/Карта)", callback_data="pay_rub"
              ),
              InlineKeyboardButton(
                  text="🔷 USDT (TRC-20)", callback_data="pay_usdt"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="🪙 Bitcoin (BTC)", callback_data="pay_btc"
              ),
              InlineKeyboardButton(
                  text="🪙 Litecoin (LTC)", callback_data="pay_ltc"
              ),
          ],
      ]
  )
  await callback.message.answer(
      "💳 Выберите способ оплаты или актив:", reply_markup=kb
  )
  await callback.answer()


@router.callback_query(F.data.startswith("pay_"))
async def choose_currency(callback: Message, state: FSMContext):
  currency = callback.data.split("_")[1].upper()
  await state.update_data(currency=currency)
  await callback.message.answer(
      f"✍️ Вы выбрали: {currency}.\nВведите сумму для обмена (цифрами):"
  )
  await state.set_state(ExchangeState.waiting_for_amount)
  await callback.answer()


@router.message(ExchangeState.waiting_for_amount)
async def receive_amount(message: Message, state: FSMContext):
  await state.update_data(amount=message.text)
  data = await state.get_data()

  requisites = (
      "📌 **Реквизиты для оплаты:**\n"
      "Банк: СБП / Тинькофф / Сбер\n"
      f"Счет / Номер: `+37377xxxxxx`\n"
      f"Валюта/Сумма: {data['amount']} ({data['currency']})\n\n"
      "⚠️ **Важно:** после оплаты отправьте сюда скриншот или чек (фото квитанции)."
  )

  await message.answer(requisites, parse_mode="Markdown")
  await state.set_state(ExchangeState.waiting_for_receipt)


@router.message(ExchangeState.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
  data = await state.get_data()
  user = message.from_user

  caption = (
      f"🚨 **Новая заявка на обмен!**\n\n"
      f"👤 Пользователь: @{user.username} (ID: `{user.id}`)\n"
      f"💰 Валюта: {data['currency']}\n"
      f"💵 Сумма: {data['amount']}\n"
  )

  await message.bot.send_photo(
      chat_id=OPERATOR_ID,
      photo=message.photo[-1].file_id,
      caption=caption,
      parse_mode="Markdown",
  )

  await message.answer(
      "✅ Чек успешно отправлен оператору! Ожидайте проверки и зачисления"
      " средств."
  )
  await state.clear()


async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)
  await bot.delete_webhook(drop_pending_updates=True)
  print("Бот запущен и готов к работе!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
