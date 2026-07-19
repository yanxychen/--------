import { CaseScorer } from '../src';
import type { ScoringCase } from '../src';

function createCase(overrides: Partial<ScoringCase> = {}): ScoringCase {
  return {
    itemId: 'case-' + Math.random().toString(36).substr(2, 9),
    platform: 'taobao',
    title: '测试案例',
    fullAddress: '北京市朝阳区测试路1号',
    buildingArea: 100,
    marketValue: 5000000,
    auctionTime: new Date().toISOString(),
    auctionStatus: '已成交',
    auctionRound: '一拍',
    drivingDistance: 1000,
    sourceUrl: 'https://zc-item.taobao.com/auction/item_detail.htm?itemId=test',
    ...overrides,
  };
}

describe('CaseScorer', () => {
  describe('距离评分', () => {
    const scorer = new CaseScorer({ propertyType: 'residential', targetArea: 100 });

    it('500m以内得50分', () => {
      const result = scorer.scoreAndSort({
        cases: [createCase({ drivingDistance: 300 })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].distanceScore).toBe(50);
    });

    it('1km以内得45分', () => {
      const result = scorer.scoreAndSort({
        cases: [createCase({ drivingDistance: 800 })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].distanceScore).toBe(45);
    });

    it('2km以内得37.5分', () => {
      const result = scorer.scoreAndSort({
        cases: [createCase({ drivingDistance: 1500 })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].distanceScore).toBe(37.5);
    });

    it('5km以上得5分', () => {
      const result = scorer.scoreAndSort({
        cases: [createCase({ drivingDistance: 10000 })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].distanceScore).toBe(5);
    });
  });

  describe('面积评分', () => {
    const scorer = new CaseScorer({ propertyType: 'residential', targetArea: 100 });

    it('差异10%以内得30分', () => {
      const result = scorer.scoreAndSort({
        cases: [createCase({ buildingArea: 105 })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].areaScore).toBe(30);
    });

    it('差异20%以内得25分', () => {
      const result = scorer.scoreAndSort({
        cases: [createCase({ buildingArea: 115 })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].areaScore).toBe(25);
    });

    it('差异50%以上得5分', () => {
      const result = scorer.scoreAndSort({
        cases: [createCase({ buildingArea: 200 })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].areaScore).toBe(5);
    });
  });

  describe('时间评分', () => {
    const scorer = new CaseScorer({ propertyType: 'residential', targetArea: 100 });

    it('3个月内得20分', () => {
      const time = new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString();
      const result = scorer.scoreAndSort({
        cases: [createCase({ auctionTime: time })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].timeScore).toBe(20);
    });

    it('2年以上得1分', () => {
      const time = new Date(Date.now() - 800 * 24 * 60 * 60 * 1000).toISOString();
      const result = scorer.scoreAndSort({
        cases: [createCase({ auctionTime: time })],
        propertyType: 'residential',
        targetArea: 100,
      });
      expect(result.scoredCases[0].timeScore).toBe(1);
    });
  });

  describe('排序', () => {
    const scorer = new CaseScorer({ propertyType: 'residential', targetArea: 100 });

    it('按总分降序排序', () => {
      const case1 = createCase({ drivingDistance: 300, buildingArea: 100 });
      const case2 = createCase({ drivingDistance: 5000, buildingArea: 200 });

      const result = scorer.scoreAndSort({
        cases: [case2, case1],
        propertyType: 'residential',
        targetArea: 100,
      });

      expect(result.scoredCases[0].totalScore).toBeGreaterThan(result.scoredCases[1].totalScore);
    });
  });

  describe('自身拍卖', () => {
    const scorer = new CaseScorer({ propertyType: 'residential', targetArea: 100 });

    it('自身拍卖案例单独列出', () => {
      const selfCase = createCase({ itemId: 'self-1' });
      const normalCase = createCase({ itemId: 'normal-1' });

      const result = scorer.scoreAndSort({
        cases: [selfCase, normalCase],
        propertyType: 'residential',
        targetArea: 100,
        selfAuctionItemIds: ['self-1'],
      });

      expect(result.selfAuctionCases.length).toBe(1);
      expect(result.selfAuctionCases[0].itemId).toBe('self-1');
      expect(result.scoredCases.length).toBe(1);
      expect(result.scoredCases[0].itemId).toBe('normal-1');
    });
  });
});
