"""
قاعدة البيانات - إدارة البيانات الداخلية
"""

import time

# قاعدة بيانات مبسطة في الذاكرة
users_db = {}
drivers_db = {}
rides_db = {}
user_roles = {}
ride_requests = []
ride_counter = 0

def save_user_data(user_id, data):
    """حفظ بيانات المستخدم"""
    users_db[str(user_id)] = data

def get_user_data(user_id):
    """استرجاع بيانات المستخدم"""
    return users_db.get(str(user_id), {})

def save_driver_data(driver_id, data):
    """حفظ بيانات السائق"""
    drivers_db[str(driver_id)] = data

def get_driver_data(driver_id):
    """استرجاع بيانات السائق"""
    return drivers_db.get(str(driver_id), {})

def save_ride(ride_id, data):
    """حفظ بيانات الرحلة"""
    rides_db[ride_id] = data

def get_ride(ride_id):
    """استرجاع بيانات الرحلة"""
    return rides_db.get(ride_id)

def generate_ride_id():
    """إنشاء معرف فريد للرحلة"""
    global ride_counter
    ride_counter += 1
    return f"RIDE_{ride_counter}_{int(time.time())}"

def get_user_role(user_id):
    """الحصول على دور المستخدم"""
    return user_roles.get(str(user_id), 'customer')

def get_active_drivers():
    """الحصول على السائقين النشطين"""
    return [driver for driver in drivers_db.values() if driver.get('status') == 'online']

def get_user_rides(user_id):
    """الحصول على رحلات المستخدم"""
    user_rides = []
    for ride_id, ride_data in rides_db.items():
        if ride_data.get('user_id') == user_id or ride_data.get('driver_id') == user_id:
            user_rides.append(ride_data)
    return user_rides

def add_ride_request(request_data):
    """إضافة طلب رحلة جديد"""
    ride_requests.append(request_data)

def get_available_ride_requests():
    """الحصول على طلبات الرحلات المتاحة"""
    return ride_requests.copy()

def clear_old_ride_requests():
    """مسح طلبات الرحلات القديمة"""
    global ride_requests
    # يمكن إضافة منطق لحذف الطلبات القديمة بناءً على الوقت
    ride_requests = []