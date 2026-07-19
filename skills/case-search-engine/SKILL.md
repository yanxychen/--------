# 多平台分层搜索 Skill

从淘宝拍卖和京东拍卖搜索候选案例，采用分层关键词策略，确保搜索结果全面覆盖抵押物周边的拍卖案例。

## 功能描述

- 淘宝拍卖搜索（sf.taobao.com）
- 京东拍卖搜索（auction.jd.com）
- 分层关键词搜索（从细到粗，确保覆盖率）
- 跨平台结果去重
- 搜索日志记录

## 触发方式

### 自然语言触发
- "搜索一下这个地址附近的拍卖案例"
- "找一下淘宝上的拍卖信息"
- "搜一下京东拍卖"
- "多平台搜索拍卖案例"

### 代码调用
```typescript
import { CaseSearchEngine } from './case-search-engine';

const engine = new CaseSearchEngine({
  taobaoEnabled: true,
  jdEnabled: true,
  maxPages: 3,
  pageSize: 20,
});

const result = await engine.search({
  keywords: ['滨海御庭', '禅城区', '佛山市'],
  propertyType: 'residential',
  assetType: '住宅',
});

console.log('找到案例数:', result.totalCount);
console.log('案例列表:', result.cases);
```

## 输入输出

### 输入
- `keywords: string[]` - 分层关键词列表（从细到粗）
- `propertyType: string` - 资产类型（residential/commercial/industrial/land/special）
- `assetType: string` - 资产大类中文（住宅/商业/工业/土地/特殊资产）
- `maxPages?: number` - 每个关键词搜索页数，默认3
- `pageSize?: number` - 每页条数，默认20
- `platforms?: ('taobao' | 'jd')[]` - 指定平台，默认都搜

### 输出
- `cases: AuctionCase[]` - 候选案例列表（已去重）
- `totalCount: number` - 去重后的案例总数
- `platforms: string[]` - 实际使用的平台
- `searchLog: SearchLogEntry[]` - 搜索日志

### 案例数据结构
```typescript
interface AuctionCase {
  itemId: string;
  platform: 'taobao' | 'jd';
  title: string;
  currentPrice: number;
  location: string;
  detailUrl: string;
  searchKeyword: string;
  auctionStatus?: string;
  category?: string;
}
```

## 搜索策略

### 分层关键词优先级
```
第1层：完整小区名 + 楼栋（最精确，结果少但准）
第2层：小区名/楼盘名
第3层：商圈/街道
第4层：行政区
第5层：城市名（最宽泛，结果多但杂）
```

### 淘宝搜索
- 域名：sf.taobao.com
- 需要登录状态
- 每个关键词搜3页，每页20条
- 按 itemId 去重

### 京东搜索
- 域名：auction.jd.com
- 不需要登录
- 每个关键词搜3页，每页20条
- 按 itemId 去重

### 去重规则
- 同平台：按 itemId 去重
- 跨平台：按标题+地址相似度判断（保留淘宝的）

## 搜索流程

```
1. 遍历分层关键词（从细到粗）
   ├─ 搜淘宝
   ├─ 搜京东
   └─ 收集结果

2. 按平台去重（itemId）

3. 跨平台去重（标题+地址）

4. 记录搜索日志
   ├─ 关键词
   ├─ 平台
   ├─ 结果数
   └─ 耗时

5. 返回结果
```

## 配置选项

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `maxPages` | number | 3 | 每个关键词搜索页数 |
| `pageSize` | number | 20 | 每页条数 |
| `taobaoEnabled` | boolean | true | 是否启用淘宝搜索 |
| `jdEnabled` | boolean | true | 是否启用京东搜索 |
| `deduplicate` | boolean | true | 是否去重 |

## 版本号

v1.0.0

## 目录结构

```
case-search-engine/
├── SKILL.md              # Skill说明文档
├── src/
│   ├── types.ts          # 类型定义
│   ├── constants.ts      # 常量配置
│   ├── index.ts          # 主入口
│   ├── base-searcher.ts  # 搜索器基类
│   ├── taobao-searcher.ts # 淘宝搜索
│   ├── jd-searcher.ts    # 京东搜索
│   └── deduplicator.ts   # 去重器
├── tests/
│   └── basic.test.ts     # 基础测试
└── examples/
    └── basic-usage.ts    # 使用示例
```
