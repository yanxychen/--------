# 抵押物自身拍卖识别 Skill

识别哪些拍卖案例是抵押物自身的拍卖，这些案例需要特殊处理（不受时间限制、单独列示、最有参考价值）。

## 功能描述

- 基于地址相似度判断是否为同一抵押物
- 基于建筑面积接近度辅助判断
- 多等级匹配置信度
- 分离自身拍卖和其他案例

## 触发方式

### 自然语言触发
- "找出抵押物自身的拍卖"
- "判断是不是同一个房子"
- "识别自身拍卖案例"
- "哪些是抵押物本身的拍卖"

### 代码调用
```typescript
import { SelfAuctionDetector } from './self-auction-detector';

const detector = new SelfAuctionDetector({
  addressSimilarityThreshold: 0.85,
  areaTolerance: 0.1,
});

const result = detector.detect(cases, {
  targetAddress: '佛山市禅城区滨海御庭1座201室',
  targetArea: 120,
});

console.log('自身拍卖数:', result.selfAuctionCases.length);
console.log('其他案例数:', result.otherCases.length);
```

## 输入输出

### 输入
- `cases: Case[]` - 案例列表
- `targetAddress: string` - 抵押物地址
- `targetArea?: number` - 抵押物建筑面积（选填，用于面积匹配）
- `targetLng?: number` - 抵押物经度（选填，辅助判断）
- `targetLat?: number` - 抵押物纬度（选填，辅助判断）

### 输出
- `selfAuctionCases: Case[]` - 抵押物自身拍卖的案例
- `selfAuctionItemIds: string[]` - 自身拍卖的ID列表
- `otherCases: Case[]` - 其他案例（非自身拍卖）
- `matchDetails: MatchDetail[]` - 每个案例的匹配详情

### 匹配详情结构
```typescript
interface MatchDetail {
  itemId: string;
  isSelfAuction: boolean;
  matchType: 'address_area' | 'address_only' | 'area_only' | 'location' | 'none';
  addressSimilarity: number;
  areaSimilarity: number;
  locationDistance?: number;
  confidence: number;
}
```

## 识别规则

### 核心判断条件
两个条件同时满足，认为是同一抵押物：

| 条件 | 规则 | 容错范围 |
|-----|------|---------|
| 地址匹配 | 核心地址部分一致 | 文本相似度 ≥ 85% |
| 面积匹配 | 建筑面积接近 | 误差 ± 10% |

### 匹配等级（从高到低）

| 等级 | 匹配方式 | 说明 | 置信度 |
|-----|---------|------|--------|
| 1 | 地址 + 面积都匹配 | 最准确 | 高（90-100） |
| 2 | 地址完全匹配（面积缺失） | 地址完全一样 | 中高（75-85） |
| 3 | 经纬度距离很近（≤ 100m）+ 面积匹配 | 位置很近+面积对得上 | 中（70-80） |
| 4 | 只有地址高度匹配（≥ 90%） | 地址几乎一样 | 中（65-75） |
| 5 | 都不匹配 | 不是自身拍卖 | 低（0-50） |

### 地址匹配规则
1. 去掉房号、单元号、楼层号等细粒度信息
2. 提取核心地址（小区名+楼栋）
3. 计算文本相似度
4. 相似度 ≥ 85% 认为是同一地址

### 面积匹配规则
- 公式：|案例面积 - 抵押物面积| / 抵押物面积 ≤ 10%
- 面积缺失时降级为只靠地址判断

## 特殊处理

- **自身拍卖案例不受时间限制**：在 case-filter 中要豁免
- **自身拍卖单独列示**：在最终输出中放在最前面或单独区块
- **不参与评分排序**：自身拍卖是最直接的参考，不用评分

## 版本号

v1.0.0

## 目录结构

```
self-auction-detector/
├── SKILL.md                    # Skill说明文档
├── src/
│   ├── types.ts                # 类型定义
│   ├── constants.ts            # 常量配置
│   ├── index.ts                # 主入口
│   ├── address-matcher.ts      # 地址匹配器
│   ├── area-matcher.ts         # 面积匹配器
│   └── detector.ts             # 检测引擎
├── tests/
│   └── basic.test.ts           # 基础测试
└── examples/
    └── basic-usage.ts          # 使用示例
```
