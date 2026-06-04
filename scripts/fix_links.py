#!/usr/bin/env python3
"""
fix_links.py

Run from the repository root. This script updates HTML files by converting leading-root
absolute internal links (href="/..." or src="/...") to relative paths suitable
for GitHub Pages project sites (e.g. remove leading "/" or "/Hillai/").

Usage:
  pip install beautifulsoup4
  python3 scripts/fix_links.py

It will create .bak backups of files it modifies and print a summary of changes and
any potential broken links (targets that do not exist, case-sensitive).
"""

import os
import re
from bs4 import BeautifulSoup

REPO_BASENAME = "Hillai"  # adjust if the repo folder name differs on GitHub Pages

HTML_EXTS = ('.html', '.htm')

def is_external(url):
    if not url or url.strip() == '':
        return True
    url = url.strip()
    return url.startswith('http://') or url.startswith('https://') or url.startswith('//') or url.startswith('mailto:') or url.startswith('tel:') or url.startswith('#')

def normalize_internal(href):
    if href.startswith('/' + REPO_BASENAME + '/'):
        return href[len('/' + REPO_BASENAME + '/'):] 
    if href.startswith('/'):
        return href[1:]
    return href

def file_exists(target, src_dir):
    # Remove query and hash
    t = target.split('?',1)[0].split('#',1)[0]
    # If it's an absolute path now (starts with /) normalize
    if t.startswith('/'):
        t = t[1:]
    # If it's a path relative to the current HTML file directory, join
    candidate = os.path.normpath(os.path.join(src_dir, t))
    return os.path.exists(candidate)

changed = []
broken = []

for root, dirs, files in os.walk('.'):
    # skip .git and scripts directory backup
    if root.startswith('./.git'):
        continue
    for name in files:
        if not name.lower().endswith(HTML_EXTS):
            continue
        path = os.path.join(root, name)
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        modified = False
        # process href
        for tag in soup.find_all(href=True):
            href = tag['href']
            if is_external(href):
                continue
            if href.startswith('/') or href.startswith('/' + REPO_BASENAME + '/'):
                new = normalize_internal(href)
                tag['href'] = new
                modified = True
                if not file_exists(new, os.path.dirname(path)):
                    broken.append((path, href, new))
        # process src
        for tag in soup.find_all(src=True):
            src = tag['src']
            if is_external(src):
                continue
            if src.startswith('/') or src.startswith('/' + REPO_BASENAME + '/'):
                new = normalize_internal(src)
                tag['src'] = new
                modified = True
                if not file_exists(new, os.path.dirname(path)):
                    broken.append((path, src, new))
        if modified:
            bak = path + '.bak'
            if not os.path.exists(bak):
                with open(bak, 'w', encoding='utf-8') as bf:
                    bf.write(html)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            changed.append(path)

print('\nChanged files:')
for p in changed:
    print(' -', p)

if broken:
    print('\nPotential broken links (after normalization):')
    for path, old, new in broken:
        print(f" - {path}: {old} -> {new} (target exists? check case-sensitivity)")
else:
    print('\nNo potential broken links found by the script.')
