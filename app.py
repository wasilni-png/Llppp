"""
🚖 بوت النقل الذكي - النسخة المنظمة
الملف الرئيسي للتطبيق
"""

import os
import logging
from flask import Flask, request
import telebot
from telebot import types
import threading
import time

# ============================================================================
# استيراد الموديولات
# ============================================================================

from bot_handlers import setup_bot_handlers
from database import (
    save_user_data, get_user_data, save_driver_data, get_driver_data,
    save_ride, get_ride, generate_ride_id, get_user_role,
    users_db, drivers_db, rides_db, user_roles, ride_requests
)
from keyboards import (
    main_menu_keyboard, driver_menu_keyboard, role_selection_keyboard,
    ride_types_inline, payment_methods_inline, confirm_ride_inline,
    support_options_inline, quick_actions_inline
)

# ============================================================================
# إعدادات أساسية
# ============================================================================

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# الحصول على التوكن من متغير البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN غير معين!")
    # سنستخدم التوكن الموجود للاختبار
    BOT_TOKEN = "8425005126:AAH9I7qu0gjKEpKX52rFWHsuCn9Bw5jaNr0"

# تهيئة البوت
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# تهيئة التطبيق
app = Flask(__name__)

# ============================================================================
# دوال مساعدة عامة
# ============================================================================

def send_driver_found(chat_id):
    """إرسال تأكيد إيجاد سائق"""
    bot.send_message(
        chat_id,
        "✅ <b>تم العثور على سائق!</b>\n\n"
        "🚗 <b>السائق:</b> أحمد محمد\n"
        "⭐ <b>التقييم:</b> 4.8\n"
        "🚘 <b>المركبة:</b> تويوتا كامري 2023\n"
        "🎨 <b>اللون:</b> أبيض\n"
        "⏱️ <b>الوصول:</b> 5 دقائق\n"
        "💰 <b>السعر:</b> 25 ر.س\n\n"
        "هل تريد تأكيد الرحلة؟",
        reply_markup=confirm_ride_inline()
    )

def handle_ride_type_selection(chat_id, ride_type):
    """معالجة اختيار نوع الرحلة"""
    type_names = {
        "ride_normal": "عادية",
        "ride_premium": "فاخرة",
        "ride_family": "عائلية",
        "ride_economy": "اقتصادية"
    }
    
    name = type_names.get(ride_type, "عادية")
    
    bot.send_message(
        chat_id,
        f"✅ <b>تم اختيار رحلة {name}</b>\n\n"
        f"📍 الرجاء إرسال موقعك لبدء البحث عن سائق...",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(
            types.KeyboardButton("📍 إرسال موقعي", request_location=True)
        ).row('🏠 القائمة الرئيسية')
    )

def handle_payment_selection(chat_id, payment_type):
    """معالجة اختيار طريقة الدفع"""
    type_names = {
        "pay_card": "بطاقة ائتمان",
        "pay_wallet": "محفظة إلكترونية",
        "pay_cash": "نقداً"
    }
    
    name = type_names.get(payment_type, "نقداً")
    
    bot.send_message(
        chat_id,
        f"✅ <b>تم اختيار الدفع {name}</b>\n\n"
        f"💳 <b>سيتم خصم المبلغ تلقائياً بعد انتهاء الرحلة</b>\n\n"
        f"📍 <b>الرجاء إرسال موقعك الآن:</b>",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(
            types.KeyboardButton("📍 إرسال موقعي", request_location=True)
        )
    )

def handle_accept_request(chat_id, data):
    """معالجة قبول طلب ركوب"""
    request_id = data.split("_")[-1]
    
    bot.send_message(
        chat_id,
        f"✅ <b>تم قبول الطلب #{request_id}!</b>\n\n"
        f"🚗 <b>اتجه نحو موقع العميل</b>\n"
        f"📍 <b>المسافة:</b> 1.2 كم\n"
        f"⏱️ <b>الوقت المتوقع:</b> 5 دقائق\n\n"
        f"📞 <b>رقم العميل:</b> 05********\n\n"
        f"🚦 <b>اضغط على الزر أدناه عند الوصول:</b>",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("✅ وصلت للعميل", callback_data="arrived_customer")
        )
    )

