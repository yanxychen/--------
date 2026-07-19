import { CaseMerger } from '../src';

describe('CaseMerger', () => {
  let merger: CaseMerger;

  beforeEach(() => {
    merger = new CaseMerger({
      addressSimilarityThreshold: 0.8,
      areaTolerance: 0.1,
    });
  });

  describe('merge', () => {
    it('should merge multiple auctions of same property', () => {
      const cases = [
        {
          itemId: '1',
          platform: 'taobao' as const,
          title: '滨海御庭1座一拍',
          fullAddress: '佛山市禅城区滨海御庭1座201室',
          buildingArea: 92.46,
          marketValue: 125,
          unitPrice: 13500,
          startPrice: 1250000,
          auctionTime: '2024年10月15日',
          auctionStatus: '流拍',
          auctionRound: '一拍',
          priceType: '普通司法拍卖',
          detailUrl: 'https://test.com/1',
        },
        {
          itemId: '2',
          platform: 'taobao' as const,
          title: '滨海御庭1座二拍',
          fullAddress: '佛山市禅城区滨海御庭1座201室',
          buildingArea: 92.5,
          marketValue: 100,
          unitPrice: 10800,
          startPrice: 1000000,
          auctionTime: '2024年12月15日',
          auctionStatus: '已成交',
          auctionRound: '二拍',
          priceType: '普通司法拍卖',
          detailUrl: 'https://test.com/2',
        },
      ];

      const result = merger.merge({ cases });

      expect(result.mergedCases.length).toBe(1);
      expect(result.mergeCount).toBe(1);
      expect(result.mergedCases[0].auctionHistory.length).toBe(2);
      expect(result.mergedCases[0].auctionRound).toBe('二拍');
    });

    it('should not merge different properties', () => {
      const cases = [
        {
          itemId: '1',
          platform: 'taobao' as const,
          title: '小区A住宅拍卖',
          fullAddress: '佛山市禅城区小区A',
          buildingArea: 100,
          marketValue: 100,
          unitPrice: 10000,
          startPrice: 1000000,
          auctionTime: '2024年10月15日',
          auctionStatus: '即将开始',
          auctionRound: '一拍',
          priceType: '普通司法拍卖',
          detailUrl: 'https://test.com/1',
        },
        {
          itemId: '2',
          platform: 'taobao' as const,
          title: '小区B住宅拍卖',
          fullAddress: '佛山市南海区小区B',
          buildingArea: 120,
          marketValue: 150,
          unitPrice: 12500,
          startPrice: 1500000,
          auctionTime: '2024年10月20日',
          auctionStatus: '即将开始',
          auctionRound: '一拍',
          priceType: '普通司法拍卖',
          detailUrl: 'https://test.com/2',
        },
      ];

      const result = merger.merge({ cases });

      expect(result.mergedCases.length).toBe(2);
      expect(result.mergeCount).toBe(0);
    });

    it('should handle single case', () => {
      const cases = [
        {
          itemId: '1',
          platform: 'taobao' as const,
          title: '测试案例',
          fullAddress: '测试地址',
          buildingArea: 100,
          marketValue: 100,
          unitPrice: 10000,
          startPrice: 1000000,
          auctionTime: '2024年10月15日',
          auctionStatus: '即将开始',
          auctionRound: '一拍',
          priceType: '普通司法拍卖',
          detailUrl: 'https://test.com/1',
        },
      ];

      const result = merger.merge({ cases });

      expect(result.mergedCases.length).toBe(1);
      expect(result.mergeCount).toBe(0);
      expect(result.mergedCases[0].auctionHistory.length).toBe(1);
    });
  });
});
