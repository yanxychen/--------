#!/bin/bash
# 不良资产估值工具 - 打包脚本

echo "=========================================="
echo "打包不良资产估值工具"
echo "=========================================="

echo ""
echo "1. 安装核心依赖..."
pip install requests openpyxl pyinstaller -q

echo ""
echo "2. 打包轻量版 (估值+API模式)..."
rm -rf dist/asset_valuation
pyinstaller --clean --onefile \
    --name asset_valuation \
    --console \
    --hidden-import=asset_search_api \
    --hidden-import=asset_valuation_tool \
    --hidden-import=excel_renderer \
    --hidden-import=requests \
    --hidden-import=openpyxl \
    --hidden-import=openpyxl.styles \
    --hidden-import=openpyxl.utils \
    --hidden-import=urllib3 \
    --hidden-import=charset_normalizer \
    --hidden-import=idna \
    --hidden-import=certifi \
    --hidden-import=bs4 \
    --exclude-module=tkinter \
    --exclude-module=matplotlib \
    --exclude-module=numpy \
    --exclude-module=pandas \
    --exclude-module=PIL \
    --exclude-module=selenium \
    --exclude-module=webdriver_manager \
    cli.py

echo ""
if [ -f "dist/asset_valuation" ]; then
    echo "✅ 轻量版打包成功！"
    echo ""
    echo "可执行文件位置: dist/asset_valuation"
    echo ""
    ls -lh dist/asset_valuation
else
    echo "❌ 轻量版打包失败，请检查错误信息"
    exit 1
fi

echo ""
echo "3. 安装Selenium依赖（完整版）..."
pip install selenium webdriver-manager beautifulsoup4 lxml -q

echo ""
echo "4. 打包完整版 (估值+API+Selenium)..."
rm -rf dist/asset_valuation_full
pyinstaller --clean --onefile \
    --name asset_valuation_full \
    --console \
    --hidden-import=asset_search_api \
    --hidden-import=asset_search_selenium \
    --hidden-import=asset_valuation_tool \
    --hidden-import=excel_renderer \
    --hidden-import=requests \
    --hidden-import=selenium \
    --hidden-import=selenium.webdriver \
    --hidden-import=selenium.webdriver.chrome \
    --hidden-import=selenium.webdriver.chrome.webdriver \
    --hidden-import=selenium.webdriver.chrome.service \
    --hidden-import=selenium.webdriver.chrome.options \
    --hidden-import=selenium.webdriver.common.by \
    --hidden-import=selenium.webdriver.common.keys \
    --hidden-import=selenium.webdriver.support.ui \
    --hidden-import=selenium.webdriver.support.expected_conditions \
    --hidden-import=selenium.common.exceptions \
    --hidden-import=webdriver_manager \
    --hidden-import=webdriver_manager.chrome \
    --hidden-import=openpyxl \
    --hidden-import=openpyxl.styles \
    --hidden-import=openpyxl.utils \
    --hidden-import=urllib3 \
    --hidden-import=charset_normalizer \
    --hidden-import=idna \
    --hidden-import=certifi \
    --hidden-import=lxml \
    --hidden-import=lxml.etree \
    --hidden-import=bs4 \
    --exclude-module=tkinter \
    --exclude-module=matplotlib \
    --exclude-module=numpy \
    --exclude-module=pandas \
    --exclude-module=PIL \
    cli.py

echo ""
if [ -f "dist/asset_valuation_full" ]; then
    echo "✅ 完整版打包成功！"
    echo ""
    echo "可执行文件位置: dist/asset_valuation_full"
    echo ""
    ls -lh dist/asset_valuation_full
else
    echo "❌ 完整版打包失败，请检查错误信息"
fi

echo ""
echo "=========================================="
echo "打包完成！"
echo "=========================================="
echo ""
echo "使用方法:"
echo "  # 轻量版 (推荐，快速)"
echo "  ./dist/asset_valuation --help"
echo "  ./dist/asset_valuation valuation 北京 --type 住宅 --excel result.xlsx"
echo "  ./dist/asset_valuation search 北京 --type 住宅"
echo ""
echo "  # 完整版 (包含Selenium模式)"
echo "  ./dist/asset_valuation_full --help"
echo "  ./dist/asset_valuation_full valuation 上海 --type 商业 --sub-type 商铺 --excel result.xlsx"