def handle_confirm_ride(chat_id, user_id):
    """تأكيد الرحلة"""
    # تحديث بيانات المستخدم
    user_data = get_user_data(user_id)
    if user_data:
        user_data['rides_count'] = user_data.get('rides_count', 0) + 1
        save_user_data(user_id, user_data)
    
    bot.send_message(
        chat_id,
        "✅ <b>تم تأكيد طلب الرحلة!</b>\n\n"
        "🚗 <b>السائق في طريقه إليك</b>\n"
        "⏱️ <b>الوقت المتوقع:</b> 5 دقائق\n"
        "📞 <b>رقم السائق:</b> 05********\n"
        "💰 <b>المبلغ المستحق:</b> 25 ر.س\n\n"
        "📍 <b>يمكنك تتبع الرحلة في الوقت الحقيقي</b>"
    )

def handle_cancel_ride(chat_id):
    """إلغاء الرحلة"""
    bot.send_message(
        chat_id,
        "❌ <b>تم إلغاء الطلب</b>\n\n"
        "يمكنك طلب رحلة جديدة في أي وقت.",
        reply_markup=main_menu_keyboard()
    )

def handle_recharge(chat_id):
    """شحن الرصيد"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("50 ر.س", callback_data="recharge_50"),
        types.InlineKeyboardButton("100 ر.س", callback_data="recharge_100"),
        types.InlineKeyboardButton("200 ر.س", callback_data="recharge_200"),
        types.InlineKeyboardButton("500 ر.س", callback_data="recharge_500")
    )
    
    bot.send_message(
        chat_id,
        "💳 <b>شحن الرصيد</b>\n\n"
        "اختر المبلغ المطلوب:",
        reply_markup=markup
    )

def handle_recharge_amount(chat_id, data):
    """معالجة مبلغ الشحن"""
    amount = data.replace("recharge_", "")
    
    bot.send_message(
        chat_id,
        f"💳 <b>شحن {amount} ر.س</b>\n\n"
        "اختر طريقة الدفع:",
        reply_markup=payment_methods_inline()
    )

def handle_withdraw(chat_id):
    """سحب الأموال"""
    bot.send_message(
        chat_id,
        "📤 <b>سحب الأموال</b>\n\n"
        "• الحد الأدنى للسحب: 50 ر.س\n"
        "• الوقت المتوقع: 1-3 أيام عمل\n"
        "• يجب ربط حساب بنكي أولاً\n\n"
        "📞 <b>للطلب يرجى التواصل مع الدعم</b>"
    )

def handle_quick_ride(chat_id):
    """طلب سريع"""
    bot.send_message(
        chat_id,
        "🚖 <b>طلب سريع</b>\n\n"
        "جاري البحث عن أقرب سائق...",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(
            types.KeyboardButton("📍 إرسال موقعي", request_location=True)
        ).row('🏠 القائمة الرئيسية')
    )

def handle_quick_location(chat_id):
    """موقع سريع"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("📍 إرسال موقعي", request_location=True)
    )
    markup.row('🏠 القائمة الرئيسية')
    
    bot.send_message(
        chat_id,
        "📍 <b>إرسال الموقع</b>\n\n"
        "اضغط على الزر أدناه:",
        reply_markup=markup
    )

def handle_quick_balance(chat_id, user_id):
    """رصيد سريع"""
    user_data = get_user_data(user_id)
    balance = user_data.get('balance', 0)
    
    bot.send_message(
        chat_id,
        f"💰 <b>رصيدك الحالي: {balance} ر.س</b>"
    )

def handle_quick_support(chat_id):
    """دعم سريع"""
    bot.send_message(
        chat_id,
        "📞 <b>الدعم الفني</b>\n\n"
        "💬 الدردشة: 24/7\n"
        "📱 الهاتف: 920000000\n"
        "✉️ البريد: support@nabd-bot.com",
        reply_markup=support_options_inline()
    )

