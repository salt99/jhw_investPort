import requests
import json
import re
from datetime import datetime, timezone, timedelta

# 조회할 ETF 종목코드 목록
CODES = [
    '272580',  # TIGER 단기채권액티브
    '305080',  # TIGER 미국채10년 선물
    '360750',  # TIGER 미국S&P500
    '361580',  # RISE 200TR
    '411060',  # ACE KRX 금현물
    '148070',  # KIWOOM 국고채10년
    '195980',  # PLUS 신흥국 MSCI(합성H)
    '284430',  # KODEX 200미국채혼합
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def fetch_price(code):
    url = f'https://finance.naver.com/item/main.naver?code={code}'
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        html = res.text
        # 현재가 파싱 — <strong id="_nowVal">56,685</strong>
        m = re.search(r'id="_nowVal"[^>]*>([\d,]+)<', html)
        if m:
            return int(m.group(1).replace(',', ''))
    except Exception as e:
        print(f'[ERROR] {code}: {e}')
    return None

KST = timezone(timedelta(hours=9))
now = datetime.now(KST)

prices = {}
for code in CODES:
    price = fetch_price(code)
    if price:
        prices[code] = price
        print(f'{code}: {price:,}원')
    else:
        print(f'{code}: 조회 실패')

result = {
    'updated': now.strftime('%Y.%m.%d %H:%M KST'),
    'date':    now.strftime('%Y-%m-%d'),
    'prices':  prices
}

with open('prices.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'\n✅ prices.json 저장 완료 ({now.strftime("%Y.%m.%d %H:%M KST")})')
