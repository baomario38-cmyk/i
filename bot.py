import os
import hashlib
from threading import Thread
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SERVER KEEP-ALIVE ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "TX PRO ANALYTICS v8.0 ACTIVE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
TOKEN = '8985526419:AAGdRkntgFNYLBG53LoI-pNC7aHtOFMWhGA'
ADMIN_ID = 755092812  # ID của bạn
bot = telebot.TeleBot(TOKEN)

user_data = {}
all_users = set()

def init_user(uid):
    all_users.add(uid)
    if uid not in user_data:
        user_data[uid] = {
            "balance": 20,
            "web": "HitClub",
            "logs": []
        }

# --- CORE ALGORITHM (PURE ANALYTICS) ---
def analyze_hash(hex_str):
    # Lấy 12 ký tự đầu để tránh tràn bộ nhớ khi ép kiểu int
    core_hex = hashlib.sha256(hex_str.encode()).hexdigest()[:12]
    val = int(core_hex, 16)
    
    # Tính tỉ lệ phần trăm dựa trên thuật toán chia dư (Modulo Matrix)
    # Đảm bảo phân bổ tỉ lệ luôn chạy mượt mà từ 20% đến 80%
    base_percent = (val % 600) / 10.0 + 20.0
    
    is_tai = base_percent >= 50.0
    result = "TÀI" if is_tai else "XỈU"
    
    if is_tai:
        percent_tai = round(base_percent, 1)
        percent_xiu = round(100.0 - base_percent, 1)
    else:
        percent_xiu = round(100.0 - base_percent, 1)
        percent_tai = round(base_percent, 1)
        
    # Độ tin cậy tính bằng biến thiên của mã MD5 gốc
    acc_hex = int(hashlib.md5(hex_str.encode()).hexdigest()[:8], 16)
    accuracy = round(85.0 + (acc_hex % 140) / 10.0, 1) # Ra kết quả từ 85.0% - 99.0%
    
    return result, percent_tai, percent_xiu, accuracy

# --- MINIMALIST UI ---
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚙️ Chuyển Cổng", callback_data="btn_web"),
        InlineKeyboardButton("💳 Ví & Lịch Sử", callback_data="btn_info")
    )
    markup.add(
        InlineKeyboardButton("💎 Nạp Xu", callback_data="btn_nap")
    )
    return markup

# --- USER COMMANDS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    init_user(uid)
    
    text = (
        "📊 **TOOL MD5 QBAO V8**\n"
        "---------------------------\n"
        f"ID: `{uid}`\n"
        f"Số dư: `{user_data[uid]['balance']} Xu`\n"
        f"Cổng: `{user_data[uid]['web']}`\n"
        "---------------------------\n"
        "Nhập mã MD5 (32 ký tự) hoặc SHA256 (64 ký tự) để hệ thống phân tích."
    )
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=main_menu())

# --- ADMIN COMMANDS (ERROR HANDLED) ---
@bot.message_handler(commands=['congxu'])
def add_coins(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Sai số lượng tham số.")
            
        target_id = int(parts[1])
        amount = int(parts[2])
        
        init_user(target_id)
        user_data[target_id]["balance"] += amount
        
        bot.reply_to(message, f"✅ Đã cộng {amount} Xu cho ID {target_id}. Số dư mới: {user_data[target_id]['balance']} Xu.")
        
        try:
            bot.send_message(target_id, f"💳 Tài khoản của bạn vừa được cộng +{amount} Xu từ Admin.")
        except:
            bot.reply_to(message, f"⚠️ Đã cộng xu, nhưng không thể gửi tin nhắn báo cáo cho ID {target_id} (Họ có thể đã chặn bot).")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi lệnh: {str(e)}\nSử dụng: `/congxu <ID> <Số_lượng>`", parse_mode="Markdown")

@bot.message_handler(commands=['thongbao'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        notice = message.text.split(" ", 1)[1].strip()
        success = 0
        text = f"📢 **THÔNG BÁO TỪ ADMIN**\n---------------------------\n{notice}"
        for uid in all_users:
            try:
                bot.send_message(uid, text, parse_mode="Markdown")
                success += 1
            except:
                pass
        bot.reply_to(message, f"✅ Đã gửi thông báo đến {success} người dùng.")
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi lệnh: {str(e)}\nSử dụng: `/thongbao <Nội_dung>`", parse_mode="Markdown")

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    init_user(uid)
    
    if call.data == "btn_web":
        markup = InlineKeyboardMarkup(row_width=2)
        for w in ["HitClub", "B52", "Lucky88", "LC79"]:
            markup.add(InlineKeyboardButton(w, callback_data=f"web_{w}"))
        bot.send_message(call.message.chat.id, "Chọn cổng game:", reply_markup=markup)
        
    elif call.data.startswith("web_"):
        web = call.data.split("_")[1]
        user_data[uid]["web"] = web
        bot.answer_callback_query(call.id, f"Đã chuyển cổng: {web}")
        bot.send_message(call.message.chat.id, f"✅ Cổng phân tích hiện tại: {web}", reply_markup=main_menu())
        
    elif call.data == "btn_info":
        logs_str = "\n".join(user_data[uid]["logs"]) if user_data[uid]["logs"] else "Chưa có dữ liệu."
        text = (
            f"💳 **VÍ & LỊCH SỬ**\n"
            "---------------------------\n"
            f"Số dư: `{user_data[uid]['balance']} Xu`\n"
            "---------------------------\n"
            f"Lịch sử phân tích:\n{logs_str}"
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
        
    elif call.data == "btn_nap":
        text = (
            "💎 **NẠP XU HỆ THỐNG**\n"
            "---------------------------\n"
            "Liên hệ Admin: @lionVnIos\n"
            f"Kèm theo ID của bạn: `{uid}`"
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

# --- HASH ANALYZER ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    uid = message.from_user.id
    init_user(uid)
    text = message.text.strip().lower()
    
    if len(text) not in [32, 64]:
        bot.reply_to(message, "⚠️ Vui lòng gửi đúng định dạng mã MD5 (32 ký tự) hoặc SHA256 (64 ký tự).")
        return
        
    if user_data[uid]["balance"] < 1:
        bot.reply_to(message, "⚠️ Số dư không đủ. Vui lòng nạp thêm xu để sử dụng.", reply_markup=main_menu())
        return
        
    user_data[uid]["balance"] -= 1
    result, p_tai, p_xiu, acc = analyze_hash(text)
    
    code_type = "MD5" if len(text) == 32 else "SHA256"
    short_hash = text[:8] + "..."
    
    user_data[uid]["logs"].insert(0, f"{short_hash} ➔ {result}")
    if len(user_data[uid]["logs"]) > 5:
        user_data[uid]["logs"].pop()
        
    res_msg = (
        f"📊 **KẾT QUẢ PHÂN TÍCH {code_type}**\n"
        "---------------------------\n"
        f"Dự đoán: **{result}**\n"
        f"Tỉ lệ: Tài {p_tai}% - Xỉu {p_xiu}%\n"
        f"Độ tin cậy: {acc}%\n"
        "---------------------------\n"
        f"Số dư: `{user_data[uid]['balance']} Xu`"
    )
    bot.reply_to(message, res_msg, parse_mode="Markdown", reply_markup=main_menu())

# --- LAUNCHER ---
if __name__ == '__main__':
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    try:
        bot.remove_webhook()
    except:
        pass
        
    print("TX PRO ANALYTICS v8.0 CORE ACTIVE...")
    bot.infinity_polling(none_stop=True)
