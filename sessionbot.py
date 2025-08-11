from telethon import TelegramClient, events
from telethon.sessions import StringSession

BOT_TOKEN = "7943293334:AAHSxLV82W7C7Qtp6IIzyGiNgW03BKvGn3k"

bot = TelegramClient('bot_session', api_id=28725696, api_hash='4254d53414182d2ea793853ff84a6747')  # api_id و api_hash مؤقتين
pending = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    pending[user_id] = {'step': 'api_id'}
    await event.reply("🔹 أرسل الـ API ID الخاص بك:")

@bot.on(events.NewMessage)
async def handle_steps(event):
    user_id = event.sender_id
    if user_id not in pending:
        return

    step_data = pending[user_id]

    # الخطوة 1: API ID
    if step_data['step'] == 'api_id':
        try:
            step_data['api_id'] = int(event.raw_text.strip())
            step_data['step'] = 'api_hash'
            await event.reply("🔹 أرسل الـ API Hash الخاص بك:")
        except ValueError:
            await event.reply("❌ API ID يجب أن يكون رقم.")
        return

    # الخطوة 2: API Hash
    if step_data['step'] == 'api_hash':
        step_data['api_hash'] = event.raw_text.strip()
        step_data['step'] = 'phone'
        await event.reply("📱 أرسل رقم هاتفك مع كود الدولة (مثال: +201234567890):")
        return

    # الخطوة 3: رقم الهاتف
    if step_data['step'] == 'phone':
        step_data['phone'] = event.raw_text.strip()
        await event.reply(f"📲 جاري إرسال كود التحقق إلى {step_data['phone']}...")
        client = TelegramClient(StringSession(), step_data['api_id'], step_data['api_hash'])
        await client.connect()
        try:
            await client.send_code_request(step_data['phone'])
            step_data['client'] = client
            step_data['step'] = 'code'
            await event.reply("🔹 أرسل كود التحقق:")
        except Exception as e:
            await event.reply(f"❌ خطأ: {str(e)}")
            pending.pop(user_id, None)
        return

    # الخطوة 4: الكود
    if step_data['step'] == 'code':
        code = event.raw_text.strip()
        client = step_data['client']
        try:
            await client.sign_in(step_data['phone'], code)
            string_session = client.session.save()
            await event.reply(f"✅ تم إنشاء الجلسة بنجاح:\n\n
            await client.disconnect()
            pending.pop(user_id, None)
        except Exception as e:
            if "2FA" in str(e) or "PASSWORD" in str(e).upper():
                step_data['step'] = 'password'
                await event.reply("🔐 الحساب محمي بكلمة مرور. أرسل كلمة المرور:")
            else:
                await event.reply(f"❌ خطأ أثناء تسجيل الدخول: {str(e)}")
                await client.disconnect()
                pending.pop(user_id, None)
        return

    # الخطوة 5: كلمة المرور
    if step_data['step'] == 'password':
        password = event.raw_text.strip()
        client = step_data['client']
        try:
            await client.sign_in(password=password)
            string_session = client.session.save()
            await event.reply(f"✅ تم إنشاء الجلسة بنجاح:\n\n
\n{string_session}\n```", parse_mode='md')
        except Exception as e:
            await event.reply(f"❌ خطأ في كلمة المرور: {str(e)}")
        finally:
            await client.disconnect()
            pending.pop(user_id, None)

print("🚀 البوت شغال...")
bot.start(bot_token=BOT_TOKEN)
bot.run_until_disconnected()
