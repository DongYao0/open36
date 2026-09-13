#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量创建 HOJ 压测账号（root 管理端批量导入，公开注册有验证码不可用）。

用法（Windows 本机）：
  HOJ_ADMIN_USER=root HOJ_ADMIN_PASS=*** python gen-hoj-accounts.py \
      --base http://172.20.193.162:8080 --count 170 \
      --prefix ltc --password 'LtHoj#0436' --out hoj-accounts.txt

行格式（HOJ AdminUserManager.addNewUser）：
  [username, password(明文，服务端MD5), email, realname, gender, nickname, school]
产出 user:pass 每行一条（k6 HOJ_ACCOUNTS_FILE）。账号文件已 gitignore。
"""
import argparse
import getpass
import json
import os
import re
import sys
import time
import urllib.request


def post_json(base, path, body, headers=None, timeout=30):
    h = {'Content-Type': 'application/json'}
    h.update(headers or {})
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(),
                                 headers=h, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8', 'replace')), dict(resp.headers)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8', 'replace')), {}
        except Exception:
            return e.code, {}, {}


def login(base, user, password):
    req = urllib.request.Request(
        base + '/api/login',
        data=json.dumps({'username': user, 'password': password}).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=15) as resp:
        token = resp.headers.get('Authorization')
        resp.read()
    return token


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://172.20.193.162:8080')
    ap.add_argument('--count', type=int, default=170)
    ap.add_argument('--prefix', default='ltc')
    ap.add_argument('--password', default='LtHoj#0436')
    ap.add_argument('--out', default='hoj-accounts.txt')
    args = ap.parse_args()

    admin_user = os.environ.get('HOJ_ADMIN_USER') or input('HOJ root 用户名: ').strip()
    admin_pass = os.environ.get('HOJ_ADMIN_PASS') or getpass.getpass('HOJ root 密码: ')

    token = login(args.base, admin_user, admin_pass)
    if not token:
        print('root 登录失败：无 Authorization 头', file=sys.stderr)
        sys.exit(2)
    print('root 登录成功（token %d 字符）' % len(token))

    users = [[f'{args.prefix}{i}', args.password, f'{args.prefix}{i}@lt.local',
              f'压测选手{i}', 'male', f'LT选手{i}', 'Open436压测']
             for i in range(1, args.count + 1)]

    created, failed = 0, 0
    CHUNK = 50
    for c in range(0, len(users), CHUNK):
        chunk = users[c:c + CHUNK]
        st, body, _ = post_json(args.base, '/api/admin/user/insert-batch-user',
                                {'users': chunk}, headers={'Authorization': token})
        msg = (body or {}).get('msg', '') or ''
        if st == 200:
            created += len(chunk)
        else:
            m = re.search(r'成功数：(\d+),\s+失败数：(\d+)', msg)
            if m:
                created += int(m.group(1))
                failed += int(m.group(2))
            else:
                failed += len(chunk)
                print(f'WARN chunk: HTTP {st} {msg[:150]}', file=sys.stderr)
        time.sleep(0.3)

    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# HOJ 压测账号（自动生成，勿提交）\n')
        for u in users:
            f.write(f'{u[0]}:{u[1]}\n')
    print(f'done: created/imported={created} failed={failed} -> {args.out}')
    # 校验：抽查一个账号能登录
    probe_user, probe_pass = users[0][0], users[0][1]
    try:
        t = login(args.base, probe_user, probe_pass)
        print(f'probe login {probe_user}: {"OK" if t else "FAIL"}')
    except Exception as e:
        print(f'probe login {probe_user}: FAIL {e}', file=sys.stderr)


if __name__ == '__main__':
    main()
