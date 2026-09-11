import asyncio
import logging
import os
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
from aiohttp import web

# Токен и ID оператора
TOKEN = "8616697712:AAHeF6EDbZYld2l-St6qxSpGQTu7-zSNNHY"
OPERATOR_ID = 8974638307

WELCOME_PHOTO_URL = (
    "https://i.postimg.cc/NMQ2Yp4z/file-00000000f2cc8210a8520b37b3885c4c.png"
)

logging.basicConfig(level=logging.INFO)
router = Router()


class ExchangeState(StatesGroup):
  direction = State()
  currency = State()
  payment_method = State()
  waiting_for_amount = State()
  waiting_for_receipt = State()


async def get_binance_prices():
  prices = {"BTC": 90000.0, "LTC": 100.0, "TRX": 0.25, "USDT": 1.0, "TON": 5.0}
  try:
    async with aiohttp.ClientSession() as session:
      async with session.get(
          "https://api.binance.com/api/v3/ticker/price", timeout=5
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
      "👋 <b>Добро пожаловать в официальный обменный сервис @VLADIMIR_BTC_MD!</b>\n\n"
      "⚡️ Быстрый, безопасный и надежный обмен фиатных средств и"
      " криптовалюты.\n"
      "💼 Работаем с рублями РФ, ПМР и молдавскими леями.\n\n"
      "👇 Выберите необходимую операцию ниже:"
  )

  try:
    await message.answer_photo(
        photo=WELCOME_PHOTO_URL,
        caption=welcome_text,
        reply_markup=kb,
        parse_mode="HTML",
    )
  except Exception:
    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")


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
      "🟢 <b>Покупка криптовалюты</b>\nВыберите актив, который хотите купить:",
      reply_markup=kb,
      parse_mode="HTML",
  )
  await callback.answer()


@router.callback_query(F.data.startswith("buy_cur_"))
async def process_buy_currency(callback: CallbackQuery, state: FSMContext):
  currency = callback.data.replace("buy_cur_", "")
  await state.update_data(currency=currency)

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
      f"💳 Вы выбрали покупку <b>{currency}</b>.\nВыберите способ оплаты"
      " (фиат):",
      reply_markup=kb,
      parse_mode="HTML",
  )
  await callback.answer()


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
      "🔴 <b>Продажа криптовалюты</b>\nВыберите актив, который хотите продать:",
      reply_markup=kb,
      parse_mode="HTML",
  )
  await callback.answer()


@router.callback_query(F.data.startswith("sell_cur_"))
async def process_sell_currency(callback: CallbackQuery, state: FSMContext):
  currency = callback.data.replace("sell_cur_", "")
  await state.update_data(currency=currency)

  await callback.message.answer(
      f"✍️ Вы выбрали продажу <b>{currency}</b>.\nВведите сумму криптовалюты"
      " для продажи (цифрами):",
      parse_mode="HTML",
  )
  await state.set_state(ExchangeState.waiting_for_amount)
  await callback.answer()


