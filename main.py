import asyncio
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================
API_TOKEN = "8624564680:AAGy8J2IEwJV_lm1mSSR2-eauAmeg5lJWtY"
ADMIN_ID = 8725569658
CHANNEL = "@dev_spacce"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS categories(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS words(id INTEGER PRIMARY KEY AUTOINCREMENT, category_id INTEGER, word TEXT, date TEXT)")
conn.commit()

# ================= STATES =================
class AdminState(StatesGroup):
    add_category = State()
    add_word_text = State()
    ads = State()

# ================= SUB CHECK =================
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= KEYBOARDS =================
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📚 Bo‘limlar", callback_data="show_categories")
    kb.button(text="🔄 Yangilash", callback_data="refresh")
    if ADMIN_ID:
        kb.button(text="⚙️ Admin panel", callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()

def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Bo‘lim", callback_data="add_cat")
    kb.button(text="🗑 O‘chirish", callback_data="del_cat")
    kb.button(text="📝 So‘z", callback_data="add_word")
    kb.button(text="📢 Reklama", callback_data="ads")
    kb.button(text="👥 Statistika", callback_data="users")
    kb.button(text="🏠 Asosiy menu", callback_data="back_main")
    kb.adjust(2)
    return kb.as_markup()

def back_admin():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Admin panel", callback_data="admin_panel")
    return kb.as_markup()

# ================= START =================
@dp.message(CommandStart())
async def start(message: Message):
    cursor.execute("INSERT OR IGNORE INTO users VALUES(?,?)",
                   (message.from_user.id, message.from_user.username))
    conn.commit()

    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardBuilder()
        kb.button(text="📢 Kanal", url=f"https://t.me/{CHANNEL.replace('@','')}")
        kb.button(text="✅ Tekshirish", callback_data="check_sub")
        kb.adjust(1)
        return await message.answer("🚫 Kanalga obuna bo‘ling!", reply_markup=kb.as_markup())

    if message.from_user.id == ADMIN_ID:
        return await message.answer("⚙️ Admin panel", reply_markup=admin_menu())

    await message.answer("Bu bot orqali ingliz 🇬🇧, koreys 🇰🇷 va boshqa tillardagi so‘z boyligingizni oson va tez oshirishingiz mumkin 🚀", reply_markup=main_menu())

# ================= ADMIN PANEL =================
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ Ruxsat Bu tugma Adminlar uchun", show_alert=True)

    await call.message.edit_text("⚙️ Admin panel", reply_markup=admin_menu())

# ================= REFRESH =================
@dp.callback_query(F.data == "refresh")
async def refresh(call: CallbackQuery):
    await call.message.edit_text("🔄 Yangilandi", reply_markup=main_menu())

# ================= CHECK SUB =================
@dp.callback_query(F.data == "check_sub")
async def check(call: CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.edit_text("✅ Tasdiqlandi!\n\n Bu bot orqali ingliz 🇬🇧, koreys 🇰🇷 va boshqa tillardagi so‘z boyligingizni oson va tez oshirishingiz mumkin 🚀", reply_markup=main_menu())
    else:
        await call.answer("❌ Obuna yo‘q", show_alert=True)

# ================= CATEGORIES =================
@dp.callback_query(F.data == "show_categories")
async def categories(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    cursor.execute("SELECT * FROM categories")
    cats = cursor.fetchall()

    if not cats:
        return await call.message.edit_text("❌ Bo‘lim yo‘q", reply_markup=main_menu())

    for c in cats:
        kb.button(text=c[1], callback_data=f"cat_{c[0]}")

    kb.button(text="🔙 Ortga", callback_data="back_main")
    kb.adjust(2)

    await call.message.edit_text("📂 Bo‘lim tanlang:", reply_markup=kb.as_markup())

# ================= WORDS =================
@dp.callback_query(F.data.startswith("cat_"))
async def words(call: CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT word FROM words WHERE category_id=? AND date=?", (cat_id, today))
    words = cursor.fetchall()

    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Bo‘limlar", callback_data="show_categories")

    if not words:
        return await call.message.edit_text("❌ Bugun so‘z yo‘q", reply_markup=kb.as_markup())

    text = "📚 Bugungi so‘zlar:\n\n"
    for w in words:
        text += f"🔹 {w[0]}\n"

    await call.message.edit_text(text, reply_markup=kb.as_markup())

# ================= BACK MAIN =================
@dp.callback_query(F.data == "back_main")
async def back(call: CallbackQuery):
    await call.message.edit_text("🏠 Asosiy menu", reply_markup=main_menu())

# ================= ADD CATEGORY =================
@dp.callback_query(F.data == "add_cat")
async def add_cat(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_category)
    await call.message.edit_text("➕ Bo‘lim nomini yozing:", reply_markup=back_admin())

@dp.message(AdminState.add_category)
async def save_cat(message: Message, state: FSMContext):
    try:
        cursor.execute("INSERT INTO categories(name) VALUES(?)", (message.text,))
        conn.commit()
        await message.answer("✅ Qo‘shildi", reply_markup=admin_menu())
    except:
        await message.answer("⚠️ Bu bo‘lim mavjud", reply_markup=admin_menu())
    await state.clear()

# ================= DELETE =================
@dp.callback_query(F.data == "del_cat")
async def del_cat(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    cursor.execute("SELECT * FROM categories")
    for c in cursor.fetchall():
        kb.button(text=f"❌ {c[1]}", callback_data=f"del_{c[0]}")

    kb.button(text="🔙 Admin", callback_data="admin_panel")
    await call.message.edit_text("🗑 O‘chirish:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("del_"))
async def delete(call: CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    cursor.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    await call.answer("O‘chirildi", show_alert=True)
    await admin_panel(call)

# ================= ADD WORD =================
@dp.callback_query(F.data == "add_word")
async def add_word(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    cursor.execute("SELECT * FROM categories")
    for c in cursor.fetchall():
        kb.button(text=c[1], callback_data=f"w_{c[0]}")

    kb.button(text="🔙 Admin", callback_data="admin_panel")
    await call.message.edit_text("📚 Bo‘lim tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("w_"))
async def write(call: CallbackQuery, state: FSMContext):
    await state.update_data(cat_id=int(call.data.split("_")[1]))
    await state.set_state(AdminState.add_word_text)
    await call.message.edit_text("✍️ So‘z yozing:", reply_markup=back_admin())

@dp.message(AdminState.add_word_text)
async def save_word(message: Message, state: FSMContext):
    data = await state.get_data()
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        "INSERT INTO words(category_id,word,date) VALUES(?,?,?)",
        (data["cat_id"], message.text, today)
    )
    conn.commit()

    await message.answer("✅ Saqlandi", reply_markup=admin_menu())
    await state.clear()

# ================= ADS =================
@dp.callback_query(F.data == "ads")
async def ads(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.ads)
    await call.message.edit_text("📢 Reklama matnini yozing:", reply_markup=back_admin())

@dp.message(AdminState.ads)
async def send_ads(message: Message, state: FSMContext):
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            await bot.send_message(u[0], message.text)
            await asyncio.sleep(0.02)
        except:
            pass

    await state.clear()
    await message.answer("✅ Yuborildi", reply_markup=admin_menu())

# ================= USERS =================
@dp.callback_query(F.data == "users")
async def users(call: CallbackQuery):
    cursor.execute("SELECT * FROM users")
    count = len(cursor.fetchall())
    await call.message.edit_text(f"👥 Userlar soni: {count}", reply_markup=admin_menu())

# ================= RUN =================
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())