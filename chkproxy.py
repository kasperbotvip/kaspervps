import requests

proxies_list = [
    "rp.scrapegw.com:6060:8i1857hm2b2xipl-odds-5+100-country-us-state-newyork:udgt90kug3p8oo6",
]

# حذف المكرر تلقائياً
proxies_list = list(set(proxies_list))

working = []

for proxy in proxies_list:
    try:
        host, port, user, password = proxy.split(":")

        proxy_url = f"http://{user}:{password}@{host}:{port}"

        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }

        response = requests.get(
            "https://httpbin.org/ip",
            proxies=proxies,
            timeout=10
        )

        if response.status_code == 200:
            print(f"[WORKING] {proxy}")
            working.append(proxy)

    except Exception:
        print(f"[FAILED] {proxy}")

print("\n===== WORKING PROXIES =====")

for proxy in working:
    print(proxy)

# حفظ الشغال بملف
with open("working_proxies.txt", "w") as f:
    for proxy in working:
        f.write(proxy + "\n")

print("\nSaved to working_proxies.txt")