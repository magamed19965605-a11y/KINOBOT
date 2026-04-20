from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter

import database
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
import time
import random

class UserState(StatesGroup):
    waiting_for_screenshot = State()
    waiting_for_search_query = State()
from keyboards.inline import profile_keyboard, admin_approval_keyboard
from keyboards.reply import main_reply_keyboard
from config import LIMIT_PRICE, ADMINS, LOGO_PATH, PAYMENT_LINKS

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message):
    # Foydalanuvchini bazaga qo'shamiz
    await database.add_user(message.from_user.id, message.from_user.full_name)
    
    # Agar admin bo'lsa, unga admin menyusini chiqaramiz
    if message.from_user.id in ADMINS:
        from keyboards.reply import admin_reply_keyboard
        await message.answer(
            f"Salom, Admin {message.from_user.full_name}!\nAdministratsiya paneliga xush kelibsiz.", 
            reply_markup=admin_reply_keyboard()
        )
        return

    # Oddiy foydalanuvchi uchun welcome xabari
    welcome_text = (
        "🎬 <b>CINEMA_uz90_bot — Sevimli kinolaringiz markazi!</b>\n\n"
        "Bu bot orqali siz:\n"
        "🔹 Eng so'nggi dunyo premyera kinolarni;\n"
        "🔹 Sevimli va qiziqarli multifilmlarni;\n"
        "🔹 O'zbek tilidagi sifatli filmlarni tomosha qilishingiz mumkin.\n\n"
        "🍿 <b>Botga obuna bo'ling va eng sara kontentlardan bahramand bo'ling!</b>\n\n"
        "📢 Rasmiy kanal: @CINEMA_uz90\n"
        "👤 Admin: @XONaction\n\n"
        "👇 <b>Botni davom ettirish uchun kanaldagi kino kodini yuboring!</b>"
    )
    try:
        logo = FSInputFile(LOGO_PATH)
        await message.answer_photo(logo, caption=welcome_text, parse_mode="HTML", reply_markup=main_reply_keyboard())
    except:
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_reply_keyboard())

@user_router.message(F.text == "👤 Profil")
async def cmd_profile(message: Message, state: FSMContext):
    await state.clear()
    # Foydalanuvchini bazada borligini ta'minlaymiz (Xatolikni oldini olish uchun)
    await database.add_user(message.from_user.id, message.from_user.full_name)
    user = await database.get_user(message.from_user.id)
    if not user:
        return await message.answer("Siz haqingizda ma'lumot topilmadi.")
    
    # uid, tg_id, fname, addr, balance, l_count, is_prem, prem_start, prem_end, join_date, last_active, req_count = user
    uid, tg_id, fname, addr, balance, l_count, is_prem, p_start, p_end, join_date, last_active, req_count = user
    
    from config import LIMIT
    prem_text = "Faol ✅" if is_prem else "Mavjud emas ❌"
    
    if is_prem and p_end:
        prem_text += f"\n📅 Tugash muddati: {p_end.split('.')[0]}"

    profile_text = (f"👤 <b>Mening profilim</b>\n\n"
            f"🆔 ID: <code>{tg_id}</code>\n"
            f"👤 Ism: {fname}\n"
            f"💰 Balans: <b>{balance:,}</b> so'm\n"
            f"🎬 Kino qoldig'i: <b>{l_count if not is_prem else 'Cheksiz (Premium)'}</b>\n"
            f"💎 Premium holati: <b>{prem_text}</b>\n\n"
            f"🎁 Kunlik bepul limit: <b>{LIMIT}</b> ta\n"
            f"<i>Limitni ko'paytirish yoki Premium sotib olish uchun pastdagi tugmalardan foydalaning.</i>")
    
    try:
        logo = FSInputFile(LOGO_PATH)
        await message.answer_photo(logo, caption=profile_text, parse_mode="HTML", reply_markup=profile_keyboard())
    except:
        await message.answer(profile_text, parse_mode="HTML", reply_markup=profile_keyboard())

