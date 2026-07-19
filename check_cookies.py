"""检查保存的cookie"""
import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
state_file = os.path.join(base_dir, 'taobao_storage_state.json')
output_file = os.path.join(base_dir, 'cookie_report.txt')

data = json.load(open(state_file, 'r', encoding='utf-8'))

cookies = data.get('cookies', [])
lines = []
lines.append(f"Cookie总数: {len(cookies)}")
lines.append("")

key_cookies = ['cookie2', 't', '_tb_token_', 'unb', 'uc1', 'csg', '_m_h5_tk', 'login5', 'uc3', 'cna', 'isg', 'tfstk']
lines.append("关键登录Cookie:")
for c in cookies:
    if c['name'] in key_cookies:
        val = c.get('value', '')[:30]
        domain = c.get('domain', '')
        expires = c.get('expires', -1)
        lines.append(f"  {c['name']:15s} domain={domain:20s} expires={expires} value={val}...")

lines.append("")
lines.append("所有Cookie域名分布:")
domains = {}
for c in cookies:
    d = c.get('domain', '')
    domains[d] = domains.get(d, 0) + 1
for d, count in sorted(domains.items()):
    lines.append(f"  {d}: {count}个")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('\n'.join(lines))
