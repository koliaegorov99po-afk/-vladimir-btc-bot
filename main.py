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
OPERATOR_ID = 8974638307  # Оператор также доступен как @VLADIMIR_BTC_MD

WELCOME_PHOTO_URL = "https://i.postimg.cc/nVytVm20/202-3.jpg"

logging.basicConfig(level=logging.INFO)
router = Router()


class ExchangeState(StatesGroup):
  direction = State()  # buy_crypto or sell_crypto
  currency = State()
  payment_method = State()
  waiting_for_amount = State()
  waiting_for_receipt = State()


# Получение актуальных курсов с Binance
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
                  text="🟢 Купить криптовалюту", callback_data="dir_buy"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔴 Продать криптовалюту", callback_data="dir_sell"
              )
          ],
      ]
  )

  welcome_text = (
      "👋 **Добро пожаловать в официальный обменный сервис @VLADIMIR_BTC_MD!**\n\n"
      "⚡️ Быстрый, безопасный и надежный обмен фиатных средств и"
      " криптовалюты.\n"
      "💼 Работаем с рублями РФ, ПМР и молдавскими леями через удобные"
      " направления.\n\n"
      "👇 Выберите необходимую операцию ниже:"
  )

  try:
    await message.answer_photo(
        photo=WELCOME_PHOTO_URL, caption=welcome_text, reply_markup=kb, parse_mode="Markdown"
    )
  except Exception:
    await message.answer(welcome_text, reply_markup=kb, parse_mode="Markdown")