@user_router.message(F.text == "💰 Balans")
async def cmd_balance(message: Message, state: FSMContext):
    await state.clear()
    # Foydalanuvchini bazada borligini ta'minlaymiz
    await database.add_user(message.from_user.id, message.from_user.full_name)
    user = await database.get_user(message.from_user.id)
    if not user:
        return await message.answer("Siz haqingizda ma'lumot topilmadi.")
    
    # uid, tg_id, fname, addr, balance, l_count, is_prem, ...
    balance = user[4]
    spent = await database.get_user_spent_amount(message.from_user.id)
    
    text = (f"💰 <b>Sizning balansingiz:</b>\n\n"
            f"💵 Mavjud mablag': <b>{balance:,}</b> so'm\n"
            f"📉 Jami sarflangan mablag': <b>{spent:,}</b> so'm\n\n"
            f"<i>Balansni to'ldirish uchun '👤 Profil' bo'limiga o'ting.</i>")
    
    try:
        logo = FSInputFile(LOGO_PATH)
        await message.answer_photo(logo, caption=text, parse_mode="HTML")
    except:
        await message.answer(text, parse_mode="HTML")

@user_router.message(F.text == "🎬 Kino/Multfilm izlash")
async def cmd_search_start(message: Message, state: FSMContext):
    await message.answer("🎬 <b>Kino kodini yoki nomini yuboring:</b>\n\nMasalan: <code>113</code>", parse_mode="HTML")
    await state.set_state(UserState.waiting_for_search_query)

@user_router.message(F.text == "✍️ Adminga murojaat")
async def cmd_contact_admin(message: Message):
    from config import ADMIN_USER
    await message.answer(f"🆘 Muammo yuzaga kelsa yoki balansni to'ldirmoqchi bo'lsangiz, adminga yozing: {ADMIN_USER}")

@user_router.callback_query(F.data == "contact_admin")
async def callback_contact_admin(callback: CallbackQuery):
    from config import ADMIN_USER
    await callback.message.answer(f"🆘 Adminga murojaat: {ADMIN_USER}")
    await callback.answer()

@user_router.callback_query(F.data == "show_premium")
async def process_show_premium(callback: CallbackQuery):
    from keyboards.inline import premium_plans_keyboard
    text = (
        "💎 <b>Premium obuna</b>\n\n"
        "Premium orqali quyidagilarga ega bo'lasiz:\n"
        "• Kanallarga obuna bo'lmasdan kino ko'rish\n"
        "• Reklamasiz foydalanish\n"
        "• Yuqori sifatda tomosha qilish\n\n"
        "📋 <b>Quyidagi tariflardan birini tanlang:</b>"
    )
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=premium_plans_keyboard())
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=premium_plans_keyboard())
    await callback.answer()

@user_router.callback_query(F.data.startswith("select_prem_"))
async def process_select_plan(callback: CallbackQuery):
    months = int(callback.data.split("_")[2])
    from keyboards.inline import premium_payment_keyboard
    
    # Tarif ma'lumotlari
    prices = {1: 15000, 3: 35000, 12: 65000}
    price = prices.get(months, 15000)
    days = months * 30 if months < 12 else 365
    name = f"{months} oylik obuna" if months < 12 else "1 yillik obuna"
    
    text = (
        "💳 <b>To'lov tizimini tanlang</b>\n\n"
        f"💎 Tarif: {name}\n"
        f"📅 Muddat: {days} kun\n"
        f"💰 Narx: {price:,} so'm"
    )
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=premium_payment_keyboard(months))
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=premium_payment_keyboard(months))
    await callback.answer()

@user_router.callback_query(F.data.startswith("method_prem_"))
async def process_payment_method(callback: CallbackQuery):
    parts = callback.data.split("_")
    months = int(parts[2])
    method = parts[3]
    from keyboards.inline import premium_confirm_keyboard
    from config import ADMIN_CARD, ADMIN_CARD_NAME
    
    prices = {1: 15000, 3: 35000, 12: 65000}
    price = prices.get(months, 15000)
    days = months * 30 if months < 12 else 365
    name = f"{months} oylik obuna" if months < 12 else "1 yillik obuna"

    if method == "auto":
        text = (
            "💎 <b>PREMIUM OBUNA — TO'LOV MA'LUMOTLARI</b>\n\n"
            f"📦 Tarif: {name}\n"
            f"💰 To'lov summasi: {price:,} so'm\n\n"
            "✅ To'lov muvaffaqiyatli amalga oshirilgach, premium obuna avtomatik tarzda faollashtiriladi.\n\n"
            "👇 <b>To'lovni davom ettirish uchun quyidagi tugmani bosing:</b>"
        )
    else:
        text = (
            "💎 <b>PREMIUM — To'lov ma'lumotlari</b>\n\n"
            f"📦 Tarif: {name}\n"
            f"📅 Muddat: {days} kun\n"
            f"💰 Narx: {price:,} so'm\n"
            f"🏢 Tizim: Har qanday o'tkazmalar uchun\n"
            f"💳 Karta: <code>{ADMIN_CARD}</code>\n"
            f"👤 Egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
            "❗ <b>Chekni rasm sifatida yuboring.</b>"
        )
    
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=premium_confirm_keyboard(months, method))
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=premium_confirm_keyboard(months, method))
    await callback.answer()

