import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def key(item):
    if not isinstance(item, dict):
        return None
    value = item.get('item', item)
    return value.get('url') if isinstance(value, dict) else None

def clean(match):
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return match.group(0)
    def visit(value):
        if isinstance(value, dict):
            if value.get('@type') == 'ItemList' and isinstance(value.get('itemListElement'), list):
                seen = set()
                value['itemListElement'] = [item for item in value['itemListElement'] if not (key(item) in seen or seen.add(key(item)))]
                for position, item in enumerate(value['itemListElement'], 1):
                    if isinstance(item, dict): item['position'] = position
                value['numberOfItems'] = len(value['itemListElement'])
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(payload)
    return '<script type="application/ld+json">' + json.dumps(payload, ensure_ascii=False, indent=2) + '</script>'

for relative in ('index.html', 'articles/index.html', 'articles/market.html'):
    path = ROOT / relative
    path.write_text(re.sub(r'<script type="application/ld\+json">(.*?)</script>', clean, path.read_text(encoding='utf-8'), flags=re.S), encoding='utf-8', newline='\n')
