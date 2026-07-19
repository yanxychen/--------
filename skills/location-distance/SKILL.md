# 地址定位与距离计算 Skill

通过高德地图API进行地址解析、经纬度定位、分层关键词提取，以及计算抵押物与案例之间的直线距离和驾车距离。

## 功能描述

- 地址转经纬度（高德地图API）
- 从地址中提取分层搜索关键词（小区名、商圈、行政区等）
- 直线距离计算（哈弗辛公式，快速粗筛）
- 驾车距离计算（高德API，精确计算）

## 触发方式

### 自然语言触发
- "定位一下这个地址"
- "计算两个地址的距离"
- "提取搜索关键词"
- "算一下驾车距离"
- "地址转经纬度"

### 代码调用
```typescript
import { LocationDistance } from './location-distance';

const locator = new LocationDistance({ amapKey: 'your-amap-key' });

// 定位地址
const location = await locator.geocode('佛山市禅城区滨海御庭');

// 计算直线距离
const straightDist = locator.haversineDistance(lng1, lat1, lng2, lat2);

// 计算驾车距离
const drivingDist = await locator.drivingDistance(originLng, originLat, destLng, destLat);

// 提取分层关键词
const keywords = locator.extractKeywords('佛山市禅城区季华路滨海御庭1座');
```

## 输入输出

### 地址定位输入
- `address: string` - 完整地址
- `city?: string` - 所在城市（辅助定位）

### 地址定位输出
- `longitude: number` - 经度
- `latitude: number` - 纬度
- `formattedAddress: string` - 格式化地址
- `province: string` - 省份
- `city: string` - 城市
- `district: string` - 区/县
- `township?: string` - 街道/乡镇
- `neighborhood?: string` - 社区/小区
- `building?: string` - 楼栋
- `keywords: string[]` - 分层搜索关键词（从细到粗）

### 距离计算输入
- `originLng: number` - 起点经度
- `originLat: number` - 起点纬度
- `destLng: number` - 终点经度
- `destLat: number` - 终点纬度

### 距离计算输出
- `straightDistance: number` - 直线距离（米）
- `drivingDistance?: number` - 驾车距离（米）
- `drivingDuration?: number` - 驾车时间（秒）

## 分层关键词提取规则

按优先级从高到低排列：
1. 完整小区名 + 楼栋（如"滨海御庭1座"）
2. 小区名/楼盘名（如"滨海御庭"）
3. 商圈/街道（如"季华路""祖庙街道"）
4. 行政区（如"禅城区"）
5. 城市名（如"佛山市"）

## 距离计算策略

### 两步过滤法
1. **直线距离粗筛**：用哈弗辛公式快速计算，阈值 = 最大距离 × 1.8
2. **驾车距离精算**：只对通过粗筛的案例调用高德API

### 直线距离公式
哈弗辛公式（Haversine），考虑地球曲率。

## 特殊情况处理

| 情况 | 处理方式 |
|------|---------|
| 地址解析失败 | 返回空坐标，后续用地址文本匹配 |
| 案例地址无法解析 | 跳过该案例的距离计算，评分时用基础分 |
| 高德API限流 | 降级为只算直线距离 |
| 无距离数据 | 评分时给基础分 |

## 版本号

v1.0.0

## 目录结构

```
location-distance/
├── SKILL.md              # Skill说明文档
├── src/
│   ├── types.ts          # 类型定义
│   ├── constants.ts      # 常量配置
│   ├── index.ts          # 主入口
│   ├── geocoder.ts       # 地址解析（高德API）
│   ├── distance.ts       # 距离计算
│   └── keywords.ts       # 关键词提取
├── tests/
│   └── basic.test.ts     # 基础测试
└── examples/
    └── basic-usage.ts    # 使用示例
```