@user_router.callback_query(F.data.startswith("send_screenshot_"))
async def process_send_screenshot_tiered(callback: CallbackQuery, state: FSMContext):
    months = int(callback.data.split("_")[2])
    await state.update_data(selected_months=months)
    await callback.message.answer("📸 Iltimos, to'lov chekini (rasm ko'rinishida) yuboring:")
    await state.set_state(UserState.waiting_for_screenshot)
    await callback.answer()

@user_router.callback_query(F.data.startswith("buy_prem_"))
async def process_buy_premium_tiered(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    months = int(parts[2])
    
    prices = {1: 15000, 3: 35000, 12: 65000}
    price = prices.get(months, 15000)
    days = months * 30 if months < 12 else 365

    user = await database.get_user(callback.from_user.id)
    balance = user[4]
    
    if user[6]: # Is premium
        await callback.message.answer("💎 Sizda premium allaqachon faollashtirilgan!")
        await callback.answer()
        return

    if balance >= price:
        await database.update_user_balance(callback.from_user.id, -price)
        await database.set_premium(callback.from_user.id, True, days=days)
        await callback.message.answer(f"🎊 Tabriklaymiz! Siz {months} oylik Premium foydalanuvchiga aylandingiz. Endi barcha kinolar siz uchun cheksiz!")
        from config import BOT_NAME
        # 100% noyob order_id (User ID + Timestamp)
        order_id = f"{callback.from_user.id}_{int(time.time())}"
        await state.update_data(app_type='PREMIUM', selected_months=months, amount=price)
        
        base_url = PAYMENT_LINKS.get(price, PAYMENT_LINKS.get(15000))
        # Safopay linkiga barcha mumkin bo'lgan parametrlarni qo'shamiz (Redundant parameters)
        # Bu '0 so'm' muammosini hal qilish uchun maksimal darajadagi harakat
        params = {
            "amount": int(price),
            "sum": int(price),
            "total": int(price),
            "price": int(price),
            "amount_tiyin": int(price) * 100, # Ba'zi tizimlar tiyin kutadi
            "order_id": order_id,
            "transaction_id": order_id,
            "label": order_id,
            "comment": BOT_NAME,
            "info": BOT_NAME,
            "name": BOT_NAME
        }
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        pay_url = f"{base_url}?{query_string}"
        
        text = (
            f"❌ <b>Balansingizda mablag' yetarli emas.</b>\n\n"
            f"📦 Buyurtma ID: <b>#{order_id}</b>\n"
            f"💰 To'lov miqdori: <b>{price:,} so'm</b>\n"
            f"🔄 Holat: <b>To'lov jarayonida...</b>\n\n"
            f"Siz avtomatik to'lov tizimi (Safopay) orqali yoki karta orqali to'lov qilishingiz mumkin."
        )
        
        from keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Safopay orqali (Avto)", url=pay_url)],
            [InlineKeyboardButton(text="💰 Karta orqali (Manual)", callback_data="top_up_balance")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_profile")]
        ])
        
        try:
            logo = FSInputFile(LOGO_PATH)
            await callback.message.answer_photo(logo, caption=text, parse_mode="HTML", reply_markup=kb)
        except:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@user_router.callback_query(F.data == "show_profile")
async def callback_show_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await cmd_profile(callback.message, state)
    await callback.answer()

