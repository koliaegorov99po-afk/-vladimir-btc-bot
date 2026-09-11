import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
import aiohttp

# Токен и ID оператора
TOKEN = "8616697712:AAHeF6EDbZYld2l-St6qxSpGQTu7-zSNNHY"
OPERATOR_ID = 8974638307

# Прямая ссылка на картинку для приветствия (замените при желании на свою рабочую ссылку)
WELCOME_PHOTO_URL = "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=800"

logging.basicConfig(level=logging.INFO)
router = Router()


class ExchangeState(StatesGroup):
  direction = State()  # buy_crypto or sell_crypto
  currency = State()
  payment_method = State()
  waiting_for_amount = State()
  waiting_for_receipt = State()


# Получение актуальных курсов с Binance (или заглушки при сбое)
async def get_binance_prices():
  prices = {"BTC": 90000.0, "LTC": 100.0, "TRX": 0.25, "USDT": 1.0, "TON": 5.0}
  try:
    async with aiohttp.ClientSession() as session:
      async with session.get(
          "https://api.binance.com/api/v3/ticker/price"
      ) as response:
        if response.status == 200:
          data = await response.json()
          for item in data:
            symbol = item["symbol"]
            price = float(item["price"])
            if symbol == "BTCUSDT":
              prices["BTC"] = price
            elif symbol == "LTCUSDT":
              prices["LTC"] = price
            elif symbol == "TRXUSDT":
              prices["TRX"] = price
            elif symbol == "TONUSDT":
              prices["TON"] = price
  except Exception as e:
    logging.error(f"Ошибка получения курсов Binance: {e}")
  return prices


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🟢 Купить крипту за фиат", callback_data="dir_buy"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔴 Продать крипту за фиат", callback_data="dir_sell"
              )
          ],
      ]
  )

  welcome_text = (
      "👋 Добро пожаловать в обменный сервис @VLADIMIR_BTC_MD!\n\n"
      "Здесь вы можете быстро и безопасно обменять фиат и криптовалюту."
  )

  try:
    await message.answer_photo(
        photo=WELCOME_PHOTO_URL, caption=welcome_text, reply_markup=kb
    )
  except Exception:
    await message.answer(welcome_text, reply_markup=kb)


@router.callback_query(F.data.startswith("dir_"))
async def process_direction(callback: CallbackQuery, state: FSMContext):
  direction = callback.data.split("_")[1]
  await state.update_data(direction=direction)

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔷 USDT (TRC-20)", callback_data="cur_USDT_TRC20"
              ),
              InlineKeyboardButton(
                  text="🔷 USDT (BEP-20)", callback_data="cur_USDT_BEP20"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="🔷 USDT (TON)", callback_data="cur_USDT_TON"
              ),
              InlineKeyboardButton(
                  text="🪙 Bitcoin (BTC)", callback_data="cur_BTC"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="🪙 Litecoin (LTC)", callback_data="cur_LTC"
              ),
              InlineKeyboardButton(text="🪙 TRON (TRX)", callback_data="cur_TRON"),
          ],
      ]
  )
  await callback.message.answer(
      "🪙 Выберите криптовалюту для операции:", reply_markup=kb
  )
  await callback.answer()


@router.callback_query(F.data.startswith("cur_"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
  parts = callback.data.split("_")
  currency = parts[1]
  if len(parts) > 2:
    currency += f"_{parts[2]}"
  await state.update_data(currency=currency)

  data = await state.get_data()
  direction = data.get("direction")

  if direction == "buy":
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Рубли РФ (СБП)", callback_data="pay_RUB_SBP"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Рубли ПМР (П2П / Эксим)", callback_data="pay_PMR"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧮 Леи МД (Paynet / MIA / MAIB)",
                    callback_data="pay_MDL",
                )
            ],
        ]
    )
    await callback.message.answer(
        "💳 Выберите способ оплаты (фиат):", reply_markup=kb
    )
  else:
    await callback.message.answer(
        f"✍️ Вы выбрали продажу {currency}.\nВведите сумму криптовалюты для"
        " продажи (цифрами):"
    )
    await state.set_state(ExchangeState.waiting_for_amount)
  await callback.answer()


