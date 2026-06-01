import requests
import json
import re
from datetime import datetime, timezone, timedelta

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

KST = timezone(timedelta(hours=9))
now = datetime.now(KST)

def fetch_naver_json(code):
    """네이버 금융 JSON API"""
    url = f'https://m.stock.naver.com/api/stock/{code}/basic'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json',
        'Referer': f'https://m.stock.naver.com/domestic/stock/{code}/overview',
        'Origin': 'https://m.stock.naver.com',
    }
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    d = res.json()
    price = d.get('closePrice') or d.get('stockEndPrice') or d.get('currentPrice')
    if price:
        return int(str(price).replace(',', ''))
    return None

def fetch_naver_pc(code):
    """네이버 금융 PC 시세"""
    url = f'https://finance.naver.com/item/main.naver?code={code}'
    session = requests.Session()
    # 먼저 메인 페이지 방문 (쿠키 획득)
    session.get('https://finance.naver.com', headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }, timeout=10)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Referer': 'https://finance.naver.com/',
    }
    res = session.get(url, headers=headers, timeout=15)
    res.encoding = 'euc-kr'
    m = re.search(r'id="_nowVal"[^>]*>([\d,]+)<', res.text)
    if m:
        return int(m.group(1).replace(',', ''))
    # 대체 패턴
    m2 = re.search(r'"price"\s*:\s*"?([\d,]+)"?', res.text)
    if m2:
        return int(m2.group(1).replace(',', ''))
    return None

def fetch_yahoo(code):
    """Yahoo Finance (.KS 종목)"""
    ycode = f'{code}.KS'
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ycode}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    d = res.json()
    result = d['chart']['result']
    if result:
        price = result[0]['meta'].get('regularMarketPrice') or result[0]['meta'].get('previousClose')
        if price:
            return round(price)
    return None

def fetch_daum(code):
    """다음 금융 API"""
    url = f'https://finance.daum.net/api/quotes/A{code}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://finance.daum.net/quotes/A{code}',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://finance.daum.net',
    }
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    d = res.json()
    price = d.get('tradePrice') or d.get('closePrice')
    if price:
        return int(price)
    return None

METHODS = [
    ('Naver JSON', fetch_naver_json),
    ('Yahoo Finance', fetch_yahoo),
    ('Daum Finance', fetch_daum),
    ('Naver PC', fetch_naver_pc),
]

prices = {}
for code in CODES:
    success = False
    for method_name, method in METHODS:
        try:
            price = method(code)
            if price and price > 0:
                prices[code] = price
                print(f'{code}: {price:,}원 ({method_name})')
                success = True
                break
        except Exception as e:
            print(f'{code} [{method_name}] 실패: {type(e).__name__}: {str(e)[:80]}')
    if not success:
        print(f'{code}: ❌ 모든 방법 실패')

result = {
    'updated': now.strftime('%Y.%m.%d %H:%M KST'),
    'date':    now.strftime('%Y-%m-%d'),
    'prices':  prices,
    'success': len(prices),
    'total':   len(CODES)
}

with open('prices.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'\n✅ {len(prices)}/{len(CODES)} 종목 저장 완료')