@user_router.callback_query(F.data == "buy_limit")
async def process_buy_limit(callback: CallbackQuery):
    user = await database.get_user(callback.from_user.id)
    balance = user[4]
    
    if balance >= LIMIT_PRICE:
        await database.update_user_balance(callback.from_user.id, -LIMIT_PRICE)
        await database.update_limit(callback.from_user.id, user[5] + 5)
        if callback.message.photo:
            await callback.message.edit_caption(caption="✅ Siz 5 ta kino/multfilm kuchi sotib oldingiz!")
        else:
            await callback.message.edit_text("✅ Siz 5 ta kino/multfilm kuchi sotib oldingiz!")
    else:
        from keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="top_up_balance")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_profile")]
        ])
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=f"❌ <b>Balansingizda mablag' yetarli emas.</b>\n\nLimit (5 ta) narxi: <b>{LIMIT_PRICE:,}</b> so'm.\nSizning balansingiz: <b>{balance:,}</b> so'm.",
                parse_mode="HTML",
                reply_markup=kb
            )
        else:
            await callback.message.edit_text(
                text=f"❌ <b>Balansingizda mablag' yetarli emas.</b>\n\nLimit (5 ta) narxi: <b>{LIMIT_PRICE:,}</b> so'm.\nSizning balansingiz: <b>{balance:,}</b> so'm.",
                parse_mode="HTML",
                reply_markup=kb
            )
    await callback.answer()

@user_router.callback_query(F.data == "top_up_balance")
async def process_top_up(callback: CallbackQuery, state: FSMContext):
    from config import ADMIN_CARD, ADMIN_CARD_NAME
    from keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton
    
    data = await state.get_data()
    amount = data.get('amount', LIMIT_PRICE)
    
    # Noyob order_id manual to'lov uchun ham
    order_id = f"{callback.from_user.id}_{int(time.time())}"
    
    text = (
        "💰 <b>Balansni to'ldirish (Manual)</b>\n\n"
        f"📦 Buyurtma ID: <b>#{order_id}</b>\n"
        f"💰 To'lov summasi: <b>{amount:,} so'm</b>\n\n"
        "To'lov qilish uchun quyidagi kartaga mablag' o'tkazing:\n\n"
        f"💳 Karta: <code>{ADMIN_CARD}</code>\n"
        f"👤 Egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
        f"☝️ <b>Muhim:</b> To'lovning izohiga (comment) <code>{order_id}</code> raqamini yozsangiz, tasdiqlash tezroq bo'ladi.\n\n"
        "⚠️ To'lov qilganingizdan so'ng, '📸 Chekni yuborish' tugmasini bosing va chekni yuboring."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Chekni yuborish", callback_data="send_screenshot")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_profile")]
    ])
    
    logo = FSInputFile(LOGO_PATH)
    try:
        await callback.message.answer_photo(logo, caption=text, parse_mode="HTML", reply_markup=kb)
    except:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@user_router.callback_query(F.data == "send_screenshot")
async def process_send_screenshot_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Iltimos, to'lov chekini (rasm ko'rinishida) yuboring:")
    await state.set_state(UserState.waiting_for_screenshot)
    await callback.answer()