@router.callback_query(F.data.startswith("pay_"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
  parts = callback.data.split("_")
  pay_method = parts[1]
  if len(parts) > 2:
    pay_method += f"_{parts[2]}"
  await state.update_data(payment_method=pay_method)

  await callback.message.answer(
      "✍️ Введите сумму в фиате, которую хотите обменять (цифрами):"
  )
  await state.set_state(ExchangeState.waiting_for_amount)
  await callback.answer()


@router.message(ExchangeState.waiting_for_amount)
async def receive_amount(message: Message, state: FSMContext):
  try:
    amount = float(message.text.strip().replace(",", "."))
  except ValueError:
    await message.answer(
        "❌ Пожалуйста, введите корректное число цифрами (например:"
        " 1000 или 50.5)."
    )
    return

  await state.update_data(amount=amount)
  data = await state.get_data()
  direction = data["direction"]
  currency = data["currency"]
  prices = await get_binance_prices()

  base_coin = currency.split("_")[0]
  coin_price_usd = prices.get(base_coin, 1.0)

  calc_details = ""
  requisites = ""

  if direction == "buy":
    pay_method = data.get("payment_method")
    usd_amount = 0

    if "RUB" in pay_method:
      usd_amount = amount / 100.0
      calc_details = f"Сумма: {amount} RUB\nКурс: 1$ = 100 RUB"
      requisites = (
          "📌 **Реквизиты для оплаты (Рубли РФ СБП):**\n"
          "🏦 **Сбер банк / Т банк / ВТБ банк**\n"
          "Номер: `+79019727196`\n"
      )
    elif "PMR" in pay_method:
      usd_amount = amount / 19.0
      calc_details = f"Сумма: {amount} ПМР руб\nКурс: 1$ = 19 ПМР"
      requisites = (
          "📌 **Реквизиты для оплаты (ПМР):**\n"
          "🏦 **ЭКСИМ / ПЕРЕВОДИЛКА**\n"
          "Счет/Номер: `77507411`\n"
      )
    elif "MDL" in pay_method:
      usd_amount = amount / 21.0
      calc_details = f"Сумма: {amount} MDL\nКурс: 1$ = 21 MDL"
      requisites = (
          "📌 **Реквизиты для оплаты (Леи МД):**\n"
          "🏦 **ПАЙНЕТ / МИЯ:** `068728340`\n"
          "🏦 **РУН ПАЙ / МИЯ:** `068728340`\n"
          "🏦 **МАИБ (Marina Russ):** `4356960081341247`\n"
      )

    crypto_amount = usd_amount / coin_price_usd if coin_price_usd > 0 else 0
    await state.update_data(
        calculated_crypto=crypto_amount, usd_amount=usd_amount
    )

    text = (
        f"🧮 **Расчет обмена:**\n{calc_details}\n"
        f"💵 Эквивалент в USD: `${usd_amount:.2f}`\n"
        f"🪙 Получите криптовалюту ({currency}): `{crypto_amount:.6f}`\n\n"
        f"{requisites}\n"
        "⚠️ **Важно:** После оплаты отправьте ответным сообщением **скриншот"
        " чека** и **хеш транзакции (если есть)**."
    )
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(ExchangeState.waiting_for_receipt)

  else:
    crypto_amount = amount
    usd_amount = crypto_amount * coin_price_usd

    rub_rf = usd_amount * 72.0
    pmr_rub = usd_amount * 16.0
    mdl_lei = usd_amount * 17.0

    await state.update_data(usd_amount=usd_amount)

    crypto_wallet = ""
    if "LTC" in currency:
      crypto_wallet = "`ltc1qkprk223v0hjc36g2dlysmtlgqdzrtp48xwvwja`"
    elif "BEP20" in currency:
      crypto_wallet = "`0x89b28d58ce3e521a920d6b8f008841c3cd3d5747`"
    elif "TRC20" in currency:
      crypto_wallet = "`TELVh3pvb2HKcL2fd6UQFwfBEEs7m3mi6v`"
    elif "BTC" in currency:
      crypto_wallet = "`3AvgzeSvUh5MXz9QSuyRwBDjLDAmsp7Z8M`"
    elif "TON" in currency:
      crypto_wallet = "`UQCVdkthxRGvHJV68mLfcGYuHYfL_2sWZVylZIGBVl7cZElX`"
    else:
      crypto_wallet = "`Адрес уточняйте у оператора`"

    text = (
        f"🧮 **Расчет продажи крипты:**\n"
        f"🪙 Сумма крипты: `{crypto_amount} {currency}`\n"
        f"💵 Эквивалент в USD: `${usd_amount:.2f}`\n\n"
        "💰 **Вы получите:**\n"
        f"• Рубли РФ (72р за 1$): **{rub_rf:.2f} RUB**\n"
        f"• Рубли ПМР (16р за 1$): **{pmr_rub:.2f} ПМР**\n"
        f"• Леи МД (17 лей за 1$): **{mdl_lei:.2f} MDL**\n\n"
        "📌 **Переведите криптовалюту на наш кошелек:**\n"
        f"{crypto_wallet}\n\n"
        "⚠️ **Важно:** После перевода отправьте **скриншот чека** и **хеш"
        " транзакции**."
    )
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(ExchangeState.waiting_for_receipt)


@router.message(ExchangeState.waiting_for_receipt)
async def receive_receipt(message: Message, state: FSMContext):
  data = await state.get_data()
  user = message.from_user

  deal_id = f"DEAL-{user.id}-{message.message_id}"

  photo_id = message.photo[-1].file_id if message.photo else None
  text_caption = message.caption or message.text or "Без текста/чека"

  operator_caption = (
      f"🚨 **Новая заявка на обмен!**\n"
      f"🆔 Номер сделки: `{deal_id}`\n"
      f"👤 Пользователь: @{user.username} (ID: `{user.id}`)\n"
      f"🔄 Направление: {data.get('direction')}\n"
      f"🪙 Валюта: {data.get('currency')}\n"
      f"💵 Сумма: {data.get('amount')}\n"
      f"📄 Данные/Хеш от клиента: {text_caption}\n"
  )

  kb_operator = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="✅ Подтвердить и выплатить",
                  callback_data=f"op_approve_{user.id}_{deal_id}",
              ),
              InlineKeyboardButton(
                  text="❌ Отклонить",
                  callback_data=f"op_decline_{user.id}_{deal_id}",
              ),
          ]
      ]
  )

  if photo_id:
    await message.bot.send_photo(
        chat_id=OPERATOR_ID,
        photo=photo_id,
        caption=operator_caption,
        reply_markup=kb_operator,
        parse_mode="Markdown",
    )
  else:
    await message.bot.send_message(
        chat_id=OPERATOR_ID,
        text=operator_caption,
        reply_markup=kb_operator,
        parse_mode="Markdown",
    )

  await message.answer(
      f"✅ Заявка принята! Номер вашей сделки: `{deal_id}`.\nОжидайте проверки"
      " оператором.",
      parse_mode="Markdown",
  )
  await state.clear()


