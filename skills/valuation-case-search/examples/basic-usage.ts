import { ValuationCaseSearch } from '../src';
import type { SubSkillHandlers } from '../src';

// 创建Mock handlers用于演示流程
const handlers: SubSkillHandlers = {
  async runLocationDistance(address: string) {
    console.log(`Step 1: 定位地址 "${address}"`);
    return {
      longitude: 116.4074,
      latitude: 39.9042,
      keywords: ['XX小区', '朝阳区', '北京'],
    };
  },

  async runCaseSearch(keywords: string[]) {
    console.log(`Step 2: 搜索关键词 ${keywords.join(', ')}`);
    return [
      {
        itemId: 'case-001',
        platform: 'taobao',
        title: 'XX小区3室2厅',
        fullAddress: '北京市朝阳区XX小区1号楼101室',
        buildingArea: 105,
        marketValue: 5000000,
        auctionTime: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
        auctionStatus: '已成交',
        auctionRound: '一拍',
        drivingDistance: 800,
        sourceUrl: 'https://zc-item.taobao.com/auction/item_detail.htm?itemId=case-001',
      },
    ];
  },

  async runAssetTypeMatch(cases) {
    console.log(`Step 3: 类型匹配 ${cases.length} 个案例`);
    return cases.map(c => ({ ...c, matchedType: 'residential' }));
  },

  async runDetailEnrich(cases) {
    console.log(`Step 4: 详情页补全 ${cases.length} 个案例`);
    return cases;
  },

  async runSelfAuctionDetect(cases, address) {
    console.log(`Step 5: 识别自身拍卖 (地址: ${address})`);
    return [];
  },

  async runCaseMerge(cases) {
    console.log(`Step 6: 合并多次拍卖 ${cases.length} 个案例`);
    return cases;
  },

  async runCaseFilter(cases, propertyType, selfAuctionIds, minCases) {
    console.log(`Step 7: 过滤 ${cases.length} 个案例 (最少${minCases}个)`);
    return cases;
  },

  async runCaseScoring(cases, propertyType, targetArea, selfAuctionIds) {
    console.log(`Step 8: 评分排序 ${cases.length} 个案例`);
    const scoredCases = cases.map(c => ({
      ...c,
      totalScore: 85,
      distanceScore: 45,
      areaScore: 25,
      timeScore: 15,
      scoreBreakdown: {
        itemId: c.itemId,
        distanceScore: 45,
        areaScore: 25,
        timeScore: 15,
        totalScore: 85,
        distance: c.drivingDistance || 0,
        areaDiffRatio: 0.05,
        daysAgo: 60,
      },
    }));
    return { scoredCases, selfAuctionCases: [] };
  },

  async runV1Format(scoredCases, selfAuctionCases, output) {
    console.log(`Step 9: 格式化输出 ${scoredCases.length} 个案例 (${output})`);
    const data = scoredCases.map(c => ({
      referenceLocation: c.fullAddress,
      landArea: '不适用',
      buildingArea: c.buildingArea,
      marketValue: c.marketValue / 10000,
      unitPrice: (c.marketValue / 10000 * 10000) / c.buildingArea,
      source: c.sourceUrl,
      remark: `${c.auctionRound}：2026年01月15日，起拍价：4,500,000元，状态：${c.auctionStatus}\n距离抵押物约0.8公里`,
      priceType: '普通司法拍卖',
    }));
    return {
      markdown: `| 参照物位置 | 土地面积 (㎡) | 建筑面积 (㎡) | 市场价值(万元) | 建筑单价(元/㎡) | 数据来源 | 备注 | 价格类型 |
|---|---|---|---|---|---|---|---|
| ${data[0]?.referenceLocation || ''} | ${data[0]?.landArea || ''} | ${data[0]?.buildingArea || ''} | ${data[0]?.marketValue || ''} | ${data[0]?.unitPrice || ''} | ${data[0]?.source || ''} | ${data[0]?.remark || ''} | ${data[0]?.priceType || ''} |`,
      data,
    };
  },
};

const search = new ValuationCaseSearch(handlers);

const result = await search.run({
  address: '北京市朝阳区XX小区1号楼',
  propertyType: '住宅',
  buildingArea: 100,
  options: {
    output: 'markdown',
    minCases: 3,
  },
});

console.log('\n=== 搜索结果 ===');
console.log(result.markdown);
console.log('\n=== 元信息 ===');
console.log(`总耗时: ${result.meta.totalDurationMs}ms`);
console.log(`评分案例: ${result.meta.scoredCases}个`);
console.log(`自身拍卖: ${result.meta.selfAuctionCases}个`);
result.meta.steps.forEach(s => {
  console.log(`  Step ${s.index + 1} ${s.name}: ${s.status} (${s.durationMs || 0}ms)`);
});
