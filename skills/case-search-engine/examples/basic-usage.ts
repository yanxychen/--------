import { CaseSearchEngine } from '../src';

const engine = new CaseSearchEngine({
  maxPages: 3,
  pageSize: 20,
  taobaoEnabled: true,
  jdEnabled: true,
});

async function example() {
  const result = await engine.search({
    keywords: ['滨海御庭', '禅城区', '佛山市'],
    propertyType: 'residential',
    assetType: '住宅',
  });

  console.log('找到案例数:', result.totalCount);
  console.log('使用平台:', result.platforms);
  console.log('搜索日志条数:', result.searchLog.length);

  console.log('\n前3个案例:');
  result.cases.slice(0, 3).forEach((c, i) => {
    console.log(`${i + 1}. [${c.platform}] ${c.title}`);
    console.log(`   价格: ¥${c.currentPrice.toLocaleString()}`);
    console.log(`   地址: ${c.location}`);
    console.log(`   状态: ${c.auctionStatus}`);
    console.log();
  });
}

example().catch(console.error);
