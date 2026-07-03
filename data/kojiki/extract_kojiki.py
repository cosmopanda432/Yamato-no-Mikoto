#!/usr/bin/env python3
"""
古事記 HTML → markdown 抽出スクリプト

- <div id="content"> 内のみを対象 (nav/form/script 除外)
- <h1> → # / <h2> → ## (markdown header)
- <p> → 段落 (空行で区切る)
- <p class="d1"> → 引用形式 (要約段落として区別) → > 段落
- <span>X</span> → 〔X〕 (割書を視覚的に区別)
- HTML エンティティ (&...;) を decode
"""

import html
import re
import sys
from pathlib import Path

RAW_DIR = Path("/home/dev/CausalityEngine/docs/kojiki/raw")
OUT_DIR = Path("/home/dev/CausalityEngine/docs/kojiki/text")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_content(html_text: str) -> str:
    """<div id="content"> の中身だけ取り出す"""
    m = re.search(r'<div id="content">(.*?)</div>', html_text, re.DOTALL)
    if m is None:
        return ""
    return m.group(1)


def span_to_brackets(text: str) -> str:
    """<span>X</span> → 〔X〕 (割書を視覚的に区別)"""
    return re.sub(r'<span[^>]*>(.*?)</span>', r'〔\1〕', text, flags=re.DOTALL)


def convert_paragraph(p_html: str) -> str:
    """<p ...>X</p> → "X" or "> X" (d1 クラスは引用)"""
    m = re.match(r'<p\s*([^>]*)>(.*?)</p>', p_html, re.DOTALL)
    if m is None:
        return p_html
    attrs, body = m.group(1), m.group(2)
    body = span_to_brackets(body)
    body = re.sub(r'\s+', '', body).strip()  # 全角文字なので 空白圧縮 (必要なら調整)
    # でも漢文は句読点で区切られているので空白圧縮ではなく、改行のみ削除
    body = body.replace('\n', '').replace('\r', '')
    body = html.unescape(body)
    if 'class="d1"' in attrs or "class='d1'" in attrs:
        return f"> {body}"
    if 'class="clear"' in attrs:
        return ""
    return body


def convert_heading(level: int, h_html: str) -> str:
    m = re.match(rf'<h{level}[^>]*>(.*?)</h{level}>', h_html, re.DOTALL)
    if m is None:
        return ""
    text = re.sub(r'<[^>]+>', '', m.group(1))
    text = html.unescape(text).strip()
    return ('#' * level) + ' ' + text


def html_to_markdown(content_html: str) -> str:
    out_lines = []

    # 順次抽出: タグの順序を保つために逐次パース
    pattern = re.compile(r'(<h1[^>]*>.*?</h1>|<h2[^>]*>.*?</h2>|<p[^>]*>.*?</p>)',
                         re.DOTALL)
    for tag in pattern.findall(content_html):
        if tag.startswith('<h1'):
            out_lines.append(convert_heading(1, tag))
            out_lines.append('')
        elif tag.startswith('<h2'):
            out_lines.append(convert_heading(2, tag))
            out_lines.append('')
        elif tag.startswith('<p'):
            converted = convert_paragraph(tag)
            if converted:
                out_lines.append(converted)
                out_lines.append('')

    # 末尾の連続空行を整理
    while out_lines and out_lines[-1] == '':
        out_lines.pop()
    return '\n'.join(out_lines)


def get_title_from_html(html_text: str) -> str:
    m = re.search(r'<title>(.*?)</title>', html_text, re.DOTALL)
    if m:
        return html.unescape(m.group(1).strip())
    return ""


def main():
    files = sorted(RAW_DIR.glob("kojiki_*.html"))
    if not files:
        print("ERR: raw HTML 未発見", file=sys.stderr)
        sys.exit(1)

    summary = []
    for src in files:
        html_text = src.read_text(encoding='utf-8')
        title = get_title_from_html(html_text)
        content = extract_content(html_text)
        if not content:
            print(f"WARN: {src.name} に <div id=\"content\"> 無し", file=sys.stderr)
            continue
        md = html_to_markdown(content)
        # 先頭にメタ情報を追加
        meta = f"<!-- source: https://www.seisaku.bz/kojiki/{src.name} -->\n"
        meta += f"<!-- title: {title} -->\n\n"
        out = meta + md + "\n"

        out_path = OUT_DIR / (src.stem + ".md")
        out_path.write_text(out, encoding='utf-8')
        chars = len(md)
        summary.append((src.name, title, chars))

    print("=== 抽出結果 ===")
    for name, title, chars in summary:
        print(f"  {name} ({chars:>5} chars) — {title}")


if __name__ == '__main__':
    main()
