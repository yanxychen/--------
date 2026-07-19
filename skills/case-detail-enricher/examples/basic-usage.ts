import { CaseDetailEnricher } from '../src';

const enricher = new CaseDetailEnricher({
  maxRetries: 2,
  concurrency: 3,
  delay: 1000,
});

async function example() {
  const cases = [
    {
      itemId: 'tb_001',
      platform: 'taobao' as const,
      title: '佛山市禅城区滨海御庭1座住宅拍卖',
      currentPrice: 1250000,
      location: '佛山市禅城区东平二路3号',
      detailUrl: 'https://sf.taobao.com/item.htm?id=tb_001',
      searchKeyword: '滨海御庭',
    },
    {
      itemId: 'jd_001',
      platform: 'jd' as const,
      title: '佛山市南海区桂城街道商铺拍卖',
      currentPrice: 800000,
      location: '佛山市南海区桂城街道',
      detailUrl: 'https://auction.jd.com/jd_001.html',
      searchKeyword: '桂城街道',
    },
  ];

  console.log('开始补全详情...\n');

  const result = await enricher.enrich({ cases });

  console.log(`成功补全: ${result.enrichCount}`);
  console.log(`失败: ${result.failCount}`);
  console.log();

  result.enrichedCases.forEach((c, i) => {
    console.log(`【案例 ${i + 1}】${c.title}`);
    console.log(`  平台: ${c.platform}`);
    console.log(`  完整地址: ${c.fullAddress}`);
    console.log(`  建筑面积: ${c.buildingArea}㎡`);
    console.log(`  市场价值: ${c.marketValue.toFixed(2)}万元`);
    console.log(`  建筑单价: ${c.unitPrice.toFixed(2)}元/㎡`);
    console.log(`  起拍时间: ${c.auctionTime}`);
    console.log(`  拍卖状态: ${c.auctionStatus}`);
    console.log(`  拍卖轮次: ${c.auctionRound}`);
    console.log(`  价格类型: ${c.priceType}`);
    console.log();
  });

  if (result.failCount > 0) {
    console.log('失败案例:');
    result.failLog.forEach(f => {
      console.log(`  - ${f.title}: ${f.error}`);
    });
  }
}

example().catch(console.error);