def handle_support_options(chat_id, option):
    """خيارات الدعم"""
    options = {
        "call_support": "📞 <b>الاتصال الفوري</b>\n\nرقم الدعم: 920000000\n\nاضغط على الزر للاتصال:",
        "chat_support": "💬 <b>المحادثة النصية</b>\n\nسيقوم ممثل خدمة العملاء بالرد عليك قريباً.",
        "send_complaint": "📧 <b>إرسال شكوى</b>\n\nيرجى كتابة شكواك وسنرد عليك خلال 24 ساعة.",
        "faq": "❓ <b>الأسئلة الشائعة</b>\n\n1. كيف أطلب رحلة؟\n2. كيف أشحن رصيدي؟\n3. كيف أصبح سائق؟\n4. كيف أقيم السائق؟\n5. كيف أتواصل مع الدعم؟"
    }
    
    message = options.get(option, "اختر خياراً آخر.")
    
    if option == "call_support":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📞 اتصل الآن", url="tel:+966920000000"))
    else:
        markup = None
    
    bot.send_message(chat_id, message, reply_markup=markup)

# ============================================================================
# تهيئة معالجات البوت
# ============================================================================

# استدعاء دالة تهيئة المعالجات
setup_bot_handlers(
    bot, 
    save_user_data, get_user_data, save_driver_data, get_driver_data,
    get_user_role, user_roles,
    main_menu_keyboard, driver_menu_keyboard, role_selection_keyboard,
    ride_types_inline, quick_actions_inline, support_options_inline,
    confirm_ride_inline
)

# ============================================================================
# معالجة الأزرار التفاعلية (Callback Handlers)
# ============================================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """معالجة جميع ضغطات الأزرار"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data
    
    logger.info(f"🔘 ضغط زر: {data} من {user_id}")
    
    # إجابة سريعة
    bot.answer_callback_query(call.id, text="جاري المعالجة...")
    
    try:
        # حذف الرسالة القديمة
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    
    # معالجة الأزرار حسب النوع
    if data.startswith("ride_"):
        handle_ride_type_selection(chat_id, data)
    
    elif data.startswith("pay_"):
        handle_payment_selection(chat_id, data)
    
    elif data.startswith("accept_request_"):
        handle_accept_request(chat_id, data)
    
    elif data == "confirm_ride":
        handle_confirm_ride(chat_id, user_id)
    
    elif data == "cancel_ride":
        handle_cancel_ride(chat_id)
    
    elif data == "recharge":
        handle_recharge(chat_id)
    
    elif data == "withdraw":
        handle_withdraw(chat_id)
    
    elif data == "quick_ride":
        handle_quick_ride(chat_id)
    
    elif data == "quick_location":
        handle_quick_location(chat_id)
    
    elif data == "quick_balance":
        handle_quick_balance(chat_id, user_id)
    
    elif data == "quick_support":
        handle_quick_support(chat_id)
    
    elif data.startswith("recharge_"):
        handle_recharge_amount(chat_id, data)
    
    elif data in ["call_support", "chat_support", "send_complaint", "faq"]:
        handle_support_options(chat_id, data)
    
    else:
        # لأي زر غير معالج
        bot.send_message(
            chat_id,
            f"🔘 <b>تم الضغط على: {data}</b>\n\n"
            f"هذه الميزة قيد التطوير حالياً.",
            reply_markup=main_menu_keyboard()
        )

# ============================================================================
# معالجة المواقع
# ============================================================================

