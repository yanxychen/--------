# 案例过滤引擎 Skill

按规则筛选符合要求的案例，采用多档位逐步放宽策略，确保既精准又有足够的参考案例。

## 功能描述

- 类型过滤（资产类型匹配）
- 距离过滤（从近到远，逐步放宽）
- 时间过滤（从新到旧，逐步放宽）
- 多档位逐步放宽策略
- 自身拍卖豁免（不受时间限制）

## 触发方式

### 自然语言触发
- "过滤一下这些案例"
- "筛选符合条件的案例"
- "按距离和时间筛选"
- "不够3个就放宽条件"

### 代码调用
```typescript
import { CaseFilter } from './case-filter';

const filter = new CaseFilter({
  propertyType: 'residential',
  minCases: 3,
});

const result = filter.filter(cases, {
  selfAuctionItemIds: ['case1', 'case2'],
});

console.log('过滤后案例数:', result.filteredCases.length);
console.log('使用的距离阈值:', result.usedDistanceThreshold);
console.log('使用的时间阈值:', result.usedTimeThreshold);
```

## 输入输出

### 输入
- `cases: Case[]` - 案例列表（合并后的案例）
- `propertyType: string` - 资产类型
- `assetType: string` - 资产大类中文
- `selfAuctionItemIds?: string[]` - 自身拍卖ID列表（不受时间限制）
- `minCases?: number` - 最少案例数，默认3
- `mode?: 'rough' | 'fine'` - 粗筛模式/精筛模式

### 输出
- `filteredCases: Case[]` - 过滤后的案例列表
- `filterLog: FilterLogEntry[]` - 过滤日志
- `usedDistanceThreshold: number` - 最终使用的距离阈值（米）
- `usedTimeThreshold: number` - 最终使用的时间阈值（天）
- `distanceLevel: number` - 距离档位
- `timeLevel: number` - 时间档位

## 过滤配置规则

### 距离档位（从近到远）

| 档位 | 住宅/商业 | 工业/土地/特殊资产 |
|-----|----------|------------------|
| 1 | ≤ 500m | ≤ 1km |
| 2 | ≤ 1km | ≤ 3km |
| 3 | ≤ 2km | ≤ 5km |
| 4 | ≤ 3km（首选） | ≤ 10km（首选） |
| 5 | ≤ 5km（放宽） | - |

### 时间档位（从新到旧）

| 档位 | 所有类型 |
|-----|---------|
| 1 | ≤ 90天（3个月） |
| 2 | ≤ 180天（6个月） |
| 3 | ≤ 365天（1年/首选） |
| 4 | ≤ 730天（2年/放宽） |

## 逐步放宽流程

```
起点：最近距离档 + 最新时间档
    ↓
够 minCases 个？→ 是 → 结束
    ↓ 否
放宽距离（下一档距离）
    ↓
够 minCases 个？→ 是 → 结束
    ↓ 否
放宽时间（下一档时间）
    ↓
够 minCases 个？→ 是 → 结束
    ↓ 否
继续放宽，直到到达最大阈值
    ↓
最终：返回所有符合最大阈值的案例
```

## 过滤类型

### 粗筛模式（rough）
- 只用类型 + 直线距离
- 用于详情页补全前的初步筛选
- 阈值适当放宽，避免漏掉

### 精筛模式（fine）
- 类型 + 驾车距离 + 起拍时间
- 用于详情页补全后的精确筛选
- 多档位逐步放宽

## 特殊规则

- **自身拍卖豁免**：抵押物自身拍卖案例不受时间限制，任何档位都包含
- **类型必过**：类型不匹配的直接过滤掉，不参与放宽
- **无数据处理**：无距离/时间数据的案例，在最后档位兜底保留

## 版本号

v1.0.0

## 目录结构

```
case-filter/
├── SKILL.md                # Skill说明文档
├── src/
│   ├── types.ts            # 类型定义
│   ├── constants.ts        # 档位配置
│   ├── index.ts            # 主入口
│   ├── type-filter.ts      # 类型过滤器
│   ├── distance-filter.ts  # 距离过滤器
│   ├── time-filter.ts      # 时间过滤器
│   └── relax-engine.ts     # 放宽引擎
├── tests/
│   └── basic.test.ts       # 基础测试
└── examples/
    └── basic-usage.ts      # 使用示例
```
