import { SelfAuctionDetector } from '../src';

describe('SelfAuctionDetector', () => {
  let detector: SelfAuctionDetector;

  beforeEach(() => {
    detector = new SelfAuctionDetector({
      addressSimilarityThreshold: 0.85,
      areaTolerance: 0.1,
    });
  });

  describe('detect', () => {
    it('should detect self auction with address and area match', () => {
      const cases = [
        {
          itemId: '1',
          platform: 'taobao' as const,
          title: '滨海御庭1座201室',
          fullAddress: '佛山市禅城区东平二路3号滨海御庭1座201室',
          buildingArea: 120,
          detailUrl: 'https://test.com/1',
        },
        {
          itemId: '2',
          platform: 'taobao' as const,
          title: '其他小区',
          fullAddress: '佛山市南海区其他小区',
          buildingArea: 200,
          detailUrl: 'https://test.com/2',
        },
      ];

      const result = detector.detect({
        cases,
        targetAddress: '佛山市禅城区东平二路3号滨海御庭1座201室',
        targetArea: 120,
      });

      expect(result.selfAuctionCases.length).toBe(1);
      expect(result.selfAuctionItemIds).toContain('1');
      expect(result.otherCases.length).toBe(1);
    });

    it('should detect self auction with address only match', () => {
      const cases = [
        {
          itemId: '1',
          platform: 'taobao' as const,
          title: '滨海御庭1座',
          fullAddress: '佛山市禅城区滨海御庭1座',
          buildingArea: 0,
          detailUrl: 'https://test.com/1',
        },
      ];

      const result = detector.detect({
        cases,
        targetAddress: '佛山市禅城区滨海御庭1座201室',
      });

      expect(result.selfAuctionCases.length).toBe(1);
      expect(result.matchDetails[0].matchType).toBe('address_only');
    });

    it('should not detect different addresses as self auction', () => {
      const cases = [
        {
          itemId: '1',
          platform: 'taobao' as const,
          title: '完全不同的地址',
          fullAddress: '广州市天河区珠江新城',
          buildingArea: 120,
          detailUrl: 'https://test.com/1',
        },
      ];

      const result = detector.detect({
        cases,
        targetAddress: '佛山市禅城区滨海御庭',
        targetArea: 120,
      });

      expect(result.selfAuctionCases.length).toBe(0);
      expect(result.otherCases.length).toBe(1);
    });
  });
});
