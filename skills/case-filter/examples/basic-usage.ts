import { CaseFilter } from '../src';

const filter = new CaseFilter();

function example() {
  const cases = [
    {
      itemId: 'case1',
      platform: 'taobao' as const,
      title: '佛山市禅城区滨海御庭住宅拍卖',
      fullAddress: '佛山市禅城区东平二路3号',
      buildingArea: 92.46,
      marketValue: 124.91,
      auctionTime: '2024年10月15日',
      auctionStatus: '流拍',
      auctionRound: '一拍',
      drivingDistance: 100,
      straightDistance: 80,
      matchedType: '住宅',
    },
    {
      itemId: 'case2',
      platform: 'taobao' as const,
      title: '佛山市禅城区魁奇二路某住宅',
      fullAddress: '佛山市禅城区魁奇二路',
      buildingArea: 120,
      marketValue: 150,
      auctionTime: '2024年6月15日',
      auctionStatus: '已成交',
      auctionRound: '一拍',
      drivingDistance: 3500,
      straightDistance: 2800,
      matchedType: '住宅',
    },
    {
      itemId: 'case3',
      platform: 'jd' as const,
      title: '佛山市南海区某商铺拍卖',
      fullAddress: '佛山市南海区',
      buildingArea: 80,
      marketValue: 200,
      auctionTime: '2024年11月20日',
      auctionStatus: '即将开始',
      auctionRound: '一拍',
      drivingDistance: 8000,
      straightDistance: 6500,
      matchedType: '商业',
    },
    {
      itemId: 'self',
      platform: 'taobao' as const,
      title: '佛山市禅城区滨海御庭1座201室（自身拍卖）',
      fullAddress: '佛山市禅城区东平二路3号',
      buildingArea: 92.46,
      marketValue: 125,
      auctionTime: '2022年1月1日',
      auctionStatus: '已成交',
      auctionRound: '二拍',
      drivingDistance: 0,
      straightDistance: 0,
      matchedType: '住宅',
    },
  ];

  console.log('=== 案例过滤测试 ===\n');

  console.log('原始案例数:', cases.length);
  console.log();

  const result = filter.filter({
    cases,
    propertyType: 'residential',
    assetType: '住宅',
    selfAuctionItemIds: ['self'],
    minCases: 3,
    mode: 'fine',
  });

  console.log('=== 精筛模式 ===');
  console.log(`过滤后案例数: ${result.filteredCases.length}`);
  console.log(`距离档位: ${result.distanceLevel + 1} (${result.usedDistanceThreshold}米)`);
  console.log(`时间档位: ${result.timeLevel + 1} (${result.usedTimeThreshold}天)`);
  console.log();

  console.log('符合条件的案例:');
  result.filteredCases.forEach((c, i) => {
    console.log(`${i + 1}. ${c.title}`);
    console.log(`   距离: ${c.drivingDistance}米`);
    console.log(`   拍卖时间: ${c.auctionTime}`);
    console.log(`   类型: ${c.matchedType}`);
    console.log();
  });

  console.log('过滤日志:');
  result.filterLog.forEach(log => {
    console.log(`  ${log.step}: ${log.beforeCount} → ${log.afterCount} (过滤掉${log.filteredCount}个)`);
  });
}

example();
