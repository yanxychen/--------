import { CaseMerger } from '../src';

const merger = new CaseMerger({
  addressSimilarityThreshold: 0.8,
  areaTolerance: 0.1,
});

function example() {
  const cases = [
    {
      itemId: 'case1',
      platform: 'taobao' as const,
      title: '佛山市禅城区滨海御庭1座201室（一拍）',
      fullAddress: '佛山市禅城区东平二路3号滨海御庭1座201室',
      buildingArea: 92.46,
      marketValue: 124.91,
      unitPrice: 13500,
      startPrice: 1249100,
      auctionTime: '2024年10月15日',
      auctionStatus: '流拍',
      auctionRound: '一拍',
      priceType: '普通司法拍卖',
      detailUrl: 'https://sf.taobao.com/case1',
    },
    {
      itemId: 'case2',
      platform: 'taobao' as const,
      title: '佛山市禅城区滨海御庭1座201室（二拍）',
      fullAddress: '佛山市禅城区东平二路3号滨海御庭1座201室',
      buildingArea: 92.5,
      marketValue: 99.93,
      unitPrice: 10800,
      startPrice: 999300,
      auctionTime: '2024年12月15日',
      auctionStatus: '已成交',
      auctionRound: '二拍',
      priceType: '普通司法拍卖',
      detailUrl: 'https://sf.taobao.com/case2',
    },
    {
      itemId: 'case3',
      platform: 'jd' as const,
      title: '佛山市南海区桂城街道某住宅拍卖',
      fullAddress: '佛山市南海区桂城街道某小区',
      buildingArea: 120,
      marketValue: 150,
      unitPrice: 12500,
      startPrice: 1500000,
      auctionTime: '2024年11月20日',
      auctionStatus: '即将开始',
      auctionRound: '一拍',
      priceType: '普通司法拍卖',
      detailUrl: 'https://auction.jd.com/case3',
    },
  ];

  console.log('=== 多次拍卖合并测试 ===\n');

  const result = merger.merge({ cases });

  console.log(`原始案例数: ${cases.length}`);
  console.log(`合并后案例数: ${result.mergedCases.length}`);
  console.log(`合并组数: ${result.mergeCount}`);
  console.log();

  result.mergedCases.forEach((c, i) => {
    console.log(`【案例 ${i + 1}】${c.title}`);
    console.log(`  地址: ${c.fullAddress}`);
    console.log(`  建筑面积: ${c.buildingArea}㎡`);
    console.log(`  当前轮次: ${c.auctionRound}`);
    console.log(`  当前状态: ${c.auctionStatus}`);
    console.log(`  历史拍卖 (${c.auctionHistory.length}次):`);
    c.auctionHistory.forEach((h, j) => {
      console.log(`    ${j + 1}. [${h.round}] ${h.time} - ¥${h.price.toLocaleString()} - ${h.status}`);
    });
    console.log();
  });

  if (result.mergeCount > 0) {
    console.log('合并日志:');
    result.mergeLog.forEach(log => {
      console.log(`  - ${log.groupId}: ${log.caseCount}个案例, 轮次: ${log.rounds.join(', ')}`);
    });
  }
}

example();
