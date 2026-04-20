from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.exceptions import TelegramBadRequest

import database
from keyboards.inline import get_subscription_keyboard
from config import ADMINS

verified_external_users = set()

class CheckSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        # Adminlar obuna tekshiruvidan ozod
        if user_id in ADMINS:
            return await handler(event, data)

        # Premium foydalanuvchilar obuna tekshiruvidan ozod
        user_data = await database.get_user(user_id)
        if user_data and user_data[6]: # is_premium
            return await handler(event, data)

        bot = data['bot']
        
        db_channels = await database.get_channels()
        all_channels = []
        all_ext_channels = []
        for ch in db_channels:
            c_id = ch[1]
            c_url = ch[2]
            c_name = ch[3]
            
            if c_id < 0: # Telegram kanali
                all_channels.append({
                    "chat_id": c_id,
                    "url": c_url,
                    "name": c_name
                })
            else: # Tashqi link
                all_ext_channels.append({
                    "url": c_url,
                    "name": c_name
                })
        
        unsubscribed_channels = []
        for channel in all_channels:
            try:
                member_info = await bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
                if member_info.status not in ["member", "administrator", "creator"]:
                    unsubscribed_channels.append(channel)
            except Exception:
                # Agar bot kanalda admin bo'lmasa, uni majburiy deb hisoblaymiz (foydalanuvchi kira olmasligi uchun)
                unsubscribed_channels.append(channel)

        # Agar obuna bo'lmagan kanallar bo'lsa yoki tashqi kanallar hali "bosilmagan" bo'lsa
        if unsubscribed_channels or (all_ext_channels and user_id not in verified_external_users):
            keyboard = get_subscription_keyboard(unsubscribed_channels, all_ext_channels)
            text = (
                "❌ <b>Kechirasiz, botimizdan foydalanish uchun ushbu kanallarga obuna bo'lishingiz kerak.</b>\n\n"
                "💎 Premium obuna sotib olib, kanallarga obuna bo'lmasdan foydalanishingiz mumkin."
            )
            
            if isinstance(event, CallbackQuery) and event.data == "check_subscription":
                if unsubscribed_channels:
                    await event.answer("⚠️ Siz hali hamma kanallarga a'zo bo'lmadingiz!", show_alert=True)
                    # Xabarni yangilash (agar birortasiga a'zo bo'lgan bo'lsa ro'yxat qisqaradi)
                    try:
                        await event.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                    except:
                        pass
                else:
                    # Telegram kanallar OK, demak tashqi kanallar verified qilinadi
                    verified_external_users.add(user_id)
                    await self._show_welcome(event)
                return

            if isinstance(event, Message):
                await event.answer(text, parse_mode="HTML", reply_markup=keyboard)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
                await event.answer()
            return

        # Tekshirish tugmasi bosilganda va hamma narsa OK bo'lsa
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            await self._show_welcome(event)
            return

        return await handler(event, data)

    async def _show_welcome(self, event: CallbackQuery):
        try:
            await event.message.delete()
        except:
            pass
            
        welcome_text = (
            "🎬 <b>CINEMA_uz90_bot — Sevimli kinolaringiz markazi!</b>\n\n"
            "Bu bot orqali siz:\n"
            "🔹 Eng so'nggi dunyo premyera kinolarni;\n"
            "🔹 Sevimli va qiziqarli multifilmlarni;\n"
            "🔹 O'zbek tilidagi sifatli filmlarni tomosha qilishingiz mumkin.\n\n"
            "📢 Rasmiy kanal: @CINEMA_uz90\n"
            "👤 Admin: @XONaction\n\n"
            "🚀 <b>Qani boshladik! Botni davom ettirish uchun kanaldagi kino kodini yuboring.</b>"
        )
        await event.message.answer(welcome_text, parse_mode="HTML")
        await event.answer("Muvaffaqiyatli tekshirildi!")
