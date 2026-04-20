from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import database
import aiosqlite
from config import ADMINS, MOVIE_CHANNEL, TELEGRAM_CHANNELS
from keyboards.reply import admin_reply_keyboard
from keyboards.inline import (
    admin_approval_keyboard,
    admin_customers_menu,
    admin_user_list_keyboard,
    admin_user_manage_keyboard,
    admin_limit_give_keyboard,
    admin_balance_manage_menu
)

admin_router = Router()

class MovieState(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_del_code = State()

class ChannelState(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_url = State()
    waiting_for_name = State()
    waiting_for_del_id = State()

class AdminState(StatesGroup):
    viewing_applications = State()

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id in ADMINS:
        return await message.answer("Tizimga xush kelibsiz, Admin!", reply_markup=admin_reply_keyboard())

@admin_router.message(F.text == "📊 Statistika")
async def process_admin_stats(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.clear()
        try:
            total_users, active_today, total_requests = await database.get_statistics()
            
            text = (
                f"📊 <b>Umumiy statistika</b>\n\n"
                f"👥 Barcha foydalanuvchilar: <b>{total_users}</b> ta\n"
                f"🟢 Oxirgi 24 soatda faol: <b>{active_today}</b> ta\n"
                f"🎬 Jami ko'rilgan kinolar: <b>{total_requests}</b> marta\n"
            )
            await message.answer(text, parse_mode="HTML")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")



@admin_router.message(F.text == "💰 Balans boshqaruvi")
async def process_admin_balance_menu(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.clear()
        text = (
            "💰 <b>Balans va Statistika boshqaruvi</b>\n\n"
            "Pastdagi tugmalar orqali kerakli ma'lumotlarni ko'rishingiz mumkin."
        )
        await message.answer(text, parse_mode="HTML", reply_markup=admin_balance_manage_menu())

@admin_router.callback_query(F.data == "admin_total_income")
async def process_admin_total_income(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        from config import ADMIN_CARD, ADMIN_CARD_NAME
        _, _, total_income = await database.get_extended_statistics()
        text = (
            "💰 <b>Umumiy tushum ma'lumotlari</b>\n\n"
            f"📊 Jami tushgan mablag': <b>{total_income:,}</b> so'm\n\n"
            f"💳 Karta: <code>{ADMIN_CARD}</code>\n"
            f"👤 Egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
            "<i>Ushbu summa tasdiqlangan barcha to'lovlar yig'indisidir.</i>"
        )
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_balance_manage_menu())
        await call.answer()

@admin_router.callback_query(F.data == "admin_daily_income")
async def process_admin_daily_income(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        from config import ADMIN_CARD, ADMIN_CARD_NAME
        _, daily_income, _ = await database.get_extended_statistics()
        text = (
            "📅 <b>Bugungi tushum ma'lumotlari</b>\n\n"
            f"📊 Bugungi tushgan mablag': <b>{daily_income:,}</b> so'm\n\n"
            f"💳 Karta: <code>{ADMIN_CARD}</code>\n"
            f"👤 Egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
            "<i>Ushbu summa bugun tasdiqlangan to'lovlar yig'indisidir.</i>"
        )
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_balance_manage_menu())
        await call.answer()

@admin_router.callback_query(F.data == "admin_purchased_list")
async def process_admin_purchased_list(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        apps = await database.get_approved_applications()
        if not apps:
            return await call.answer("Hozircha sotib olganlar yo'q!", show_alert=True)
        
        text = "📜 <b>Sotib olganlar ro'yxati (Oxirgi 30 tasi):</b>\n\n"
        for i, app in enumerate(apps[:30], 1):
            # app: (id, user_id, full_name, photo_id, plan_months, app_type, amount, status, created_at)
            type_text = "💎 Prem" if app[5] == 'PREMIUM' else "💰 Balans"
            amount_text = f"{app[6]:,} so'm" if app[5] == 'BALANCE' else f"{app[4]} oy"
            text += f"{i}. {app[2]} (<code>{app[1]}</code>) - <b>{amount_text}</b> ({type_text})\n"
        
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_balance_manage_menu())
        await call.answer()

# --- Asosiy Menyu Tugmalari (Priority) ---

@admin_router.message(F.text == "👥 Mijozlar")
async def admin_customers_start(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.clear()
        await message.answer(
            "👥 <b>Mijozlar boshqaruvi bo'limi</b>\n\nPastdagi menyu orqali kerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=admin_customers_menu()
        )

@admin_router.message(F.text == "📩 Murojaatlar")
async def view_applications_handler(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.clear()
        apps = await database.get_pending_applications()
        if not apps:
            return await message.answer("📩 Hozircha yangi murojaatlar (to'lov cheklari) yo'q.")
        
        await message.answer(f"📩 Jami {len(apps)} ta kutilayotgan murojaat bor. Birinchisini ko'rsataman:")
        
        app = apps[0]
        type_text = "💎 PREMIUM" if app[5] == 'PREMIUM' else "💰 BALANS"
        amount_text = f"{app[6]:,} so'm" if app[5] == 'BALANCE' else f"{app[4]} oylik"
        
        await message.answer_photo(
            app[3], 
            caption=(
                f"📩 <b>Yangi murojaat!</b>\n\n"
                f"👤 Foydalanuvchi: {app[2]}\n"
                f"🆔 ID: <code>{app[1]}</code>\n"
                f"📂 Turi: <b>{type_text}</b>\n"
                f"💵 Miqdori: <b>{amount_text}</b>\n"
                f"📅 Sana: {app[8]}\n\n"
                f"Tasdiqlaysizmi?"
            ),
            parse_mode="HTML",
            reply_markup=admin_approval_keyboard(app[0])
        )

@admin_router.message(F.text == "➕ Majburiy kanal qo'shish")
async def add_channel_start(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id in ADMINS:
        await state.clear()
        channels = await database.get_channels()
        text = "📋 <b>Hozirgi barcha ulangan majburiy kanallar:</b>\n"
        idx = 1
        for ch in channels:
            text += f"▪️ {ch[3]} <i>(ID: {ch[1]})</i>\n"
            idx += 1
        if idx == 1:
            text += "<i>Hozircha bot orqali hech qanday kanal qo'shilmagan.</i>\n"
        text += "\n<b>Yangi kanal qo'shish so'rovi:</b>\n1. Botni kanalingizga Admin qiling.\n2. Username yoki havolasini yuboring."
        await message.answer(text, parse_mode="HTML")
        await state.set_state(ChannelState.waiting_for_channel_id)

@admin_router.message(F.text == "🗑 Kanal o'chirish")
async def delete_channel_start(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.clear()
        channels = await database.get_channels()
        kb_buttons = []
        for ch in channels:
            kb_buttons.append([InlineKeyboardButton(text=f"🗑 {ch[3]}", callback_data=f"del_chan_{ch[1]}")])
        if not kb_buttons:
            return await message.answer("Yo'q.")
        await message.answer("Tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

@admin_router.message(F.text == "➕ Kino/Multfilm qo'shish")
async def add_movie_start(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.clear()
        await message.answer("Kinoni yuboring:")
        await state.set_state(MovieState.waiting_for_video)

@admin_router.message(F.text == "🗑 Kino/Multfilm o'chirish")
async def delete_movie_start(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.clear()
        await message.answer("Kodni yozing:")
        await state.set_state(MovieState.waiting_for_del_code)

# --- Qidiruv va boshqa amallar ---

@admin_router.message(Command("balans"))
async def cmd_add_balance(message: Message):
    if message.from_user.id in ADMINS:
        try:
            parts = message.text.split()
            if len(parts) == 3:
                target_id = int(parts[1])
                amount = int(parts[2])
                await database.update_user_balance(target_id, amount)
                await message.answer(f"✅ {target_id} foydalanuvchiga {amount} hisobiga qo'shildi.")
            else:
                await message.answer("Xato format. /balans ID SUMMA\nMasalan: /balans 123456 10000")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")

@admin_router.message(Command("limit"))
async def cmd_add_limit(message: Message):
    if message.from_user.id in ADMINS:
        try:
            parts = message.text.split()
            if len(parts) == 3:
                target_id = int(parts[1])
                lim = int(parts[2])
                await database.update_limit(target_id, lim)
                await message.answer(f"✅ {target_id} foydalanuvchiga limit: {lim} o'rnatildi.")
            else:
                await message.answer("Xato format. /limit ID SONI\nMasalan: /limit 123456 50")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")

@admin_router.message(Command("premium"))
async def cmd_set_premium(message: Message):
    if message.from_user.id in ADMINS:
        try:
            parts = message.text.split()
            if len(parts) == 3:
                target_id = int(parts[1])
                status = parts[2] == "1"
                await database.set_premium(target_id, status)
                await message.answer(f"✅ {target_id} foydalanuvchi premium holati: {'YOQILDI' if status else 'OCHIRILDI'}")
            else:
                await message.answer("Xato format. /premium ID 1 (yoqish) yoki 0 (ochirish)")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")

@admin_router.message(Command("user"))
async def cmd_check_user(message: Message):
    if message.from_user.id in ADMINS:
        try:
            parts = message.text.split()
            if len(parts) == 2:
                target_id = int(parts[1])
                user = await database.get_user(target_id)
                if user:
                    premium_st = "Bor" if user[6] else "Yo'q"
                    text = (
                        f"👤 <b>Foydalanuvchi ma'lumotlari:</b>\n\n"
                        f"🆔 ID: <code>{user[1]}</code>\n"
                        f"👤 Nomi: {user[2]}\n"
                        f"💰 Balansi: <b>{user[4]:,}</b> so'm\n"
                        f"🔢 Limiti: <b>{user[5]}</b> ta\n"
                        f"⭐ Premium: <b>{premium_st}</b>\n"
                        f"📅 Qo'shilgan: {user[7]}\n"
                        f"🕒 Oxirgi faollik: {user[8]}\n"
                        f"🎬 So'rovlar soni: {user[9]}\n"
                    )
                    await message.answer(text, parse_mode="HTML")
                else:
                    await message.answer("❌ Foydalanuvchi topilmadi.")
            else:
                await message.answer("Xato format. /user ID")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")

@admin_router.callback_query(F.data == "admin_customers")
async def admin_customers_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        await call.message.edit_text(
            "👥 <b>Mijozlar boshqaruvi bo'limi</b>\n\nPastdagi menyu orqali kerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=admin_customers_menu()
        )

@admin_router.callback_query(F.data == "admin_main")
async def admin_main_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        await call.message.edit_text("Asosiy admin paneli uchun reply tugmalardan foydalaning.")

@admin_router.callback_query(F.data.startswith("admin_list_"))
async def admin_list_users_handler(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        parts = call.data.split("_")
        list_type = parts[2]
        page = int(parts[3]) if len(parts) > 3 else 0
        limit = 10
        offset = page * limit
        
        users, total = [], 0
        title = ""
        
        if list_type == "premium":
            users_all = await database.get_active_premiums()
            total = len(users_all)
            users = users_all[offset:offset+limit]
            title = "🌟 <b>Aktiv premium foydalanuvchilar:</b>"
        elif list_type == "expired":
            users_all = await database.get_expired_premiums()
            total = len(users_all)
            users = users_all[offset:offset+limit]
            title = "⏳ <b>Muddati tugagan premiumlar:</b>"
        else:
            users_list, total_count = await database.get_users_paged(offset, limit)
            users = users_list
            total = total_count
            title = "👥 <b>Barcha foydalanuvchilar:</b>"
            
        if not users and page == 0:
            return await call.answer("Ro'yxat bo'sh!", show_alert=True)
            
        total_pages = max(1, (total + limit - 1) // limit)
        await call.message.edit_text(
            f"{title}\n\nJami: {total} ta\nSahifa: {page + 1}/{total_pages}",
            parse_mode="HTML",
            reply_markup=admin_user_list_keyboard(users, page, total_pages, list_type)
        )

@admin_router.callback_query(F.data.startswith("admin_view_user_"))
async def admin_view_user_handler(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        user_id = int(call.data.split("_")[3])
        user = await database.get_user(user_id)
        if not user:
            return await call.answer("Foydalanuvchi topilmadi!", show_alert=True)
            
        premium_status = "✅ Ha" if user[6] else "❌ Yo'q"
        text = (
            f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
            f"🆔 ID: <code>{user[1]}</code>\n"
            f"👤 Ism: {user[2]}\n"
            f"💰 Balans: <b>{user[4]:,}</b> so'm\n"
            f"🔢 Limit: <b>{user[5]}</b> ta\n\n"
            f"💎 Premium: <b>{premium_status}</b>\n"
        )
        if user[6]:
            expiry_val = str(user[8]) if user[8] else "Noaniq"
            expiry_show = expiry_val.split('.')[0]
            text += f"📅 Tugash muddati: <code>{expiry_show}</code>\n"
            
        text += f"\n📅 Qo'shilgan sana: {str(user[9]).split('.')[0]}\n"
        text += f"🎬 Ko'rilgan kinolar: {user[11]} ta"
        
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_user_manage_keyboard(user[1], user[6]))

@admin_router.callback_query(F.data.startswith("admin_give_limit_"))
async def admin_give_limit_handler(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        user_id = int(call.data.split("_")[3])
        await call.message.edit_text(
            f"🔢 <b>{user_id}</b> uchun limit miqdorini tanlang:",
            reply_markup=admin_limit_give_keyboard(user_id)
        )

@admin_router.callback_query(F.data.startswith("admin_set_limit_"))
async def admin_set_limit_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        parts = call.data.split("_")
        user_id = int(parts[3])
        amount = int(parts[4])
        
        async with aiosqlite.connect(database.DB_NAME) as db:
            await db.execute("UPDATE users SET limit_count = limit_count + ? WHERE telegram_id = ?", (amount, user_id))
            await db.commit()
            
        await call.answer(f"✅ {amount} ta limit qo'shildi!", show_alert=True)
        await admin_view_user_handler(call)

@admin_router.callback_query(F.data.startswith("admin_toggle_prem_"))
async def admin_toggle_prem_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        parts = call.data.split("_")
        user_id = int(parts[3])
        status = parts[4] == "1"
        
        await database.set_premium(user_id, status)
        await call.answer(f"✅ Premium status: {'Yoqildi' if status else 'Ochirdildi'}", show_alert=True)
        await admin_view_user_handler(call)

@admin_router.callback_query(F.data.startswith("approve_app_"))
async def approve_payment(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id in ADMINS:
        app_id = int(callback.data.split("_")[2])
        app = await database.get_application(app_id)
        if app:
            user_id = app[1]
            app_type = app[5]
            amount = app[6]
            months = app[4]
            
            if app_type == 'PREMIUM':
                days = months * 30 if months < 12 else 365
                await database.set_premium(user_id, True, days)
                user_info = await database.get_user(user_id)
                expiry = user_info[8]
                plan_text = f"{months} oylik" if months < 12 else "1 yillik"
                notify_text = f"🎊 <b>Tabriklaymiz!</b>\n\nSizning to'lovingiz tasdiqlandi. Premium status <b>{plan_text}</b>ga faollashtirildi.\n📅 Amal qilish muddati: {expiry.split('.')[0]} gacha."
                summary_text = f"✅ <b>TASDIQLANDI (Premium {plan_text})</b>"
            else:
                await database.update_user_balance(user_id, amount)
                notify_text = f"✅ <b>Tabriklaymiz!</b>\n\nSizning to'lovingiz tasdiqlandi. Balansingizga <b>{amount:,} so'm</b> qo'shildi."
                summary_text = f"✅ <b>TASDIQLANDI (Balans +{amount:,})</b>"
            
            await database.update_application_status(app_id, 'APPROVED')
            
            try:
                await bot.send_message(user_id, notify_text, parse_mode="HTML")
            except Exception as e:
                print(f"Error sending msg to user: {e}")
            
            await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n{summary_text}", parse_mode="HTML")
        await callback.answer("Tasdiqlandi!")

@admin_router.callback_query(F.data.startswith("reject_app_"))
async def reject_payment(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id in ADMINS:
        app_id = int(callback.data.split("_")[2])
        app = await database.get_application(app_id)
        if app:
            await database.update_application_status(app_id, 'REJECTED')
            try:
                await bot.send_message(app[1], "❌ Kechirasiz, siz yuborgan to'lov cheki rad etildi. Iltimos adminga murojaat qiling.")
            except:
                pass
            await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n❌ <b>RAD ETILDI</b>", parse_mode="HTML")
        await callback.answer("Rad etildi!")

@admin_router.message(ChannelState.waiting_for_channel_id)
async def process_channel_id(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id in ADMINS:
        text = message.text.strip()
        try:
            chat = await bot.get_chat(text)
            channel_id = chat.id
            name = chat.title or "Kanal"
            url = f"https://t.me/{chat.username}" if chat.username else None
            if url:
                await database.add_channel(channel_id, url, name)
                await message.answer(f"✅ {name} kanali qo'shildi!")
                await state.clear()
            else:
                await state.update_data(channel_id=channel_id, name=name)
                await message.answer(f"Kanal yopiq. Ssilkasini yuboring:")
                await state.set_state(ChannelState.waiting_for_url)
        except:
            await message.answer("Topilmadi.")

@admin_router.message(ChannelState.waiting_for_url)
async def process_channel_url(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        url = message.text
        data = await state.get_data()
        await database.add_channel(data['channel_id'], url, data['name'])
        await message.answer("✅ Saqlandi!")
        await state.clear()

@admin_router.callback_query(F.data.startswith("del_chan_"))
async def process_delete_channel_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        ch_id = int(call.data.split("_")[2])
        await database.remove_channel(ch_id)
        await call.answer("O'childi")
        await call.message.delete()

@admin_router.message(MovieState.waiting_for_video)
async def process_video(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        file_id = None
        if message.video: file_id = message.video.file_id
        elif message.document: file_id = message.document.file_id
        if not file_id: return await message.answer("Fayl yuboring.")
        await state.update_data(file_id=file_id)
        await message.answer("Kodini yozing:")
        await state.set_state(MovieState.waiting_for_code)

@admin_router.message(MovieState.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.update_data(code=message.text)
        await message.answer("Nomini yozing:")
        await state.set_state(MovieState.waiting_for_title)

@admin_router.message(MovieState.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        data = await state.get_data()
        await database.add_movie(data['code'], message.text, "kino", data['file_id'])
        await message.answer("✅ Saqlandi!")
        await state.clear()

@admin_router.message(F.text == "🗑 Kino/Multfilm o'chirish")
async def delete_movie_start(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await state.clear()
        await message.answer("Kodni yozing:")
        await state.set_state(MovieState.waiting_for_del_code)

@admin_router.message(MovieState.waiting_for_del_code)
async def process_delete_movie(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await database.delete_movie(message.text)
        await message.answer("✅ O'chirildi!")
        await state.clear()
