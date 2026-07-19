import { LocationDistance } from '../src';

describe('LocationDistance', () => {
  let locator: LocationDistance;

  beforeEach(() => {
    locator = new LocationDistance({ amapKey: 'test-key' });
  });

  describe('haversineDistance', () => {
    it('should calculate correct straight-line distance', () => {
      const beijing = { lng: 116.4074, lat: 39.9042 };
      const shanghai = { lng: 121.4737, lat: 31.2304 };

      const distance = locator.haversineDistance(beijing, shanghai);

      expect(distance).toBeGreaterThan(1000000);
      expect(distance).toBeLessThan(1200000);
    });

    it('should return 0 for same point', () => {
      const point = { lng: 116.4074, lat: 39.9042 };
      const distance = locator.haversineDistance(point, point);
      expect(distance).toBeCloseTo(0, 5);
    });
  });

  describe('extractKeywords', () => {
    it('should extract keywords from residential address', () => {
      const result = locator.extractKeywords('佛山市禅城区季华路滨海御庭1座');

      expect(result.keywords.length).toBeGreaterThan(0);
      expect(result.levels.city).toContain('佛山市');
      expect(result.levels.district).toContain('禅城区');
    });

    it('should return empty for empty address', () => {
      const result = locator.extractKeywords('');
      expect(result.keywords.length).toBe(0);
    });
  });
});
