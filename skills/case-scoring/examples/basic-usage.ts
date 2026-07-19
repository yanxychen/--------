import { CaseScorer } from '../src';

const cases = [
  {
    itemId: 'case1',
    platform: 'taobao' as const,
    title: 'XX小区3室2厅',
    fullAddress: '北京市朝阳区XX小区1号楼101室',
    buildingArea: 105,
    marketValue: 5000000,
    auctionTime: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
    auctionStatus: '已成交',
    auctionRound: '一拍',
    drivingDistance: 800,
    sourceUrl: 'https://zc-item.taobao.com/auction/item_detail.htm?itemId=case1',
  },
  {
    itemId: 'case2',
    platform: 'jd' as const,
    title: 'YY花园2室1厅',
    fullAddress: '北京市朝阳区YY花园2号楼202室',
    buildingArea: 85,
    marketValue: 4200000,
    auctionTime: new Date(Date.now() - 200 * 24 * 60 * 60 * 1000).toISOString(),
    auctionStatus: '已成交',
    auctionRound: '二拍',
    drivingDistance: 2500,
    sourceUrl: 'https://paimai.jd.com/case2',
  },
  {
    itemId: 'case3',
    platform: 'taobao' as const,
    title: 'ZZ家园4室2厅',
    fullAddress: '北京市朝阳区ZZ家园3号楼303室',
    buildingArea: 140,
    marketValue: 6800000,
    auctionTime: new Date(Date.now() - 400 * 24 * 60 * 60 * 1000).toISOString(),
    auctionStatus: '已成交',
    auctionRound: '一拍',
    drivingDistance: 4000,
    sourceUrl: 'https://zc-item.taobao.com/auction/item_detail.htm?itemId=case3',
  },
];

const scorer = new CaseScorer({
  propertyType: 'residential',
  targetArea: 100,
});

const result = scorer.scoreAndSort({
  cases,
  propertyType: 'residential',
  targetArea: 100,
  selfAuctionItemIds: [],
});

console.log('=== 评分排序结果 ===');
result.scoredCases.forEach((c, index) => {
  console.log(`\n第${index + 1}名: ${c.title}`);
  console.log(`  总分: ${c.totalScore.toFixed(1)}分`);
  console.log(`  距离分: ${c.distanceScore.toFixed(1)}分 (${(c.scoreBreakdown.distance / 1000).toFixed(1)}km)`);
  console.log(`  面积分: ${c.areaScore.toFixed(1)}分 (差异${(c.scoreBreakdown.areaDiffRatio * 100).toFixed(0)}%)`);
  console.log(`  时间分: ${c.timeScore.toFixed(1)}分 (${c.scoreBreakdown.daysAgo}天前)`);
});

console.log(`\n自身拍卖案例: ${result.selfAuctionCases.length}个`);
