#!/usr/bin/env python3
"""MD转PDF脚本"""
import markdown
from weasyprint import HTML
import os

md_file = '/workspace/估值案例报告.md'
pdf_file = '/workspace/估值案例报告.pdf'

with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
        margin: 40px;
        color: #333;
        line-height: 1.6;
        font-size: 13px;
    }}
    h1 {{
        color: #2c7a8c;
        border-bottom: 3px solid #409DAD;
        padding-bottom: 12px;
        font-size: 24px;
    }}
    h2 {{
        color: #2d3748;
        margin-top: 35px;
        font-size: 18px;
        border-left: 4px solid #409DAD;
        padding-left: 12px;
    }}
    h3 {{
        color: #4a5568;
        font-size: 15px;
        margin-top: 20px;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
        font-size: 12px;
    }}
    th {{
        background-color: #409DAD;
        color: white;
        padding: 10px 8px;
        text-align: left;
        border: 1px solid #36899a;
    }}
    td {{
        padding: 8px;
        border: 1px solid #e2e8f0;
        color: #4a5568;
    }}
    tr:nth-child(even) {{
        background-color: #f8fafc;
    }}
    tr:hover {{
        background-color: #edf2f7;
    }}
    strong {{
        color: #2d3748;
    }}
    hr {{
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 30px 0;
    }}
    em {{
        color: #718096;
        font-size: 12px;
    }}
    @page {{
        size: A4 landscape;
        margin: 1.5cm;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>'''

with open(pdf_file, 'wb') as f:
    f.write(HTML(string=html).write_pdf())

print(f'PDF生成成功: {pdf_file}')
print(f'文件大小: {os.path.getsize(pdf_file) / 1024:.1f} KB')
