import telebot
import math
import os
from flask import Flask
import threading
from telebot.types import InlineQueryResultArticle, InputTextMessageContent

TOKEN = '8447988972:AAEJaR-TJuzUSDXYab4lmFWmjO7cSXMX8U'
bot = telebot.TeleBot(TOKEN)

# သိမ်းထားမည့် order များ (duplicate စစ်ဖို့)
recent_orders = {}

# =====================================
# /start command
# =====================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "👋 မင်္ဂလာပါ! Kiwii MLBB Diamond Shop へようこそ\n\n"
        "📌 Order ပို့နည်း:\n"
        "MLBB ID နဲ့ Zone ကို ဒီပုံစံနဲ့ ပို့ပါ\n\n"
        "🔸 ဥပမာ:\n"
        "12345678(1234) dia600\n\n"
        "✅ Bot က အလိုအလျောက် confirm ပြန်ပေးမယ်"
    )

# =====================================
# MLBB Order Handler
# =====================================
@bot.message_handler(func=lambda message: True)
def handle_order(message):
    text = message.text.strip()
    
    # MLBB order pattern စစ်ဆေး: နံပါတ်(နံပါတ်) dia နံပါတ်
    import re
    pattern = r'(\d+)\((\d+)\)\s*dia\s*(\d+)'
    match = re.search(pattern, text.lower())
    
    if match:
        user_id = match.group(1)
        zone_id = match.group(2)
        diamond = match.group(3)
        
        # Order key တည်ဆောက်
        order_key = f"{user_id}_{zone_id}_{diamond}"
        chat_id = message.chat.id
        
        # Duplicate စစ်ဆေး
        if chat_id in recent_orders and recent_orders[chat_id] == order_key:
            bot.reply_to(message,
                "⚠️ သတိပေးချက်!\n\n"
                f"ဒီ order တူညီတဲ့ မှာမည်ကို မကြာသေးခင်က တင်ထားပြီးပါပြီ!\n\n"
                f"🆔 MLBB ID: {user_id}\n"
                f"🌐 Zone: {zone_id}\n"
                f"💎 Diamond: {diamond}\n\n"
                "ထပ်မံ မှာမည်မှာ သေချာရင် admin ကို ဆက်သွယ်ပါ။"
            )
            return
        
        # Order သိမ်းပါ
        recent_orders[chat_id] = order_key
        
        # Copy လုပ်ရလွယ်အောင် + Delete ခလုတ်ပုံစံ ပြန်ပို့
        confirm_text = (
            f"✅ Order လက်ခံပြီ!\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🆔 MLBB ID : `{user_id}`\n"
            f"🌐 Zone ID : `{zone_id}`\n"
            f"💎 Diamond : `{diamond}`\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"📋 Copy ယူရန် အပေါ်က စာသားများကို နှိပ်ပါ\n\n"
            f"⏳ မကြာမီ diamond ဖြည့်ပေးပါမယ် 🙏"
        )
        
        # Inline keyboard နဲ့ ပို့ပါ
        markup = telebot.types.InlineKeyboardMarkup()
        cancel_btn = telebot.types.InlineKeyboardButton(
            "❌ Order ပယ်ဖျက်မည်", 
            callback_data=f"cancel_{message.message_id}"
        )
        markup.add(cancel_btn)
        
        bot.reply_to(message, confirm_text, parse_mode='Markdown', reply_markup=markup)
    
    else:
        # Order မဟုတ်ရင် Calculator အဖြစ် သုံးပါ
        try:
            allowed_math_functions = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
            allowed_math_functions['abs'] = abs
            allowed_math_functions['round'] = round
            
            text_to_calc = text.lower()
            text_to_calc = text_to_calc.replace('^', '**')
            text_to_calc = text_to_calc.replace('×', '*')
            text_to_calc = text_to_calc.replace(',', '')
            
            result = eval(text_to_calc, {"__builtins__": None}, allowed_math_functions)
            bot.reply_to(message, f"{message.text} = {result}")
        
        except Exception:
            if message.chat.type == 'private':
                bot.reply_to(message,
                    "📌 Order ပို့နည်း:\n"
                    "12345678(1234) dia600\n\n"
                    "🆔 MLBB ID (Zone) dia ပမာဏ\n"
                    "ဒီပုံစံနဲ့ ပို့ပေးပါ 🙏"
                )
            else:
                pass

# =====================================
# Cancel Button Handler
# =====================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def handle_cancel(call):
    bot.answer_callback_query(call.id, "Order ပယ်ဖျက်လိုက်ပါပြီ ❌")
    bot.edit_message_text(
        "❌ Order ပယ်ဖျက်ပြီးပါပြီ\n\nထပ်မံ မှာမည်ချင်ရင် အသစ်တင်ပါ။",
        call.message.chat.id,
        call.message.message_id
    )
    # Recent order မှ ဖယ်ရှားပါ
    chat_id = call.message.chat.id
    if chat_id in recent_orders:
        del recent_orders[chat_id]

# =====================================
# Inline Query Handler
# =====================================
@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    try:
        allowed_math_functions = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        allowed_math_functions['abs'] = abs
        allowed_math_functions['round'] = round
        
        query_str = inline_query.query.lower()
        calc_str = query_str.replace('^', '**').replace('x', '*').replace('×', '*').replace(',', '')
        result = eval(calc_str, {"__builtins__": None}, allowed_math_functions)
        
        r = InlineQueryResultArticle(
            id='1',
            title=f"Result: {result}",
            description=f"{query_str} = {result}",
            input_message_content=InputTextMessageContent(f"{query_str} = {result}")
        )
        bot.answer_inline_query(inline_query.id, [r])
    except Exception:
        pass

# =====================================
# Flask Web Server (24/7 အတွက်)
# =====================================
app = Flask(__name__)

@app.route('/')
def home():
    return "MLBB Diamond Bot is running 24/7! 💎"

def run_bot():
    print("MLBB Diamond Bot စတင်အလုပ်လုပ်နေပါပြီ... 💎")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    thread = threading.Thread(target=run_bot)
    thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
