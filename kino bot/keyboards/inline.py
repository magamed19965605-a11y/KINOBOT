from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_subscription_keyboard(unsubscribed_tg_channels, external_channels):
    """
    Kanallar ro'yxati asosida a'zolik tugmalarini yaratadi.
    """
    builder = InlineKeyboardBuilder()
    
    # Telegram kanallar
    for channel in unsubscribed_tg_channels:
        builder.button(text="➕ Obuna bo'lish", url=channel["url"])
        
    # Instagram va YouTube linklar
    for ext in external_channels:
        builder.button(text="➕ Obuna bo'lish", url=ext["url"])
    
    # Tekshirish va Premium tugmalari
    builder.button(text="✅ Tekshirish", callback_data="check_subscription")
    builder.button(text="💎 Premium", callback_data="show_premium")
    
    builder.adjust(1)
    return builder.as_markup()

def profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎫 Limit sotib olish", callback_data="buy_limit")
    builder.button(text="💎 Premium (Cheksiz)", callback_data="show_premium")
    builder.button(text="💰 Balans to'ldirish", callback_data="top_up_balance")
    builder.button(text="👨‍💻 Adminga murojaat", callback_data="contact_admin")
    builder.adjust(1)
    return builder.as_markup()

def premium_plans_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="1 oylik obuna - 15 000 so'm", callback_data="select_prem_1")
    builder.button(text="3 oylik obuna - 35 000 so'm", callback_data="select_prem_3")
    builder.button(text="1 yillik obuna - 65 000 so'm", callback_data="select_prem_12")
    builder.button(text="⬅️ Orqaga", callback_data="show_profile")
    builder.adjust(1)
    return builder.as_markup()

def premium_payment_keyboard(months):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔹 Avto-to'lov (Payme, Click)", callback_data=f"method_prem_{months}_auto")
    builder.button(text="Har qanday o'tkazmalar uchun", callback_data=f"method_prem_{months}_manual")
    builder.button(text="⬅️ Orqaga", callback_data="show_premium")
    builder.adjust(1)
    return builder.as_markup()

def premium_confirm_keyboard(months, method):
    builder = InlineKeyboardBuilder()
    if method == "auto":
        builder.button(text="💳 To'lovni amalga oshirish", callback_data=f"buy_prem_{months}_auto")
    else:
        builder.button(text="📸 To'lov chekini yuborish", callback_data=f"send_screenshot_{months}")
    builder.button(text="⬅️ Orqaga", callback_data=f"select_prem_{months}")
    builder.adjust(1)
    return builder.as_markup()

def admin_approval_keyboard(app_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ruxsat berish", callback_data=f"approve_app_{app_id}")
    builder.button(text="❌ Rad etish", callback_data=f"reject_app_{app_id}")
    builder.adjust(2)
    return builder.as_markup()

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data="admin_stats")
    builder.button(text="➕ Kino/Multfilm qo'shish", callback_data="admin_add_movie")
    builder.button(text="➕ Majburiy kanal qo'shish", callback_data="admin_add_channel")
    builder.button(text="🗑 Kino/Multfilm o'chirish", callback_data="admin_del_movie")
    builder.button(text="🗑 Kanal o'chirish", callback_data="admin_del_channel")
    builder.button(text="💰 Balans/Limit berish", callback_data="admin_add_balance")
    builder.adjust(2)
    return builder.as_markup()

def admin_customers_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🌟 Premium foydalanuvchilar", callback_data="admin_list_premium")
    builder.button(text="⏳ Muddati tugaganlar", callback_data="admin_list_expired")
    builder.button(text="👥 Barcha foydalanuvchilar", callback_data="admin_list_users_0")
    builder.button(text="⬅️ Orqaga", callback_data="admin_main")
    builder.adjust(1)
    return builder.as_markup()

def admin_user_list_keyboard(users, page, total_pages, list_type):
    builder = InlineKeyboardBuilder()
    for user in users:
        # user: (id, tg_id, name, ...)
        builder.button(text=f"{user[2]} (ID: {user[1]})", callback_data=f"admin_view_user_{user[1]}")
    
    # Navigation buttons
    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_list_{list_type}_{page-1}"))
    if page < total_pages - 1:
        nav_btns.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_list_{list_type}_{page+1}"))
    
    if nav_btns:
        builder.row(*nav_btns)
        
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_customers"))
    builder.adjust(1)
    return builder.as_markup()

def admin_user_manage_keyboard(user_id, is_premium):
    builder = InlineKeyboardBuilder()
    # Manual tugmalar olib tashlandi, endi faqat komandalar qo'llaniladi
    builder.button(text="⬅️ Ro'yxatga qaytish", callback_data="admin_list_users_0")
    builder.adjust(1)
    return builder.as_markup()

def admin_limit_give_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="+5 (5000 so'm)", callback_data=f"admin_set_limit_{user_id}_5")
    builder.button(text="+10 (10000 so'm)", callback_data=f"admin_set_limit_{user_id}_10")
    builder.button(text="+50 (50000 so'm)", callback_data=f"admin_set_limit_{user_id}_50")
    builder.button(text="⬅️ Orqaga", callback_data=f"admin_view_user_{user_id}")
    builder.adjust(1)
    return builder.as_markup()

def admin_balance_manage_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Umumiy tushum", callback_data="admin_total_income")
    builder.button(text="📅 Bugungi tushum", callback_data="admin_daily_income")
    builder.button(text="📜 Sotib olganlar ro'yxati", callback_data="admin_purchased_list")
    builder.button(text="⬅️ Orqaga", callback_data="admin_main")
    builder.adjust(1)
    return builder.as_markup()
