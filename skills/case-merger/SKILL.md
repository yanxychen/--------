# 多次拍卖合并 Skill

把同一个抵押物的多次拍卖（一拍、二拍、变卖等）合并成一条记录，避免重复计数，同时保留历史拍卖记录。

## 功能描述

- 识别同一抵押物的多次拍卖
- 合并为一条主记录（保留最新的拍卖）
- 保留所有历史拍卖记录（按时间排序）
- 输出合并日志

## 触发方式

### 自然语言触发
- "合并同一个房子的多次拍卖"
- "把一拍二拍合并成一条"
- "去重同一抵押物的拍卖"
- "整理拍卖历史"

### 代码调用
```typescript
import { CaseMerger } from './case-merger';

const merger = new CaseMerger({
  addressSimilarityThreshold: 0.8,
  areaTolerance: 0.1,
});

const result = merger.merge(cases);

console.log('合并后案例数:', result.mergedCases.length);
console.log('合并组数:', result.mergeCount);
```

## 输入输出

### 输入
- `cases: Case[]` - 案例列表（详情页补全后的数据）

### 输出
- `mergedCases: MergedCase[]` - 合并后的案例列表
- `mergeCount: number` - 合并了多少组
- `mergeLog: MergeLogEntry[]` - 合并日志

### 合并后的数据结构
```typescript
interface MergedCase {
  itemId: string;
  platform: 'taobao' | 'jd';
  title: string;
  fullAddress: string;
  buildingArea: number;
  marketValue: number;
  unitPrice: number;
  auctionRound: string;
  auctionStatus: string;
  auctionTime: string;
  priceType: string;
  detailUrl: string;
  auctionHistory: AuctionHistoryItem[];
}

interface AuctionHistoryItem {
  itemId: string;
  round: string;
  price: number;
  time: string;
  status: string;
  detailUrl: string;
}
```

## 合并判断规则

两个条件同时满足，才认为是同一个抵押物：

| 条件 | 规则 | 容错范围 |
|-----|------|---------|
| 地址相同 | 核心地址部分一致 | 文本相似度 ≥ 80% |
| 面积相同 | 建筑面积接近 | 误差 ± 10% |

## 主案例选择规则

保留最新的一次拍卖作为主案例（显示在列表中）：

**优先级（从高到低）：**
1. 变卖
2. 二拍
3. 一拍

同轮次按时间排序，取最新的。

## 历史拍卖记录

- 同一抵押物的所有拍卖记录都存入 `auctionHistory`
- 按时间从新到旧排序
- 每次记录包含：轮次、价格、时间、状态、链接

## 分组算法

```
1. 遍历所有案例
2. 为每个案例计算"分组键"
   ├─ 规范化地址（去掉房号、单元号等）
   └─ 面积取整
3. 按分组键分组
4. 对每组内的案例：
   ├─ 两两比较地址相似度 + 面积差
   └─ 都符合的合并到一起
5. 对每组选择主案例
6. 整理历史记录
```

## 特殊情况

| 情况 | 处理方式 |
|-----|---------|
| 只有一次拍卖 | 不合并，原样返回，auctionHistory 只有一条 |
| 地址能匹配但面积缺失 | 只靠地址判断（降低置信度） |
| 面积能匹配但地址缺失 | 只靠面积判断（降低置信度） |
| 跨平台同一抵押物 | 合并，主案例取淘宝的（如有） |

## 版本号

v1.0.0

## 目录结构

```
case-merger/
├── SKILL.md                 # Skill说明文档
├── src/
│   ├── types.ts             # 类型定义
│   ├── constants.ts         # 常量配置
│   ├── index.ts             # 主入口
│   ├── grouper.ts           # 分组器
│   └── merger.ts            # 合并引擎
├── tests/
│   └── basic.test.ts        # 基础测试
└── examples/
    └── basic-usage.ts       # 使用示例
```