@user_router.message(UserState.waiting_for_screenshot, F.photo)
async def process_screenshot_received(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    app_type = data.get("app_type", "PREMIUM")
    months = data.get("selected_months", 1)
    amount = data.get("amount", 0)
    photo_id = message.photo[-1].file_id
    
    app_id = await database.add_application(
        user_id=message.from_user.id, 
        full_name=message.from_user.full_name, 
        photo_id=photo_id, 
        plan_months=months,
        app_type=app_type,
        amount=amount
    )
    await state.clear()
    
    await message.answer("✅ <b>Chek qabul qilindi!</b>\nAdmin tasdiqlashi bilan sizga xabar yuboramiz.")
    
    # Adminga xabar yuborish
    from config import ADMINS
    for admin_id in ADMINS:
        try:
            type_text = "💎 PREMIUM" if app_type == 'PREMIUM' else "💰 BALANS"
            await bot.send_photo(
                admin_id,
                photo=photo_id,
                caption=f"📩 <b>Yangi to'lov cheki!</b>\n\n👤 Foydalanuvchi: {message.from_user.full_name}\n🆔 ID: <code>{message.from_user.id}</code>\n📂 Turi: <b>{type_text}</b>\n💵 Summa/Tarif: <b>{amount:,} so'm / {months} oy</b>\n\nTasdiqlaysizmi?",
                parse_mode="HTML",
                reply_markup=admin_approval_keyboard(app_id=app_id)
            )
        except Exception as e:
            print(f"Admin notify error: {e}")
            pass
    await state.clear()

@user_router.message(UserState.waiting_for_search_query)
async def process_search_query(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    await search_handler(message, bot)


@user_router.message(StateFilter(None))
async def search_handler(message: Message, bot: Bot):
    if not message.text:
        return

    query = message.text.strip()
    
    # Buyruqlarni tekshirish
    if query.startswith("/"):
        if query.startswith("/kod_"):
            # /kod_ buyruqlari har doim ishlashi kerak (bu natijalardan keladi)
            pass 
        elif message.from_user.id in ADMINS:
            return await message.answer(f"❌ Noma'lum buyruq: {query}")
        else:
            return await message.answer("❌ Noma'lum buyruq. Kino izlash uchun kod yoki nom yuboring.")
    else:
        # AGAR TEXT BO'LSA VA STATE BO'LMASA:
        # Foydalanuvchiga avval tugmani bosishni aytamiz
        return await message.answer("⚠️ <b>Kino izlash uchun avval pastdagi '🎬 Kino/Multfilm izlash' tugmasini bosing!</b>", parse_mode="HTML")
    
    # /kod_ bo'lsa davom etadi
    user = await database.get_user(message.from_user.id)
    is_admin = message.from_user.id in ADMINS
    if not user:
        await database.add_user(message.from_user.id, message.from_user.full_name)
        user = await database.get_user(message.from_user.id)
    
    l_count = user[5]
    is_prem = user[6]
    
    if not is_prem and l_count <= 0 and not is_admin:
        return await message.answer("❌ Kechirasiz, sizda bepul kino olish limiti tugadi. /profile orqali limit sotib oling yoki VIP (Premium) raqamga o'ting.")
    
    if query.startswith("/kod_"):
        query = query.replace("/kod_", "")

    if query.isdigit():
        movie = await database.get_movie(query)
        if movie:
            await send_movie_response(message, bot, movie, is_admin)
        else:
            await message.answer("❌ bunday kodli kino botda mavjud emas.")
    else:
        # Nomi orqali qidirish
        movies = await database.search_movie_by_title(query)
        if len(movies) == 1:
            await send_movie_response(message, bot, movies[0], is_admin)
        elif len(movies) > 1:
            text = "🔎 Topilgan natijalar:\n\n"
            for m in movies:
                text += f"🎬 {m[2]} - /kod_{m[1]}\n"
            text += "\nKo'rish uchun /kod_RAQAMI ni bosing."
            await message.answer(text)
        else:
            await message.answer("❌ Bunday nomdagi kino topilmadi.")

async def send_movie_response(message: Message, bot: Bot, movie, is_admin: bool):
    await database.update_user_activity(message.from_user.id)
    code, title, m_type, file_id = movie[1], movie[2], movie[3], movie[4]
    
    if file_id.startswith("channel_"):
        msg_id = int(file_id.split("_")[1])
        try:
            from config import MOVIE_CHANNEL
            await bot.copy_message(chat_id=message.chat.id, from_chat_id=MOVIE_CHANNEL, message_id=msg_id)
            if not is_admin:
                from config import MOVIE_COST
                await database.decrement_limit(message.from_user.id, MOVIE_COST)
        except Exception as e:
            await message.answer("❌ Ushbu kino kanaldan o'chirilgan yoki topilmadi.")
    else:
        caption = f"🎬 Nomi: {title}\n🔢 Kodi: {code}\n🎞 Turi: {m_type}"
        try:
            # Video ekanligini sinab ko'ramiz
            await message.answer_video(video=file_id, caption=caption)
            if not is_admin:
                from config import MOVIE_COST
                await database.decrement_limit(message.from_user.id, MOVIE_COST)
        except Exception:
            try:
                # Yoki document ekanligini sinaymiz
                await message.answer_document(document=file_id, caption=caption)
                if not is_admin:
                    from config import MOVIE_COST
                    await database.decrement_limit(message.from_user.id, MOVIE_COST)
            except:
                try: # Rasm ekanligini sinayamiz
                    await message.answer_photo(photo=file_id, caption=caption)
                    if not is_admin:
                        from config import MOVIE_COST
                        await database.decrement_limit(message.from_user.id, MOVIE_COST)
                except Exception as e:
                    await message.answer(f"Fayl yuborishda xatolik: {e}")