# --- ВЕТКА ПОКУПКИ КРИПТЫ ---
@router.callback_query(F.data == "dir_buy")
async def process_buy_menu(callback: CallbackQuery, state: FSMContext):
  await state.update_data(direction="buy")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔷 USDT (TRC-20)", callback_data="buy_cur_USDT_TRC20"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔷 USDT (BEP-20)", callback_data="buy_cur_USDT_BEP20"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔷 USDT (TON)", callback_data="buy_cur_USDT_TON"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🪙 Bitcoin (BTC)", callback_data="buy_cur_BTC"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🪙 Litecoin (LTC)", callback_data="buy_cur_LTC"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🪙 TRON (TRX)", callback_data="buy_cur_TRON"
              )
          ],
      ]
  )
  await callback.message.answer(
      "🟢 **Покупка криптовалюты**\nВыберите актив, который хотите купить:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@router.callback_query(F.data.startswith("buy_cur_"))
async def process_buy_currency(callback: CallbackQuery, state: FSMContext):
  currency = callback.data.replace("buy_cur_", "")
  await state.update_data(currency=currency)

  # Отдельные кнопки для каждого способа оплаты при покупке
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🇷🇺 Рубли РФ (СБП — Сбер/Т-Банк/ВТБ)",
                  callback_data="pay_RUB_SBP",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💳 Рубли ПМР (Эксим / Переводилка)",
                  callback_data="pay_PMR",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🧮 Леи МД (Paynet / MIA)", callback_data="pay_MDL_PAYNET"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🧮 Леи МД (Рун Пай / MIA)", callback_data="pay_MDL_RUNPAY"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🧮 Леи МД (MAIB - Marina Russ)",
                  callback_data="pay_MDL_MAIB",
              )
          ],
      ]
  )
  await callback.message.answer(
      f"💳 Вы выбрали покупку **{currency}**.\nВыберите способ оплаты (фиат):",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


# --- ВЕТКА ПРОДАЖИ КРИПТЫ ---
@router.callback_query(F.data == "dir_sell")
async def process_sell_menu(callback: CallbackQuery, state: FSMContext):
  await state.update_data(direction="sell")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔷 USDT (TRC-20)", callback_data="sell_cur_USDT_TRC20"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔷 USDT (BEP-20)", callback_data="sell_cur_USDT_BEP20"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔷 USDT (TON)", callback_data="sell_cur_USDT_TON"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🪙 Bitcoin (BTC)", callback_data="sell_cur_BTC"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🪙 Litecoin (LTC)", callback_data="sell_cur_LTC"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🪙 TRON (TRX)", callback_data="sell_cur_TRX"
              )
          ],
      ]
  )
  await callback.message.answer(
      "🔴 **Продажа криптовалюты**\nВыберите актив, который хотите продать:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@router.callback_query(F.data.startswith("sell_cur_"))
async def process_sell_currency(callback: CallbackQuery, state: FSMContext):
  currency = callback.data.replace("sell_cur_", "")
  await state.update_data(currency=currency)

  await callback.message.answer(
      f"✍️ Вы выбрали продажу **{currency}**.\nВведите сумму криптовалюты для"
      " продажи (цифрами):",
      parse_mode="Markdown",
  )
  await state.set_state(ExchangeState.waiting_for_amount)
  await callback.answer()


@router.callback_query(F.data.startswith("pay_"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
  pay_method = callback.data.replace("pay_", "")
  await state.update_data(payment_method=pay_method)

  await callback.message.answer(
      "✍️ Введите сумму в фиате, которую хотите обменять (цифрами):",
      parse_mode="Markdown",
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
          "🏦 **Банк:** Сбербанк / Т-Банк / ВТБ\n"
          "📱 **Номер телефона / СБП:** `+79019727196`\n"
      )
    elif "PMR" in pay_method:
      usd_amount = amount / 19.0
      calc_details = f"Сумма: {amount} ПМР руб\nКурс: 1$ = 19 ПМР"
      requisites = (
          "📌 **Реквизиты для оплаты (ПМР):**\n"
          "🏦 **ЭКСИМ / ПЕРЕВОДИЛКА**\n"
          "🔢 **Счет / Номер:** `77507411`\n"
      )
    elif "MDL" in pay_method:
      usd_amount = amount / 21.0
      calc_details = f"Сумма: {amount} MDL\nКурс: 1$ = 21 MDL"
      if "PAYNET" in pay_method or "RUNPAY" in pay_method:
        requisites = (
            "📌 **Реквизиты для оплаты (Леи МД — Paynet / RunPay / MIA):**\n"
            "📱 **Номер:** `068728340`\n"
        )
      elif "MAIB" in pay_method:
        requisites = (
            "📌 **Реквизиты для оплаты (MAIB):**\n"
            "👤 **Получатель:** Marina Russ\n"
            "💳 **Счет / Карта:** `4356960081341247`\n"
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
        "⚠️ **Важно:** После оплаты обязательно отправьте в чат **скриншот чека"
        "** или **хеш транзакции** для подтверждения оператором."
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
    elif "TRC20" in currency or "TRX" in currency:
      crypto_wallet = "`TELVh3pvb2HKcL2fd6UQFwfBEEs7m3mi6v`"
    elif "BTC" in currency:
      crypto_wallet = "`3AvgzeSvUh5MXz9QSuyRwBDjLDAmsp7Z8M`"
    elif "TON" in currency:
      crypto_wallet = "`UQCVdkthxRGvHJV68mLfcGYuHYfL_2sWZVylZIGBVl7cZElX`"
    else:
      crypto_wallet = "`Адрес уточняйте у оператора @VLADIMIR_BTC_MD`"

    text = (
        f"🧮 **Расчет продажи крипты:**\n"
        f"🪙 Сумма крипты: `{crypto_amount} {currency}`\n"
        f"💵 Эквивалент в USD: `${usd_amount:.2f}`\n\n"
        "💰 **Вы получите по курсу:**\n"
        f"• Рубли РФ (72р за 1$): **{rub_rf:.2f} RUB**\n"
        f"• Рубли ПМР (16р за 1$): **{pmr_rub:.2f} ПМР**\n"
        f"• Леи МД (17 лей за 1$): **{mdl_lei:.2f} MDL**\n\n"
        "📌 **Переведите криптовалюту на наш кошелек:**\n"
        f"{crypto_wallet}\n\n"
        "⚠️ **Важно:** После перевода отправьте **хеш транзакции** или"
        " **скриншот** оператору через этот чат."
    )
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(ExchangeState.waiting_for_receipt)


@router.message(ExchangeState.waiting_for_receipt)
async def receive_receipt(message: Message, state: FSMContext):
  data = await state.get_data()
  user = message.from_user

  deal_id = f"DEAL-{user.id}-{message.message_id}"
  photo_id = message.photo[-1].file_id if message.photo else None
  text_content = message.caption or message.text or "Скриншот без текста"

  operator_caption = (
      f"🚨 **Новая заявка на обмен!**\n"
      f"🆔 Номер сделки: `{deal_id}`\n"
      f"👤 Пользователь: @{user.username} (ID: `{user.id}`)\n"
      f"🔄 Направление: {data.get('direction')}\n"
      f"🪙 Валюта: {data.get('currency')}\n"
      f"💵 Сумма: {data.get('amount')}\n"
      f"📄 Чек / Хеш от клиента: {text_content}\n"
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

  # Пересылка чека / скрина / хеша напрямую оператору в личный чат (@VLADIMIR_BTC_MD)
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
      f"✅ Чек/хеш успешно принят! Номер вашей сделки: `{deal_id}`.\nОператор"
      " (@VLADIMIR_BTC_MD) проверяет платеж, ожидания подтверждения.",
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
            " оператором!**\nСредства / криптовалюта успешно отправлены по"
            " вашим реквизитам. Спасибо за доверие к @VLADIMIR_BTC_MD!"
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
            f"❌ **Ваша сделка `{deal_id}` отклонена оператором.** Обратитесь в"
            " поддержку @VLADIMIR_BTC_MD."
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
