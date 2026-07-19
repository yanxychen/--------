# NPL Project

## 项目简介

这是一个用于搜索司法拍卖案例的Python工具，帮助评估不良资产价值。

## 当前状态

已完成第一步：搜索功能框架实现。

### 已实现功能

1. **资产类型配置**
   - 住宅：时间范围365天，距离范围5公里
   - 商业：时间范围730天，距离范围10公里
   - 工业：时间范围730天，距离范围15公里
   - 特殊：时间范围1095天，距离范围20公里

2. **搜索平台支持**
   - 淘宝司法拍卖 (sf.taobao.com)
   - 京东拍卖 (auction.jd.com)

3. **完整代码框架**
   - 模块化设计（BaseSearcher, TaobaoSfSearcher, JDAuctionSearcher）
   - 完整的HTTP请求逻辑
   - HTML解析框架
   - 结果去重和格式化输出

### 当前限制

由于淘宝司法拍卖和京东拍卖都有严格的反爬虫保护，直接HTTP请求会返回空内容或拦截页面。

**实际测试结果：**
- 淘宝司法拍卖：返回0字符（被完全拦截）
- 京东拍卖：返回185K字符但无标准结果容器（页面结构复杂或动态加载）

## 文件结构

```
/workspace/
├── asset_search.py        # 主搜索工具脚本
├── test_search.py         # 测试示例脚本
├── requirements.txt       # Python依赖
└── README.md              # 说明文档
```

## 使用方法

### 1. 交互式使用

```bash
python asset_search.py
```

按提示输入：
- 目标地址（如：北京市朝阳区望京）
- 资产类型（选择1-4）

### 2. 演示模式

```bash
python asset_search.py --demo
```

使用预设参数演示搜索流程。

### 3. 代码调用

```python
from asset_search import AssetSearchTool

tool = AssetSearchTool()
result = tool.search_cases("北京市朝阳区", "住宅")

# 打印结果
tool.print_results(result)

# 保存结果
tool.save_results(result, "output.json")

# 直接访问数据
for item in result['results']:
    print(item['title'])
    print(item['link'])
```

### 4. 运行测试

```bash
python test_search.py
```

## 下一步计划

### 方案A：使用Selenium模拟浏览器

**优点：**
- 可以绕过反爬虫检测
- 可以处理JavaScript动态加载的页面
- 模拟真实用户行为

**实现步骤：**
```bash
pip install selenium webdriver-manager
```

示例代码：
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(ChromeDriverManager().install())
driver.get("https://sf.taobao.com/item/search.htm?q=北京市朝阳区")

# 等待页面加载
time.sleep(3)

# 提取数据
items = driver.find_elements(By.CSS_SELECTOR, ".item-list .item")
for item in items[:10]:
    title = item.find_element(By.CSS_SELECTOR, "a[title]").get_attribute("title")
    link = item.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
    print(title, link)

driver.quit()
```

### 方案B：使用第三方API

如果平台提供官方API，可以申请接入：
- 数据更稳定
- 不受反爬虫影响
- 但可能需要付费或有访问限制

### 方案C：手动搜索 + 数据录入

创建一个辅助工具：
1. 提供搜索URL链接（已实现）
2. 用户手动在浏览器中搜索
3. 提供数据录入界面
4. 保存案例数据到本地数据库

### 后续功能增强

1. **详情页解析**
   - 提取拍卖价格、评估价格
   - 提取拍卖时间、状态
   - 提取房产面积、楼层、户型

2. **距离计算**
   - 使用地图API计算实际距离
   - 精确过滤距离范围内的案例

3. **时间过滤**
   - 根据拍卖时间筛选
   - 只保留配置时间范围内的案例

4. **数据持久化**
   - SQLite数据库存储
   - 历史案例积累
   - 搜索记录保存

5. **统计分析**
   - 平均价格计算
   - 价格趋势分析
   - 案例对比报告

## 技术栈

- Python 3.6+
- requests - HTTP请求
- beautifulsoup4 - HTML解析
- lxml - XML/HTML解析器

## 安装依赖

```bash
pip install requests beautifulsoup4 lxml
```

## 手动搜索指引

由于自动搜索被拦截，建议手动访问：

1. **淘宝司法拍卖**
   - URL: https://sf.taobao.com/
   - 在搜索框输入地址关键词
   - 浏览结果列表

2. **京东拍卖**
   - URL: https://auction.jd.com/
   - 搜索司法拍卖相关内容

## 项目目标

第一步目标已达成：确认搜索框架可用，代码逻辑正确。

下一步需要解决反爬虫问题，才能获取真实数据。

## 作者说明

这是一个教学/研究性质的工具，用于学习网络爬虫和数据处理技术。

使用时应遵守：
- 各平台的用户协议
- 反爬虫相关规定
- 合理的访问频率
- 数据用途限制