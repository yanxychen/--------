# 估值案例搜索总控 Skill

串联9个子Skill，完成从抵押物地址输入到标准8列V1格式表格输出的完整流程。

## 功能描述

作为总控调度器，按固定顺序调用以下9个子Skill：

1. **location-distance** - 定位抵押物，提取搜索关键词
2. **case-search-engine** - 多平台分层搜索案例
3. **asset-type-matcher** - 资产类型匹配
4. **case-detail-enricher** - 详情页数据补全
5. **self-auction-detector** - 识别抵押物自身拍卖
6. **case-merger** - 合并多次拍卖案例
7. **case-filter** - 多档位逐步放宽过滤
8. **case-scoring** - 案例评分排序
9. **v1-valuation-format** - 格式化输出8列表格

## 触发方式

### 自然语言触发
- "搜索这个地址的参考案例"
- "帮我找抵押物附近的拍卖案例"
- "输入地址，输出估值参考案例"

### 代码调用
```typescript
import { ValuationCaseSearch } from './valuation-case-search';

const search = new ValuationCaseSearch({
  amapApiKey: 'your-amap-key',
  taobaoCookies: 'cookie-string',
});

const result = await search.run({
  address: '北京市朝阳区XX小区1号楼',
  propertyType: '住宅',
  buildingArea: 100,
});

console.log(result.markdown);
```

## 输入输出

### 输入
- `address: string` - 抵押物完整地址
- `propertyType: string` - 资产类型（住宅/商业/工业/土地/特殊资产）
- `buildingArea?: number` - 建筑面积（平方米，选填）
- `options.output?: 'markdown' | 'json' | 'html'` - 输出格式（默认markdown）

### 输出
- `markdown: string` - V1标准8列表格
- `data: V1Case[]` - 结构化数据
- `meta: SearchMeta` - 搜索元信息（耗时、各步骤状态等）

## 流程编排

```
输入: 地址 + 类型 + 面积(选填)
  │
  ├─ Step 1: location-distance
  │   └─ 输出: 经纬度、搜索关键词、驾车距离矩阵
  │
  ├─ Step 2: case-search-engine
  │   └─ 输出: 原始案例列表（淘宝+京东并行）
  │
  ├─ Step 3: asset-type-matcher
  │   └─ 输出: 标注类型的案例列表
  │
  ├─ Step 4: case-detail-enricher
  │   └─ 输出: 补全详情的案例列表（建筑面积、市场价值、起拍价等）
  │
  ├─ Step 5: self-auction-detector
  │   └─ 输出: 自身拍卖ID列表
  │
  ├─ Step 6: case-merger
  │   └─ 输出: 合并后的案例列表（同一抵押物多次拍卖合并）
  │
  ├─ Step 7: case-filter
  │   └─ 输出: 过滤后的案例列表（多档位逐步放宽）
  │
  ├─ Step 8: case-scoring
  │   └─ 输出: 评分排序后的案例列表 + 自身拍卖案例
  │
  └─ Step 9: v1-valuation-format
      └─ 输出: V1标准8列表格
```

## 错误处理

- 任一步骤失败时记录错误日志，不中断后续步骤
- 搜索步骤失败时返回空列表，继续执行
- 详情页补全失败时保留已有数据，不丢弃案例
- 最终输出时保证8列格式完整，缺失数据用"-"填充

## 版本号

v1.0.0

## 目录结构

```
valuation-case-search/
├── SKILL.md              # Skill说明文档
├── src/
│   ├── types.ts          # 类型定义
│   ├── constants.ts      # 常量配置
│   ├── orchestrator.ts   # 流程编排器
│   └── index.ts          # 主入口
├── tests/
│   └── basic.test.ts     # 基础测试
└── examples/
    └── basic-usage.ts    # 使用示例
```