@bot.message_handler(content_types=['location'])
def handle_location(message):
    """معالجة الموقع المرسل"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    location = message.location
    
    role = get_user_role(user_id)
    
    if role == 'driver':
        # تحديث موقع السائق
        driver_data = get_driver_data(user_id)
        if driver_data:
            from datetime import datetime
            driver_data['location'] = {
                'lat': location.latitude,
                'lon': location.longitude,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_driver_data(user_id, driver_data)
            
            response = (
                "✅ <b>تم تحديث موقع السائق!</b>\n\n"
                f"• <b>خط العرض:</b> {location.latitude:.6f}\n"
                f"• <b>خط الطول:</b> {location.longitude:.6f}\n\n"
                "🎯 أنت الآن مرئي للعملاء القريبين"
            )
        else:
            response = "⚠️ <b>لا توجد بيانات سائق!</b>"
    else:
        # موقع العميل لطلب رحلة
        response = (
            "📍 <b>تم استلام موقعك!</b>\n\n"
            f"• <b>الإحداثيات:</b>\n"
            f"  خط العرض: {location.latitude:.6f}\n"
            f"  خط الطول: {location.longitude:.6f}\n\n"
            "🚖 <b>جاري البحث عن أقرب سائق...</b>"
        )
        
        # بعد 3 ثواني، إرسال تأكيد
        threading.Timer(3, lambda: send_driver_found(chat_id)).start()
    
    bot.send_message(chat_id, response)

# ============================================================================
# صفحات الويب
# ============================================================================

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    from datetime import datetime
    try:
        bot_info = bot.get_me()
        bot_status = f"@{bot_info.username}"
    except Exception as e:
        bot_status = f"❌ خطأ: {str(e)}"
    
    # إحصاءات
    total_users = len(users_db)
    total_drivers = len(drivers_db)
    active_drivers = sum(1 for d in drivers_db.values() if d.get('status') == 'online')
    
    return f'''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>🚖 بوت النقل الذكي</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                transition: transform 0.3s;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                background: rgba(255, 255, 255, 0.3);
            }}
            .btn {{
                display: inline-block;
                padding: 12px 30px;
                margin: 10px;
                background: white;
                color: #667eea;
                text-decoration: none;
                border-radius: 50px;
                font-weight: bold;
                transition: all 0.3s;
                border: 2px solid white;
            }}
            .btn:hover {{
                background: transparent;
                color: white;
            }}
            .btn-container {{
                text-align: center;
                margin: 40px 0;
            }}
            .feature {{
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                margin: 10px 0;
                border-radius: 10px;
                border-right: 5px solid #4CAF50;
            }}
            .instructions {{
                background: rgba(0, 0, 0, 0.2);
                padding: 20px;
                border-radius: 10px;
                margin: 30px 0;
            }}
            @media (max-width: 600px) {{
                .container {{
                    padding: 20px;
                }}
                .stats {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="font-size: 2.5em; margin-bottom: 10px;">🚖 بوت النقل الذكي</h1>
                <p style="font-size: 1.2em; opacity: 0.9;">نظام نقل ذكي متكامل - الإصدار المنظم</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>🤖 حالة البوت</h3>
                    <p style="font-size: 1.5em; font-weight: bold;">{bot_status}</p>
                </div>
                <div class="stat-card">
                    <h3>👥 إجمالي المستخدمين</h3>
                    <p style="font-size: 1.5em; font-weight: bold;">{total_users}</p>
                </div>
                <div class="stat-card">
                    <h3>🚖 السائقين النشطين</h3>
                    <p style="font-size: 1.5em; font-weight: bold;">{active_drivers} / {total_drivers}</p>
                </div>
                <div class="stat-card">
                    <h3>📅 تاريخ التشغيل</h3>
                    <p style="font-size: 1.5em; font-weight: bold;">{datetime.now().strftime("%Y-%m-%d")}</p>
                </div>
            </div>
            
            <div class="btn-container">
                <a href="/set_webhook" class="btn">⚙️ تعيين ويب هوك</a>
                <a href="https://t.me/Dhdhdyduudbot" target="_blank" class="btn">💬 فتح البوت</a>
                <a href="/test" class="btn">🧪 صفحة الاختبار</a>
            </div>
            
            <div class="instructions">
                <h3>🎯 ميزات البوت:</h3>
                <div class="feature">🚖 طلب رحلات فورية بأنواع مختلفة</div>
                <div class="feature">📍 تحديد الموقع تلقائياً</div>
                <div class="feature">💰 نظام دفع إلكتروني آمن</div>
                <div class="feature">👥 نظام مزدوج (عملاء وسائقين)</div>
                <div class="feature">📊 إحصائيات وتقارير مفصلة</div>
                <div class="feature">📞 دعم فني مباشر 24/7</div>
            </div>
            
            <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
                <p>🔗 الرابط: https://dhhfhfjd.onrender.com</p>
                <p>📞 الدعم: support@nabd-bot.com | 920000000</p>
                <p>© 2024 بوت النقل الذكي - جميع الحقوق محفوظة</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """تعيين ويب هوك"""
    try:
        # الحصول على عنوان التطبيق
        host = request.host
        
        # على Render، نستخدم RENDER_EXTERNAL_HOSTNAME
        render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if render_host:
            webhook_url = f"https://{render_host}/webhook"
        else:
            webhook_url = f"https://{host}/webhook"
        
        logger.info(f"🔄 محاولة تعيين ويب هوك على: {webhook_url}")
        
        # إزالة أي ويب هوك سابق
        bot.remove_webhook()
        time.sleep(1)
        
        # تعيين ويب هوك جديد
        result = bot.set_webhook(url=webhook_url)
        
        # اختبار البوت
        try:
            bot_info = bot.get_me()
            bot_details = f"@{bot_info.username} - {bot_info.first_name}"
            bot_status = "✅ متصل"
        except Exception as e:
            bot_details = f"❌ خطأ: {str(e)}"
            bot_status = "❌ غير متصل"
        
        return f'''
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>✅ تم تعيين الويب هوك</title>
            <style>
                body {{
                    padding: 50px;
                    font-family: Arial;
                    text-align: center;
                    background: #f5f5f5;
                }}
                .result-box {{
                    max-width: 600px;
                    margin: 20px auto;
                    padding: 30px;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .success {{
                    border-left: 5px solid #4CAF50;
                }}
                .btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    margin: 10px;
                    background: #0088cc;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="result-box success">
                <h2 style="color: #4CAF50;">✅ تم تعيين الويب هوك بنجاح!</h2>
                
                <div style="text-align: right; margin: 30px 0;">
                    <p><strong>🌐 رابط الويب هوك:</strong></p>
                    <p style="background: #f0f0f0; padding: 10px; border-radius: 5px; direction: ltr;">
                        {webhook_url}
                    </p>
                </div>
                
                <div style="text-align: right; margin: 20px 0;">
                    <p><strong>🤖 حالة البوت:</strong> {bot_status}</p>
                    <p><strong>🔧 التفاصيل:</strong> {bot_details}</p>
                    <p><strong>👥 المستخدمين المسجلين:</strong> {len(users_db)}</p>
                </div>
                
                <div style="margin-top: 40px;">
                    <a href="/" class="btn">🏠 الصفحة الرئيسية</a>
                    <a href="https://t.me/Dhdhdyduudbot" target="_blank" class="btn" style="background: #28a745;">
                        💬 افتح البوت
                    </a>
                </div>
            </div>
            
            <div style="margin-top: 20px; color: #666;">
                <p>⚠️ <strong>ملاحظة:</strong> إذا لم يستجب البوت، جرب إعادة تعيين ويب هوك مرة أخرى.</p>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        logger.error(f"❌ خطأ في تعيين ويب هوك: {e}")
        return f'''
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ padding: 50px; text-align: center; }}
                .error-box {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 30px;
                    background: #ffebee;
                    color: #c62828;
                    border-radius: 10px;
                    border-left: 5px solid #c62828;
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <h2>❌ خطأ في تعيين الويب هوك</h2>
                <p><strong>الخطأ:</strong> {str(e)}</p>
                
                <div style="text-align: right; margin: 30px 0; background: rgba(0,0,0,0.05); padding: 15px; border-radius: 5px;">
                    <h3>🛠️ خطوات الحل:</h3>
                    <ol style="text-align: right;">
                        <li>تأكد من صحة التوكن (BOT_TOKEN)</li>
                        <li>تحقق من اتصال الإنترنت</li>
                        <li>انتظر قليلاً ثم حاول مرة أخرى</li>
                        <li>إذا استمر الخطأ، أعد نشر التطبيق</li>
                    </ol>
                </div>
                
                <div style="margin-top: 20px;">
                    <a href="/" style="padding: 10px 20px; background: #0088cc; color: white; text-decoration: none; border-radius: 5px;">
                        العودة للصفحة الرئيسية
                    </a>
                </div>
            </div>
        </body>
        </html>
        ''', 500

@app.route('/test')
def test_page():
    """صفحة اختبار البوت"""
    return '''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>🧪 اختبار البوت</title>
        <style>
            body {
                padding: 30px;
                font-family: Arial;
                text-align: center;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }
            .test-container {
                max-width: 600px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            .step {
                background: #e3f2fd;
                padding: 15px;
                margin: 15px 0;
                border-radius: 10px;
                border-right: 5px solid #2196f3;
                text-align: right;
            }
            .btn {
                display: inline-block;
                padding: 12px 25px;
                margin: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                transition: transform 0.3s;
            }
            .btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .feature-list {
                text-align: right;
                margin: 30px 0;
            }
            .feature-item {
                padding: 10px;
                margin: 5px 0;
                background: #f8f9fa;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="test-container">
            <h1 style="color: #667eea;">🧪 اختبار البوت التفاعلي</h1>
            <p style="color: #666; margin-bottom: 30px;">اختبار شامل لجميع ميزات بوت النقل الذكي</p>
            
            <div class="step">
                <h3>📱 الخطوة 1: افتح البوت</h3>
                <p>اضغط على الزر أدناه لفتح البوت على Telegram</p>
            </div>
            
            <div class="step">
                <h3>🎯 الخطوة 2: أرسل /start</h3>
                <p>اكتب <code>/start</code> في محادثة البوت</p>
            </div>
            
            <div class="step">
                <h3>👤 الخطوة 3: اختر دورك</h3>
                <p>اختر "👤 عميل" أو "🚖 سائق" حسب احتياجك</p>
            </div>
            
            <div class="step">
                <h3>🔘 الخطوة 4: جرب الأزرار</h3>
                <p>جرب جميع الأزرار التفاعلية والقوائم</p>
            </div>
            
            <div class="feature-list">
                <h3>✨ الميزات التي يمكنك اختبارها:</h3>
                <div class="feature-item">🚖 طلب رحلة بأنواع مختلفة</div>
                <div class="feature-item">📍 إرسال الموقع تلقائياً</div>
                <div class="feature-item">💰 شحن الرصيد والسحب</div>
                <div class="feature-item">📞 التواصل مع الدعم</div>
                <div class="feature-item">⚙️ تعديل الإعدادات</div>
                <div class="feature-item">⭐ نظام التقييمات</div>
            </div>
            
            <div style="margin: 40px 0;">
                <a href="https://t.me/Dhdhdyduudbot" target="_blank" class="btn" style="font-size: 1.2em;">
                    🚀 ابدأ الاختبار الآن
                </a>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <p>مشكلة في الاختبار؟ <a href="/set_webhook">أعد تعيين ويب هوك</a></p>
                <p><a href="/">العودة للصفحة الرئيسية</a></p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/webhook', methods=['POST'])
def webhook():
    """نقطة استقبال تحديثات Telegram"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK'
    return 'Bad Request', 400

# ============================================================================
# بدء التطبيق
# ============================================================================

def setup():
    """إعداد البوت عند التشغيل"""
    try:
        bot_info = bot.get_me()
        logger.info(f"✅ البوت جاهز: @{bot_info.username}")
        logger.info(f"📊 قاعدة البيانات: {len(users_db)} مستخدم، {len(drivers_db)} سائق")
        return True
    except Exception as e:
        logger.error(f"❌ فشل إعداد البوت: {e}")
        return False

if __name__ == '__main__':
    # التشغيل المحلي
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 بدء التشغيل على منفذ {port}")
    setup()
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # على Render
    setup()