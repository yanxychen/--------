import { CaseDetailEnricher } from '../src';

describe('CaseDetailEnricher', () => {
  let enricher: CaseDetailEnricher;

  beforeEach(() => {
    enricher = new CaseDetailEnricher({
      maxRetries: 0,
      concurrency: 2,
      delay: 0,
    });
  });

  describe('enrich', () => {
    it('should enrich cases with mock data', async () => {
      const cases = [
        {
          itemId: 'test1',
          platform: 'taobao' as const,
          title: '佛山市禅城区滨海御庭住宅拍卖',
          currentPrice: 1000000,
          location: '佛山市禅城区',
          detailUrl: 'https://sf.taobao.com/test1',
          searchKeyword: '滨海御庭',
        },
        {
          itemId: 'test2',
          platform: 'jd' as const,
          title: '佛山市南海区商铺拍卖',
          currentPrice: 500000,
          location: '佛山市南海区',
          detailUrl: 'https://auction.jd.com/test2',
          searchKeyword: '南海区',
        },
      ];

      const result = await enricher.enrich({ cases });

      expect(result.enrichCount).toBeGreaterThan(0);
      expect(result.enrichedCases.length).toBeGreaterThan(0);
      expect(result.enrichedCases[0].buildingArea).toBeGreaterThan(0);
      expect(result.enrichedCases[0].marketValue).toBeGreaterThan(0);
    });
  });
});
