import { ValuationCaseSearch } from '../src';
import type { SubSkillHandlers, SearchResultCase } from '../src';

function createMockCase(overrides: Partial<SearchResultCase> = {}): SearchResultCase {
  return {
    itemId: 'case-001',
    platform: 'taobao',
    title: '测试案例',
    fullAddress: '北京市朝阳区测试路1号',
    buildingArea: 100,
    marketValue: 5000000,
    auctionTime: new Date().toISOString(),
    auctionStatus: '已成交',
    auctionRound: '一拍',
    drivingDistance: 800,
    sourceUrl: 'https://zc-item.taobao.com/test',
    ...overrides,
  };
}

function createMockHandlers(cases: SearchResultCase[] = [createMockCase()]): SubSkillHandlers {
  return {
    async runLocationDistance(address) {
      return { longitude: 116.4074, latitude: 39.9042, keywords: ['测试小区'] };
    },
    async runCaseSearch() {
      return cases;
    },
    async runAssetTypeMatch(c) {
      return c;
    },
    async runDetailEnrich(c) {
      return c;
    },
    async runSelfAuctionDetect() {
      return [];
    },
    async runCaseMerge(c) {
      return c;
    },
    async runCaseFilter(c) {
      return c;
    },
    async runCaseScoring(c) {
      const scored = c.map(item => ({
        ...item,
        totalScore: 85,
        distanceScore: 45,
        areaScore: 25,
        timeScore: 15,
        scoreBreakdown: {
          itemId: item.itemId,
          distanceScore: 45,
          areaScore: 25,
          timeScore: 15,
          totalScore: 85,
          distance: 800,
          areaDiffRatio: 0.05,
          daysAgo: 60,
        },
      }));
      return { scoredCases: scored, selfAuctionCases: [] };
    },
    async runV1Format(scoredCases) {
      return {
        markdown: `| 参照物位置 | 土地面积 (㎡) | 建筑面积 (㎡) | 市场价值(万元) | 建筑单价(元/㎡) | 数据来源 | 备注 | 价格类型 |
|---|---|---|---|---|---|---|---|
| ${scoredCases[0]?.fullAddress || ''} | 不适用 | 100 | 500.00 | 50000.00 | ${scoredCases[0]?.sourceUrl || ''} | 一拍 | 普通司法拍卖 |`,
        data: [],
      };
    },
  };
}

describe('ValuationCaseSearch', () => {
  it('完整流程执行成功', async () => {
    const handlers = createMockHandlers();
    const search = new ValuationCaseSearch(handlers);

    const result = await search.run({
      address: '北京市朝阳区测试路1号',
      propertyType: '住宅',
      buildingArea: 100,
    });

    expect(result.meta.steps).toHaveLength(9);
    expect(result.meta.steps.every(s => s.status === 'done')).toBe(true);
    expect(result.markdown).toContain('参照物位置');
  });

  it('某步骤失败时不中断后续步骤', async () => {
    const handlers = createMockHandlers();
    handlers.runCaseSearch = async () => {
      throw new Error('搜索失败');
    };

    const search = new ValuationCaseSearch(handlers);
    const result = await search.run({
      address: '北京市朝阳区测试路1号',
      propertyType: '住宅',
    });

    expect(result.meta.steps[1].status).toBe('error');
    expect(result.meta.steps[2].status).toBe('done');
  });

  it('空案例列表也能正常输出', async () => {
    const handlers = createMockHandlers([]);
    const search = new ValuationCaseSearch(handlers);

    const result = await search.run({
      address: '北京市朝阳区测试路1号',
      propertyType: '住宅',
    });

    expect(result.meta.steps.every(s => s.status === 'done')).toBe(true);
  });
});