@router.callback_query(F.data.startswith("pay_"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
  pay_method = callback.data.replace("pay_", "")
  await state.update_data(payment_method=pay_method)

  await callback.message.answer(
      "✍️ Введите сумму в фиате, которую хотите обменять (цифрами):",
      parse_mode="HTML",
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

  try:
    await state.update_data(amount=amount)
    data = await state.get_data()
    direction = data.get("direction", "buy")
    currency = data.get("currency", "USDT_TRC20")
    prices = await get_binance_prices()

    base_coin = currency.split("_")[0]
    coin_price_usd = prices.get(base_coin, 1.0)

    calc_details = ""
    requisites = ""

    if direction == "buy":
      pay_method = data.get("payment_method", "RUB_SBP")
      usd_amount = 0

      if "RUB" in pay_method:
        usd_amount = amount / 100.0
        calc_details = f"Сумма: {amount} RUB\nКурс: 1$ = 100 RUB"
        requisites = (
            "📌 <b>Реквизиты для оплаты (Рубли РФ СБП):</b>\n"
            "🏦 <b>Банк:</b> Сбербанк / Т-Банк / ВТБ\n"
            "📱 <b>Номер телефона / СБП:</b> <code>+79019727196</code>\n"
        )
      elif "PMR" in pay_method:
        usd_amount = amount / 19.0
        calc_details = f"Сумма: {amount} ПМР руб\nКурс: 1$ = 19 ПМР"
        requisites = (
            "📌 <b>Реквизиты для оплаты (ПМР):</b>\n"
            "🏦 <b>ЭКСИМ / ПЕРЕВОДИЛКА</b>\n"
            "🔢 <b>Счет / Номер:</b> <code>77507411</code>\n"
        )
      elif "MDL" in pay_method:
        usd_amount = amount / 21.0
        calc_details = f"Сумма: {amount} MDL\nКурс: 1$ = 21 MDL"
        if "PAYNET" in pay_method or "RUNPAY" in pay_method:
          requisites = (
              "📌 <b>Реквизиты для оплаты (Леи МД — Paynet / RunPay /"
              " MIA):</b>\n"
              "📱 <b>Номер:</b> <code>068728340</code>\n"
          )
        elif "MAIB" in pay_method:
          requisites = (
              "📌 <b>Реквизиты для оплаты (MAIB):</b>\n"
              "👤 <b>Получатель:</b> Marina Russ\n"
              "💳 <b>Счет / Карта:</b> <code>4356960081341247</code>\n"
          )
        else:
          requisites = (
              "📌 <b>Реквизиты для оплаты (Леи МД):</b>\n"
              "📱 <b>Номер / Счет:</b> <code>068728340</code> или"
              " <code>4356960081341247</code> (MAIB)\n"
          )

      crypto_amount = usd_amount / coin_price_usd if coin_price_usd > 0 else 0
      await state.update_data(
          calculated_crypto=crypto_amount, usd_amount=usd_amount
      )

      text = (
          f"🧮 <b>Расчет обмена:</b>\n{calc_details}\n"
          f"💵 Эквивалент в USD: <b>${usd_amount:.2f}</b>\n"
          f"🪙 Получите криптовалюту ({currency}):"
          f" <code>{crypto_amount:.6f}</code>\n\n"
          f"{requisites}\n"
          "⚠️ <b>Важно:</b> После оплаты обязательно отправьте в чат"
          " <b>скриншот чека</b> или <b>хеш транзакции</b> для подтверждения"
          " оператором."
      )
      await message.answer(text, parse_mode="HTML")
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
        crypto_wallet = "<code>ltc1qkprk223v0hjc36g2dlysmtlgqdzrtp48xwvwja</code>"
      elif "BEP20" in currency:
        crypto_wallet = "<code>0x89b28d58ce3e521a920d6b8f008841c3cd3d5747</code>"
      elif "TRC20" in currency or "TRX" in currency:
        crypto_wallet = "<code>TELVh3pvb2HKcL2fd6UQFwfBEEs7m3mi6v</code>"
      elif "BTC" in currency:
        crypto_wallet = "<code>3AvgzeSvUh5MXz9QSuyRwBDjLDAmsp7Z8M</code>"
      elif "TON" in currency:
        crypto_wallet = (
            "<code>UQCVdkthxRGvHJV68mLfcGYuHYfL_2sWZVylZIGBVl7cZElX</code>"
        )
      else:
        crypto_wallet = (
            "<code>Адрес уточняйте у оператора @VLADIMIR_BTC_MD</code>"
        )

      text = (
          f"🧮 <b>Расчет продажи крипты:</b>\n"
          f"🪙 Сумма крипты: <code>{crypto_amount} {currency}</code>\n"
          f"💵 Эквивалент в USD: <b>${usd_amount:.2f}</b>\n\n"
          "💰 <b>Вы получите по курсу:</b>\n"
          f"• Рубли РФ (72р за 1$): <b>{rub_rf:.2f} RUB</b>\n"
          f"• Рубли ПМР (16р за 1$): <b>{pmr_rub:.2f} ПМР</b>\n"
          f"• Леи МД (17 лей за 1$): <b>{mdl_lei:.2f} MDL</b>\n\n"
          "📌 <b>Переведите криптовалюту на наш кошелек:</b>\n"
          f"{crypto_wallet}\n\n"
          "⚠️ <b>Важно:</b> После перевода отправьте <b>хеш транзакции</b> или"
          " <b>скриншот</b> оператору через этот чат."
      )
      await message.answer(text, parse_mode="HTML")
      await state.set_state(ExchangeState.waiting_for_receipt)

  except Exception as e:
    logging.error(f"Ошибка в receive_amount: {e}")
    await message.answer(
        "❌ Произошла ошибка при расчете. Начните заново с помощью команды /start"
    )
    await state.clear()


@router.message(ExchangeState.waiting_for_receipt)
async def receive_receipt(message: Message, state: FSMContext):
  try:
    data = await state.get_data()
    user = message.from_user

    deal_id = f"DEAL-{user.id}-{message.message_id}"
    photo_id = message.photo[-1].file_id if message.photo else None
    text_content = message.caption or message.text or "Скриншот без текста"

    operator_caption = (
        f"🚨 <b>Новая заявка на обмен!</b>\n"
        f"🆔 Номер сделки: <code>{deal_id}</code>\n"
        f"👤 Пользователь: @{user.username} (ID: <code>{user.id}</code>)\n"
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

    if photo_id:
      await message.bot.send_photo(
          chat_id=OPERATOR_ID,
          photo=photo_id,
          caption=operator_caption,
          reply_markup=kb_operator,
          parse_mode="HTML",
      )
    else:
      await message.bot.send_message(
          chat_id=OPERATOR_ID,
          text=operator_caption,
          reply_markup=kb_operator,
          parse_mode="HTML",
      )

    await message.answer(
        f"✅ Чек/хеш успешно принят! Номер вашей сделки: <code>{deal_id}</code>.\nОператор"
        " (@VLADIMIR_BTC_MD) проверяет платеж, ожидайте подтверждения.",
        parse_mode="HTML",
    )
    await state.clear()
  except Exception as e:
    logging.error(f"Ошибка в receive_receipt: {e}")
    await message.answer(
        "❌ Произошла ошибка при отправке чека оператору. Попробуйте еще раз"
        " или нажмите /start"
    )


@router.callback_query(F.data.startswith("op_"))
async def operator_action(callback: CallbackQuery):
  try:
    parts = callback.data.split("_")
    action = parts[1]
    target_user_id = int(parts[2])
    deal_id = parts[3]

    if action == "approve":
      await callback.bot.send_message(
          chat_id=target_user_id,
          text=(
              f"✅ <b>Ваша сделка <code>{deal_id}</code> успешно подтверждена"
              " оператором!</b>\nСредства / криптовалюта успешно отправлены по"
              " вашим реквизитам. Спасибо за доверие к @VLADIMIR_BTC_MD!"
          ),
          parse_mode="HTML",
      )
      if callback.message.caption:
        await callback.message.edit_caption(
            caption=callback.message.caption
            + "\n\n🟢 <b>СТАТУС: Подтверждено оператором</b>",
            reply_markup=None,
        )
      else:
        await callback.message.edit_text(
            text=callback.message.text
            + "\n\n🟢 <b>СТАТУС: Подтверждено оператором</b>",
            reply_markup=None,
        )
      await callback.answer("Сделка подтверждена!")
    else:
      await callback.bot.send_message(
          chat_id=target_user_id,
          text=(
              f"❌ <b>Ваша сделка <code>{deal_id}</code> отклонена оператором.</b> Обратитесь в"
              " поддержку @VLADIMIR_BTC_MD."
          ),
          parse_mode="HTML",
      )
      if callback.message.caption:
        await callback.message.edit_caption(
            caption=callback.message.caption
            + "\n\n🔴 <b>СТАТУС: Отклонено</b>",
            reply_markup=None,
        )
      else:
        await callback.message.edit_text(
            text=callback.message.text + "\n\n🔴 <b>СТАТУС: Отклонено</b>",
            reply_markup=None,
        )
      await callback.answer("Сделка отклонена.")
  except Exception as e:
    logging.error(f"Ошибка в operator_action: {e}")
    await callback.answer("Произошла ошибка при обработке действия.")


# --- Веб-сервер для поддержки активности на Render ---
async def handle(request):
  return web.Response(text="Bot is alive and running!")


async def start_web_server():
  app = web.Application()
  app.router.add_get("/", handle)
  runner = web.AppRunner(app)
  await runner.setup()
  port = int(os.environ.get("PORT", 10000))
  site = web.TCPSite(runner, "0.0.0.0", port)
  await site.start()
  logging.info(f"Веб-сервер запущен на порту {port}")


async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)
  await bot.delete_webhook(drop_pending_updates=True)

  print("Бот и веб-сервер запущены!")

  # Одновременный запуск веб-сервера и опроса Telegram
  await asyncio.gather(start_web_server(), dp.start_polling(bot))


if __name__ == "__main__":
  asyncio.run(main())
