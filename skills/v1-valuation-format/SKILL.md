# V1估值格式输出 Skill

不良资产估值参考案例的标准输出格式Skill，输出严格的8列V1标准格式，永不修改。

## 功能描述

将评分排序后的拍卖案例数据，转换为固定的V1格式（8列标准表格）输出。支持多种输出格式：Markdown表格、JSON、Excel、HTML表格。

**格式一旦锁定，永不修改。** 如需变更格式，请发布v2版本。

## 在流程中的位置

这是案例搜索流程的**第9步（格式化输出）**，位于案例评分排序之后，是最终输出环节：
1. 接收评分排序后的案例数据（来自 case-scoring Skill）
2. 接收自身拍卖案例数据（来自 self-auction-detector Skill）
3. 转换为标准8列V1格式输出

## 触发方式

### 自然语言触发
- "用V1格式输出这些案例"
- "生成8列标准表格"
- "导出V1格式Excel"
- "按照锁定格式输出"
- "估值报告格式"

### 代码调用
```typescript
import { v1Format } from './v1-valuation-format';

const result = v1Format.format(rawCases, {
  output: 'markdown', // 'markdown' | 'json' | 'excel' | 'html'
  fieldMapping: { ... } // 可选：自定义字段映射
});
```

## 输入输出

### 输入
- `scoredCases: ScoredCase[]` - 评分排序后的案例列表（来自 case-scoring Skill）
- `selfAuctionCases: ScoringCase[]` - 自身拍卖案例列表（可选，单独展示）
- `options.fieldMapping?: FieldMapping` - 字段映射配置（可选，有默认映射）
- `options.output?: 'markdown' | 'json' | 'excel' | 'html'` - 输出格式
- `options.includeHeader?: boolean` - 是否包含表头（默认true）
- `options.numberPrecision?: number` - 数字保留小数位（默认2）
- `options.selfAuctionFirst?: boolean` - 自身拍卖是否排在前面（默认true）
- `options.showScore?: boolean` - 是否在备注中显示评分（默认false）

### 输出
严格的8列V1格式数据：
1. 参照物位置
2. 土地面积 (㎡)
3. 建筑面积 (㎡)
4. 市场价值(万元)
5. 建筑单价(元/㎡)
6. 数据来源
7. 备注
8. 价格类型

## 格式规则

### 数据规则
- 建筑面积：保留2位小数，单位㎡
- 市场价值：保留2位小数，单位万元，取最新拍卖价
- 建筑单价：保留2位小数，= 市场价值(万元) × 10000 ÷ 建筑面积(㎡)
- 土地面积：无则填"不适用"
- 数据来源：完整URL，可点击跳转

### 备注格式
```
一拍：YYYY年MM月DD日，起拍价：X,XXX,XXX元，状态：XXX
二拍：YYYY年MM月DD日，起拍价：X,XXX,XXX元，状态：XXX
变卖：YYYY年MM月DD日，起拍价：X,XXX,XXX元，状态：XXX
距离抵押物约X.X公里
```

### 特殊标记

- **距离显示**：统一使用驾车距离，格式为"距离抵押物约X.X公里"（精确到1位小数）
- **起拍时间**：必须显示具体拍卖日期，格式为"YYYY年MM月DD日"
- **无数据处理**：建筑面积、市场价值等必填项缺失时显示"-"，土地面积无则显示"不适用"

## 版本号

v1.0.0 - 锁定版本，永不修改

## 目录结构

```
v1-valuation-format/
├── SKILL.md              # Skill说明文档
├── src/
│   ├── types.ts          # 类型定义
│   ├── constants.ts      # 常量配置（列名、默认值）
│   ├── converter.ts      # 格式转换引擎
│   ├── validator.ts      # Schema校验器
│   └── formatters/       # 多格式输出器
│       ├── markdown.ts
│       ├── json.ts
│       ├── excel.ts
│       └── html.ts
├── tests/
│   ├── format.test.ts    # 格式快照测试
│   └── validator.test.ts # 校验测试
└── examples/
    └── basic-usage.ts    # 使用示例
```