@router.callback_query(F.data.startswith("op_"))
async def operator_action(callback: CallbackQuery):
  parts = callback.data.split("_")
  action = parts[1]
  target_user_id = int(parts[2])
  deal_id = parts[3]

  if action == "approve":
    await callback.bot.send_message(
        chat_id=target_user_id,
        text=(
            f"✅ **Ваша сделка `{deal_id}` успешно подтверждена"
            " оператором!**\nСредства / криптовалюта отправлены по вашим"
            " реквизитам."
        ),
        parse_mode="Markdown",
    )
    if callback.message.caption:
      await callback.message.edit_caption(
          caption=callback.message.caption
          + "\n\n🟢 **СТАТУС: Подтверждено оператором**",
          reply_markup=None,
      )
    else:
      await callback.message.edit_text(
          text=callback.message.text
          + "\n\n🟢 **СТАТУС: Подтверждено оператором**",
          reply_markup=None,
      )
    await callback.answer("Сделка подтверждена!")
  else:
    await callback.bot.send_message(
        chat_id=target_user_id,
        text=(
            f"❌ **Ваша сделка `{deal_id}` была отклонена оператором.** Обратитесь"
            " в поддержку."
        ),
        parse_mode="Markdown",
    )
    if callback.message.caption:
      await callback.message.edit_caption(
          caption=callback.message.caption
          + "\n\n🔴 **СТАТУС: Отклонено**",
          reply_markup=None,
      )
    else:
      await callback.message.edit_text(
          text=callback.message.text + "\n\n🔴 **СТАТУС: Отклонено**",
          reply_markup=None,
      )
    await callback.answer("Сделка отклонена.")


async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)
  await bot.delete_webhook(drop_pending_updates=True)
  print("Бот запущен и готов к работе!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
