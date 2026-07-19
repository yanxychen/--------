import { SelfAuctionDetector } from '../src';

const detector = new SelfAuctionDetector({
  addressSimilarityThreshold: 0.85,
  areaTolerance: 0.1,
});

function example() {
  const cases = [
    {
      itemId: 'case1',
      platform: 'taobao' as const,
      title: '佛山市禅城区滨海御庭1座201室住宅拍卖',
      fullAddress: '佛山市禅城区东平二路3号滨海御庭1座201室',
      buildingArea: 92.46,
      detailUrl: 'https://sf.taobao.com/case1',
    },
    {
      itemId: 'case2',
      platform: 'taobao' as const,
      title: '佛山市禅城区滨海御庭1座二拍',
      fullAddress: '佛山市禅城区东平二路3号滨海御庭1座201室',
      buildingArea: 92.5,
      detailUrl: 'https://sf.taobao.com/case2',
    },
    {
      itemId: 'case3',
      platform: 'jd' as const,
      title: '佛山市南海区桂城街道某住宅拍卖',
      fullAddress: '佛山市南海区桂城街道某小区',
      buildingArea: 120,
      detailUrl: 'https://auction.jd.com/case3',
    },
  ];

  console.log('=== 抵押物自身拍卖识别测试 ===\n');

  const result = detector.detect({
    cases,
    targetAddress: '佛山市禅城区东平二路3号滨海御庭1座201室',
    targetArea: 92.46,
  });

  console.log(`自身拍卖案例: ${result.selfAuctionCases.length} 个`);
  console.log(`其他案例: ${result.otherCases.length} 个`);
  console.log();

  console.log('--- 自身拍卖案例 ---');
  result.selfAuctionCases.forEach((c, i) => {
    const detail = result.matchDetails.find(d => d.itemId === c.itemId);
    console.log(`${i + 1}. ${c.title}`);
    console.log(`   匹配类型: ${detail?.matchType}`);
    console.log(`   置信度: ${detail?.confidence}%`);
    console.log(`   地址相似度: ${(detail?.addressSimilarity || 0).toFixed(2)}`);
    console.log(`   面积相似度: ${(detail?.areaSimilarity || 0).toFixed(2)}`);
    console.log();
  });

  console.log('--- 其他案例 ---');
  result.otherCases.forEach((c, i) => {
    const detail = result.matchDetails.find(d => d.itemId === c.itemId);
    console.log(`${i + 1}. ${c.title}`);
    console.log(`   置信度: ${detail?.confidence}%`);
    console.log();
  });
}

example();
