"""
معالجات البوت - منطق التفاعل مع المستخدمين
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_bot_handlers(
    bot, 
    save_user_data, get_user_data, save_driver_data, get_driver_data,
    get_user_role, user_roles,
    main_menu_keyboard, driver_menu_keyboard, role_selection_keyboard,
    ride_types_inline, quick_actions_inline, support_options_inline,
    confirm_ride_inline
):
    """تهيئة جميع معالجات البوت"""
    
    # ============================================================================
    # معالجات الأوامر الرئيسية
    # ============================================================================
    
    @bot.message_handler(commands=['start', 'help'])
    def handle_start(message):
        """معالجة أمر البدء"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        name = message.from_user.first_name
        
        logger.info(f"👋 مستخدم جديد: {name} ({user_id})")
        
        # حفظ بيانات المستخدم
        user_data = {
            'id': user_id,
            'chat_id': chat_id,
            'name': name,
            'username': message.from_user.username,
            'join_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'balance': 100,  # رصيد افتراضي
            'rides_count': 0,
            'rating': 5.0
        }
        save_user_data(user_id, user_data)
        
        # عرض اختيار الدور
        bot.send_message(
            chat_id,
            f"🎉 <b>مرحباً بك {name} في بوت النقل الذكي!</b>\n\n"
            f"🚖 <b>خدمة نقل ذكية توفر لك:</b>\n"
            f"• رحلات سريعة وآمنة\n"
            f"• تتبع مباشر للرحلة\n"
            f"• دفع إلكتروني آمن\n"
            f"• تقييمات موثوقة\n\n"
            f"📱 <b>اختر دورك للبدء:</b>",
            reply_markup=role_selection_keyboard()
        )
    
    @bot.message_handler(func=lambda message: message.text == '👤 عميل')
    def handle_customer_role(message):
        """اختيار دور العميل"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        user_roles[str(user_id)] = 'customer'
        
        bot.send_message(
            chat_id,
            "✅ <b>تم تسجيلك كعميل!</b>\n\n"
            "يمكنك الآن طلب رحلات واستخدام جميع خدماتنا.",
            reply_markup=main_menu_keyboard()
        )
        
        # إرسال أزرار سريعة
        bot.send_message(
            chat_id,
            "⚡ <b>أوامر سريعة:</b>",
            reply_markup=quick_actions_inline()
        )
    
    @bot.message_handler(func=lambda message: message.text == '🚖 سائق')
    def handle_driver_role(message):
        """اختيار دور السائق"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        user_roles[str(user_id)] = 'driver'
        
        # حفظ بيانات السائق
        driver_data = {
            'id': user_id,
            'name': message.from_user.first_name,
            'status': 'offline',
            'earnings': 0,
            'rides_completed': 0,
            'rating': 5.0,
            'location': None,
            'vehicle_type': 'سيارة عادية',
            'vehicle_number': 'أ ب ج 123'
        }
        save_driver_data(user_id, driver_data)
        
        bot.send_message(
            chat_id,
            "✅ <b>تم تسجيلك كسائق!</b>\n\n"
            "يمكنك الآن بدء العمل واستقبال طلبات الركوب.",
            reply_markup=driver_menu_keyboard()
        )
    
    @bot.message_handler(func=lambda message: message.text == '🏠 القائمة الرئيسية')
    def handle_main_menu(message):
        """العودة للقائمة الرئيسية"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        role = get_user_role(user_id)
        
        if role == 'driver':
            bot.send_message(
                chat_id,
                "🏠 <b>القائمة الرئيسية للسائق</b>",
                reply_markup=driver_menu_keyboard()
            )
        else:
            bot.send_message(
                chat_id,
                "🏠 <b>القائمة الرئيسية</b>",
                reply_markup=main_menu_keyboard()
            )
    
    # ============================================================================
    # معالجات العملاء
    # ============================================================================
    
    @bot.message_handler(func=lambda message: message.text == '🚖 طلب رحلة')
    def handle_ride_request(message):
        """طلب رحلة جديدة"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # تحقق إذا كان المستخدم عميل
        if get_user_role(user_id) != 'customer':
            bot.send_message(
                chat_id,
                "⚠️ <b>عذراً!</b>\n\n"
                "يجب أن تكون مسجلاً كعميل لطلب رحلة.\n"
                "أرسل /start لتغيير دورك.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        bot.send_message(
            chat_id,
            "🚗 <b>اختر نوع الرحلة:</b>\n\n"
            "• 🚗 <b>عادية</b>: سعر أساسي\n"
            "• 🚙 <b>فاخرة</b>: راحة أكثر +30%\n"
            "• 🚐 <b>عائلية</b>: سيارة كبيرة +50%\n"
            "• 🚗 <b>اقتصادية</b>: توفير سعر -20%",
            reply_markup=ride_types_inline()
        )
    
    @bot.message_handler(func=lambda message: message.text == '📍 إرسال موقعي')
    def handle_send_location(message):
        """طلب إرسال الموقع"""
        chat_id = message.chat.id
        
        from telebot import types
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(
            types.KeyboardButton("📍 إرسال موقعي الحالي", request_location=True)
        )
        markup.row('🏠 القائمة الرئيسية')
        
        bot.send_message(
            chat_id,
            "📍 <b>إرسال الموقع</b>\n\n"
            "اضغط على الزر أدناه لمشاركة موقعك الحالي مع السائق.",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '💰 رصيدي')
    def handle_balance(message):
        """عرض الرصيد"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        user_data = get_user_data(user_id)
        balance = user_data.get('balance', 0)
        
        from telebot import types
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("💳 شحن الرصيد", callback_data="recharge"),
            types.InlineKeyboardButton("📤 سحب الأموال", callback_data="withdraw")
        )
        markup.add(
            types.InlineKeyboardButton("📊 التفاصيل", callback_data="balance_details"),
            types.InlineKeyboardButton("💳 طرق الدفع", callback_data="payment_methods")
        )
        
        bot.send_message(
            chat_id,
            f"💰 <b>حسابك المالي</b>\n\n"
            f"• الرصيد المتاح: <b>{balance} ر.س</b>\n"
            f"• الرحلات المكتملة: <b>{user_data.get('rides_count', 0)}</b>\n"
            f"• التقييم: <b>{user_data.get('rating', 5.0)} ⭐</b>\n\n"
            f"اختر الإجراء:",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '📋 رحلاتي')
    def handle_my_rides(message):
        """عرض الرحلات"""
        chat_id = message.chat.id
        
        from telebot import types
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔄 الرحلات الحالية", callback_data="current_rides"),
            types.InlineKeyboardButton("📜 الرحلات السابقة", callback_data="past_rides")
        )
        
        bot.send_message(
            chat_id,
            "📋 <b>رحلاتي</b>\n\n"
            "يمكنك عرض الرحلات الحالية والسابقة:",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '⚙️ إعدادات')
    def handle_settings(message):
        """عرض الإعدادات"""
        chat_id = message.chat.id
        
        from telebot import types
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👤 تعديل الملف الشخصي", callback_data="edit_profile"),
            types.InlineKeyboardButton("🔔 إعدادات الإشعارات", callback_data="notification_settings"),
            types.InlineKeyboardButton("🌍 تغيير اللغة", callback_data="change_language"),
            types.InlineKeyboardButton("🔒 الخصوصية والأمان", callback_data="privacy_settings")
        )
        
        bot.send_message(
            chat_id,
            "⚙️ <b>الإعدادات</b>\n\n"
            "إدارة إعدادات حسابك:",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '📞 الدعم')
    def handle_support(message):
        """عرض خيارات الدعم"""
        chat_id = message.chat.id
        
        bot.send_message(
            chat_id,
            "📞 <b>مركز الدعم والمساعدة</b>\n\n"
            "💬 <b>الدردشة المباشرة:</b> 24/7\n"
            "📱 <b>الهاتف:</b> 920000000\n"
            "✉️ <b>البريد:</b> support@nabd-bot.com\n\n"
            "اختر طريقة التواصل:",
            reply_markup=support_options_inline()
        )
    
    @bot.message_handler(func=lambda message: message.text == '👤 حسابي')
    def handle_profile(message):
        """عرض الملف الشخصي"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        user_data = get_user_data(user_id)
        
        from telebot import types
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✏️ تعديل الاسم", callback_data="edit_name"),
            types.InlineKeyboardButton("📱 رقم الجوال", callback_data="edit_phone")
        )
        markup.add(
            types.InlineKeyboardButton("📧 البريد الإلكتروني", callback_data="edit_email"),
            types.InlineKeyboardButton("🔐 تغيير كلمة المرور", callback_data="change_password")
        )
        
        bot.send_message(
            chat_id,
            f"👤 <b>الملف الشخصي</b>\n\n"
            f"• <b>الاسم:</b> {user_data.get('name', 'غير محدد')}\n"
            f"• <b>رقم العضوية:</b> #{str(user_id)[-6:]}\n"
            f"• <b>تاريخ التسجيل:</b> {user_data.get('join_date', 'اليوم')}\n"
            f"• <b>عدد الرحلات:</b> {user_data.get('rides_count', 0)}\n"
            f"• <b>التقييم:</b> {user_data.get('rating', 5.0)} ⭐\n\n"
            f"اختر ما تريد تعديله:",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '🎫 العروض')
    def handle_offers(message):
        """عرض العروض"""
        chat_id = message.chat.id
        
        from telebot import types
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🎁 أول رحلة مجاناً", callback_data="offer_first"),
            types.InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite_friends"),
            types.InlineKeyboardButton("📱 حمّل التطبيق", callback_data="download_app"),
            types.InlineKeyboardButton("🎯 عرض العودة", callback_data="comeback_offer")
        )
        
        bot.send_message(
            chat_id,
            "🎫 <b>العروض والترقيات</b>\n\n"
            "🔥 <b>عروض حصرية لك!</b>\n\n"
            "1. 🎁 <b>الرحلة الأولى مجاناً</b>\n"
            "   - لحد 50 ريال\n"
            "   - صالح لـ 7 أيام\n\n"
            "2. 👥 <b>دعوة أصدقاء</b>\n"
            "   - احصل على 50 ريال\n"
            "   - لكل صديق\n\n"
            "3. 📱 <b>خصم التطبيق</b>\n"
            "   - خصم 20% على أول 5 رحلات\n\n"
            "اختر العرض:",
            reply_markup=markup
        )
    
    # ============================================================================
    # معالجات السائقين
    # ============================================================================
    
    @bot.message_handler(func=lambda message: message.text == '🟢 بدء العمل')
    def handle_start_work(message):
        """بدء عمل السائق"""
        driver_id = message.from_user.id
        chat_id = message.chat.id
        
        driver_data = get_driver_data(driver_id)
        if not driver_data:
            bot.send_message(
                chat_id,
                "⚠️ <b>عذراً!</b>\n\n"
                "يجب أن تكون مسجلاً كسائق أولاً.\n"
                "أرسل /start واختر '🚖 سائق'.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        driver_data['status'] = 'online'
        driver_data['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_driver_data(driver_id, driver_data)
        
        bot.send_message(
            chat_id,
            "✅ <b>تم تفعيل وضع السائق!</b>\n\n"
            "🎯 أنت الآن مرئي للعملاء\n"
            "📱 ستستقبل طلبات جديدة تلقائياً\n"
            "💰 ابدأ بكسب الأرباح الآن!\n\n"
            "📍 <b>تأكد من تحديث موقعك بانتظام</b>"
        )
    
    @bot.message_handler(func=lambda message: message.text == '🔴 إيقاف')
    def handle_stop_work(message):
        """إيقاف عمل السائق"""
        driver_id = message.from_user.id
        chat_id = message.chat.id
        
        driver_data = get_driver_data(driver_id)
        if driver_data:
            driver_data['status'] = 'offline'
            save_driver_data(driver_id, driver_data)
        
        bot.send_message(
            chat_id,
            "🔴 <b>تم إيقاف خدمة الاستقبال</b>\n\n"
            "للعودة لاستقبال الطلبات، اضغط '🟢 بدء العمل'"
        )
    
    @bot.message_handler(func=lambda message: message.text == '📍 تحديث موقعي')
    def handle_update_location_driver(message):
        """تحديث موقع السائق"""
        chat_id = message.chat.id
        
        from telebot import types
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(
            types.KeyboardButton("📍 تحديث موقعي", request_location=True)
        )
        
        bot.send_message(
            chat_id,
            "📍 <b>تحديث الموقع</b>\n\n"
            "اضغط على الزر أدناه لتحديث موقعك الحالي.",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '📊 الطلبات')
    def handle_ride_requests(message):
        """عرض طلبات الركوب"""
        driver_id = message.from_user.id
        chat_id = message.chat.id
        
        # محاكاة طلبات وهمية
        fake_requests = [
            {"id": 1, "distance": "1.2 كم", "price": "25 ر.س", "time": "5 دقائق", "type": "🚗 عادية"},
            {"id": 2, "distance": "2.5 كم", "price": "35 ر.س", "time": "8 دقائق", "type": "🚙 فاخرة"},
            {"id": 3, "distance": "3.1 كم", "price": "45 ر.س", "time": "10 دقائق", "type": "🚐 عائلية"}
        ]
        
        from telebot import types
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for req in fake_requests:
            markup.add(
                types.InlineKeyboardButton(
                    f"طلب #{req['id']} - {req['distance']} - {req['price']} - {req['type']}", 
                    callback_data=f"accept_request_{req['id']}"
                )
            )
        
        markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_requests"))
        
        bot.send_message(
            chat_id,
            "📊 <b>الطلبات المتاحة</b>\n\n"
            f"• عدد الطلبات: <b>{len(fake_requests)}</b>\n"
            f"• أقرب طلب: <b>{fake_requests[0]['distance']}</b>\n"
            f"• متوسط السعر: <b>35 ر.س</b>\n\n"
            f"اختر طلباً للقبول:",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '💰 أرباحي')
    def handle_driver_earnings(message):
        """عرض أرباح السائق"""
        driver_id = message.from_user.id
        chat_id = message.chat.id
        
        driver_data = get_driver_data(driver_id)
        if not driver_data:
            bot.send_message(
                chat_id,
                "⚠️ <b>لا توجد بيانات سائق!</b>\n\n"
                "يجب أن تكون مسجلاً كسائق أولاً.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        earnings = driver_data.get('earnings', 0)
        rides_completed = driver_data.get('rides_completed', 0)
        
        from telebot import types
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("💳 سحب الأرباح", callback_data="withdraw_earnings"),
            types.InlineKeyboardButton("📊 التفاصيل", callback_data="earnings_details")
        )
        
        bot.send_message(
            chat_id,
            f"💰 <b>أرباحك</b>\n\n"
            f"• إجمالي الأرباح: <b>{earnings} ر.س</b>\n"
            f"• الرحلات المكتملة: <b>{rides_completed}</b>\n"
            f"• متوسط الربح/رحلة: <b>{earnings/max(rides_completed, 1):.1f} ر.س</b>\n"
            f"• التقييم: <b>{driver_data.get('rating', 5.0)} ⭐</b>\n\n"
            f"اختر الإجراء:",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '📈 إحصائيات')
    def handle_driver_stats(message):
        """عرض إحصائيات السائق"""
        driver_id = message.from_user.id
        chat_id = message.chat.id
        
        driver_data = get_driver_data(driver_id)
        if not driver_data:
            bot.send_message(
                chat_id,
                "⚠️ <b>لا توجد بيانات سائق!</b>",
                reply_markup=main_menu_keyboard()
            )
            return
        
        rides_completed = driver_data.get('rides_completed', 0)
        earnings = driver_data.get('earnings', 0)
        
        bot.send_message(
            chat_id,
            f"📈 <b>إحصائياتك</b>\n\n"
            f"• الرحلات المكتملة: <b>{rides_completed}</b>\n"
            f"• إجمالي المسافة: <b>{rides_completed * 5} كم</b>\n"
            f"• متوسط التقييم: <b>{driver_data.get('rating', 5.0)} ⭐</b>\n"
            f"• ساعات العمل: <b>{rides_completed * 0.5:.1f} ساعة</b>\n"
            f"• إجمالي الأرباح: <b>{earnings} ر.س</b>\n"
            f"• العملاء الراضين: <b>{int(rides_completed * 0.9)}</b>\n\n"
            f"🎯 <b>استمر في العمل لزيادة إحصائياتك!</b>"
        )
    
    # ============================================================================
    # معالجة الرسائل العامة
    # ============================================================================
    
    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        """معالجة جميع الرسائل الأخرى"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        logger.info(f"📩 رسالة: {message.text} من {user_id}")
        
        # إذا كانت رسالة نصية عادية ولم يتم التعامل معها
        bot.send_message(
            chat_id,
            "🤖 <b>مرحباً!</b>\n\n"
            "استخدم الأزرار للتنقل أو:\n"
            "/start - للبدء من جديد\n"
            "/help - للمساعدة\n\n"
            "أو اختر من القائمة:",
            reply_markup=main_menu_keyboard()
        )
    
    logger.info("✅ تم تهيئة جميع معالجات البوت")