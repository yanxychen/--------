import { CaseFilter } from '../src';

describe('CaseFilter', () => {
  let filter: CaseFilter;

  beforeEach(() => {
    filter = new CaseFilter();
  });

  describe('filter', () => {
    const createCase = (overrides = {}) => ({
      itemId: 'test',
      platform: 'taobao' as const,
      title: '测试住宅',
      fullAddress: '佛山市禅城区',
      buildingArea: 100,
      marketValue: 100,
      auctionTime: '2024年10月15日',
      auctionStatus: '即将开始',
      auctionRound: '一拍',
      drivingDistance: 2000,
      straightDistance: 1500,
      matchedType: '住宅',
      ...overrides,
    });

    it('should filter by type first', () => {
      const cases = [
        createCase({ itemId: '1', title: '住宅拍卖', matchedType: '住宅' }),
        createCase({ itemId: '2', title: '商铺拍卖', matchedType: '商业' }),
      ];

      const result = filter.filter({
        cases,
        propertyType: 'residential',
        assetType: '住宅',
        minCases: 1,
      });

      expect(result.filteredCases.length).toBe(1);
      expect(result.filteredCases[0].itemId).toBe('1');
    });

    it('should relax distance when not enough cases', () => {
      const cases = [
        createCase({ itemId: '1', drivingDistance: 4000, straightDistance: 3500 }),
        createCase({ itemId: '2', drivingDistance: 2000, straightDistance: 1800 }),
        createCase({ itemId: '3', drivingDistance: 6000, straightDistance: 5500 }),
      ];

      const result = filter.filter({
        cases,
        propertyType: 'residential',
        assetType: '住宅',
        minCases: 3,
      });

      expect(result.distanceLevel).toBeGreaterThan(0);
    });

    it('should include self auction cases regardless of time', () => {
      const cases = [
        createCase({ itemId: 'self', auctionTime: '2020年1月1日' }),
        createCase({ itemId: 'other', auctionTime: '2024年10月15日' }),
      ];

      const result = filter.filter({
        cases,
        propertyType: 'residential',
        assetType: '住宅',
        selfAuctionItemIds: ['self'],
        minCases: 2,
      });

      const selfCase = result.filteredCases.find(c => c.itemId === 'self');
      expect(selfCase).toBeDefined();
    });

    it('should handle rough mode with straight distance', () => {
      const cases = [
        createCase({ itemId: '1', straightDistance: 1000 }),
      ];

      const result = filter.roughFilter({
        cases,
        propertyType: 'residential',
        assetType: '住宅',
        minCases: 1,
      });

      expect(result.filteredCases.length).toBe(1);
    });
  });
});
