import re
import random
import requests
import json

with open('config.json', 'r') as f:
    config = json.load(f)

def luhn_checksum(card_number):
    digits = [int(d) for d in str(card_number)]
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0

def cc_gen(bin_format, amount=10):
    parts = bin_format.split('|')
    bin_num = re.sub(r'[^0-9xX]', '', parts[0])
    month = parts[1] if len(parts) > 1 and parts[1].isdigit() else str(random.randint(1, 12)).zfill(2)
    year = parts[2] if len(parts) > 2 and parts[2].isdigit() else str(random.randint(2025, 2031))
    cvv = parts[3] if len(parts) > 3 and parts[3].isdigit() else str(random.randint(100, 999))
    
    generated = []
    amount = min(amount, config['limits']['max_gen_amount'])
    for _ in range(amount):
        card_no = bin_num.lower()
        while 'x' in card_no:
            card_no = card_no.replace('x', str(random.randint(0, 9)), 1)
        length = 15 if card_no.startswith('3') else 16
        while len(card_no) < length - 1:
            card_no += str(random.randint(0, 9))
        for i in range(10):
            temp_card = card_no + str(i)
            if luhn_checksum(temp_card):
                card_no = temp_card
                break
        generated.append(f"<code>{card_no}|{month}|{year}|{cvv}</code>")
    return generated

async def clean(text: str) -> str:
    text = re.sub(r"\r|\n", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^0-9]", " ", text)
    text = text.strip()
    return re.sub(r"\s+", " ", text)

async def parse_cc(input_data: str) -> list:
    tarjetas = []
    lines = input_data.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        cleaned = await clean(line)
        try:
            if cleaned.startswith("3"):
                match = re.search(r"(\d{15}) (\d{1,2}) (\d{2,4}) (\d{4})", cleaned)
            else:
                match = re.search(r"(\d{16}) (\d{1,2}) (\d{2,4}) (\d{3,4})", cleaned)
            if match:
                cc, mes, ano, cvv = match.groups()
                if len(mes) == 1:
                    mes = f"0{mes}"
                if len(ano) == 2:
                    ano = f"20{ano}"
                tarjetas.append(f"{cc}|{mes}|{ano}|{cvv}")
        except Exception:
            continue
    return tarjetas

async def get_bin_info(bin_number):
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_number}", timeout=7)
        if response.status_code == 200:
            data = response.json()
            country = data.get("country", {}).get("name", "Unknown")
            scheme = data.get("scheme", "Unknown").upper()
            type_card = data.get("type", "Unknown").upper()
            return country, f"{scheme}-{type_card}"
    except:
        pass
    return "Unknown", "N/A"