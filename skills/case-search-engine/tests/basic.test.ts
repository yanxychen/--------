import { CaseSearchEngine } from '../src';

describe('CaseSearchEngine', () => {
  let engine: CaseSearchEngine;

  beforeEach(() => {
    engine = new CaseSearchEngine({
      maxPages: 1,
      pageSize: 10,
      taobaoEnabled: true,
      jdEnabled: true,
    });
  });

  describe('search', () => {
    it('should search with keywords and return cases', async () => {
      const result = await engine.search({
        keywords: ['滨海御庭', '禅城区'],
        propertyType: 'residential',
        assetType: '住宅',
      });

      expect(result.cases.length).toBeGreaterThan(0);
      expect(result.totalCount).toBeGreaterThan(0);
      expect(result.platforms.length).toBeGreaterThan(0);
    });

    it('should record search log', async () => {
      const result = await engine.search({
        keywords: ['测试小区'],
        propertyType: 'residential',
        assetType: '住宅',
      });

      expect(result.searchLog.length).toBeGreaterThan(0);
      expect(result.searchLog[0].keyword).toBe('测试小区');
    });
  });
});
