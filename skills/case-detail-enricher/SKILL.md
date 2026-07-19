# 案例详情补全 Skill

打开每个拍卖案例的详情页，爬取完整数据，确保8列输出的所有字段都有准确值。

## 功能描述

- 淘宝拍卖详情页数据爬取（需登录状态）
- 京东拍卖详情页数据爬取
- 补全建筑面积、起拍时间、拍卖状态等关键字段
- 失败重试机制
- 进度与失败日志

## 触发方式

### 自然语言触发
- "打开详情页补全数据"
- "爬取详情页信息"
- "补全建筑面积和起拍时间"
- "获取完整的拍卖数据"

### 代码调用
```typescript
import { CaseDetailEnricher } from './case-detail-enricher';

const enricher = new CaseDetailEnricher({
  maxRetries: 2,
  concurrency: 3,
  delay: 1000,
});

const result = await enricher.enrich(cases, {
  platform: 'taobao',
});

console.log('成功补全:', result.enrichCount);
console.log('失败:', result.failCount);
console.log('补全后案例:', result.enrichedCases);
```

## 输入输出

### 输入
- `cases: AuctionCase[]` - 原始案例列表（列表页数据）
- `options.platform?: 'taobao' | 'jd'` - 平台（从案例中自动识别）
- `options.maxRetries?: number` - 最大重试次数，默认2
- `options.concurrency?: number` - 并发数，默认3
- `options.delay?: number` - 请求间隔（毫秒），默认1000

### 输出
- `enrichedCases: EnrichedCase[]` - 补全后的案例列表
- `enrichCount: number` - 成功补全的数量
- `failCount: number` - 补全失败的数量
- `failLog: FailLogEntry[]` - 失败日志

### 补全后的数据结构
```typescript
interface EnrichedCase {
  itemId: string;
  platform: 'taobao' | 'jd';
  title: string;
  fullAddress: string;
  buildingArea: number;
  landArea?: number;
  marketValue: number;
  unitPrice: number;
  startPrice: number;
  auctionTime: string;
  auctionStatus: string;
  auctionRound: string;
  priceType: string;
  detailUrl: string;
  bidCount?: number;
  court?: string;
}
```

## 必须补全的字段（8列输出所需）

| 字段 | 说明 | 失败处理 |
|-----|------|---------|
| fullAddress | 完整地址 | 用列表页地址兜底 |
| buildingArea | 建筑面积（㎡） | 必须获取，失败则标记 |
| landArea | 土地面积（㎡） | 房产类显示"不适用" |
| marketValue | 市场价值（万元） | 起拍价或成交价 |
| unitPrice | 建筑单价（元/㎡） | 市场价值 ÷ 建筑面积 |
| auctionTime | 起拍时间 | 必须获取 |
| auctionStatus | 拍卖状态 | 必须获取 |
| startPrice | 起拍价 | 必须获取 |
| detailUrl | 详情页链接 | 用于数据来源列跳转 |
| priceType | 价格类型 | 默认"普通司法拍卖" |

## 拍卖状态枚举

只有以下几种状态：
- 即将开始
- 正在进行
- 已成交
- 流拍
- 变卖失败

## 爬取策略

### 淘宝详情页
- 使用 Playwright + 登录状态
- 页面加载完成后提取数据
- 支持多种页面结构

### 京东详情页
- 直接请求 + DOM解析
- 或 Playwright 方式

### 并发控制
- 默认同时处理3个案例
- 每个请求间隔1秒
- 防止被限流

### 失败重试
- 每个案例最多重试2次
- 记录失败原因
- 失败案例保留列表页数据

## 日期提取模式

支持多种日期格式：
- "开拍时间：2024年10月15日 10:00"
- "拍卖开始时间：2024-10-15 10:00:00"
- "起拍时间：2024/10/15"
- "变卖开始时间：..."

## 版本号

v1.0.0

## 目录结构

```
case-detail-enricher/
├── SKILL.md                   # Skill说明文档
├── src/
│   ├── types.ts               # 类型定义
│   ├── constants.ts           # 常量配置
│   ├── index.ts               # 主入口
│   ├── base-enricher.ts       # 补全器基类
│   ├── taobao-enricher.ts     # 淘宝详情补全
│   ├── jd-enricher.ts         # 京东详情补全
│   └── date-parser.ts         # 日期解析器
├── tests/
│   └── basic.test.ts          # 基础测试
└── examples/
    └── basic-usage.ts         # 使用示例
```
