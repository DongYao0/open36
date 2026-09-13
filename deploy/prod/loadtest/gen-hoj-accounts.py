#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量创建 HOJ 压测账号（走公开注册接口，仅限压测环境）。

用法（Windows 本机，对 LAN）：
  python gen-hoj-accounts.py --base http://172.20.193.162:8080 \
      --count 170 --prefix ltc --password 'LtHoj#0436' --out hoj-accounts.txt

产出 user:pass 每行一条（k6 HOJ_ACCOUNTS_FILE）。已存在的账号（重跑）自动跳过。
密码只落在本地文件（loadtest/ 下已 gitignore），不入库不入仓。
"""
import argparse
import json
import sys
import time
import urllib.request

def post(base, path, body):
    req = urllib.request.Request(base + path,
                                 data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'},
                                 method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8', 'replace'))
        except Exception:
            return e.code, {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://172.20.193.162:8080')
    ap.add_argument('--count', type=int, default=170)
    ap.add_argument('--prefix', default='ltc')
    ap.add_argument('--password', default='LtHoj#0436')
    ap.add_argument('--out', default='hoj-accounts.txt')
    args = ap.parse_args()

    created, skipped, failed = 0, 0, 0
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# HOJ 压测账号（自动生成，勿提交）\n')
        for i in range(1, args.count + 1):
            username = f'{args.prefix}{i}'
            status, body = post(args.base, '/api/register', {
                'username': username, 'password': args.password,
                'realName': f'压测选手{i}', 'email': f'{username}@lt.local',
            })
            msg = (body or {}).get('msg', '')
            if status == 200:
                created += 1
            elif '存在' in msg or 'exist' in msg.lower():
                skipped += 1  # 重跑：已存在视为成功
            else:
                failed += 1
                print(f'WARN {username}: HTTP {status} {msg}', file=sys.stderr)
                time.sleep(0.5)
            f.write(f'{username}:{args.password}\n')
            time.sleep(0.05)
    print(f'done: created={created} skipped={skipped} failed={failed} -> {args.out}')

if __name__ == '__main__':
    main()
