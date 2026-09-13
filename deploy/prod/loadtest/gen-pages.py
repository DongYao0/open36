#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对着真实部署生成 pages.generated.js（压测页面资源清单）。

用法（Windows 本机）：
  python deploy/prod/loadtest/gen-pages.py --base http://172.20.193.162:8080

抓取各页面 HTML，解析出实际引用的哈希 js/css/图片，采样荣誉相册图片，
生成 k6 可 import 的 PAGE_GROUPS。
"""
import argparse
import json
import re
import sys
import urllib.request


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'loadtest-gen/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode('utf-8', 'replace')


def assets_from_html(base, html):
    out = []
    for m in re.finditer(r'(?:src|href)=["\']([^"\']+)["\']', html):
        u = m.group(1)
        if u.startswith('http') or u.startswith('data:'):
            continue
        if not re.search(r'\.(js|css|png|jpe?g|svg|webp|glb)(\?|$)', u):
            continue
        if not u.startswith('/'):
            u = '/' + u
        out.append(u)
    # 保持顺序去重
    seen, dedup = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            dedup.append(u)
    return dedup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://172.20.193.162:8080')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    base = args.base.rstrip('/')
    out_path = args.out or 'deploy/prod/loadtest/pages.generated.js'

    landing_html = fetch(base + '/')
    app_html = fetch(base + '/app/')
    forum_html = fetch(base + '/app/forum')

    landing_assets = assets_from_html(base, landing_html)[:8]   # 主 bundle + 字体图
    app_assets = assets_from_html(base, app_html)[:8]
    # /honors/ 目录无 autoindex；从部署 dist 固定采样真实图片
    honors_imgs = [
        '/honors/baidu/01.jpg', '/honors/lanqiao/01.jpg',
        '/honors/team/01.jpg', '/honors/mati/01.jpg',
    ]
    for probe in list(honors_imgs):
        try:
            fetch(base + probe)
        except Exception:
            honors_imgs.remove(probe)

    groups = [
        {'name': 'home', 'weight': 30,
         'static': ['/'] + landing_assets,
         'api': ['/api/users/homepage/public']},
        {'name': 'app-home', 'weight': 10,
         'static': ['/app/'] + app_assets + ['/app/user.jpg'],
         'api': ['/api/sections/']},
        {'name': 'forum', 'weight': 25,
         'static': ['/app/'],
         'api': ['/api/sections/', '/api/posts/?page=1&page_size=20']},
        {'name': 'resources', 'weight': 15,
         'static': ['/app/'],
         'api': ['/api/posts/?section=share&page=1&page_size=20']},
        {'name': 'contests', 'weight': 10,
         'static': ['/app/'],
         'api': ['/api/sections/']},
        {'name': 'honors', 'weight': 10,
         # /honors/ 目录无 autoindex（404），只请求真实图片
         'static': honors_imgs,
         'api': []},
    ]

    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('// 自动生成：python gen-pages.py --base %s\n' % base)
        f.write('// 请勿手改；部署变化后重新生成。\n')
        f.write('export const PAGE_GROUPS = ')
        f.write(json.dumps(groups, ensure_ascii=False, indent=2))
        f.write(';\n')
    total_assets = sum(len(g['static']) for g in groups)
    print('generated %s: %d groups, %d static refs' % (out_path, len(groups), total_assets))


if __name__ == '__main__':
    sys.exit(main())
