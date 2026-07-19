import { AssetTypeMatcher } from '../src';

describe('AssetTypeMatcher', () => {
  let matcher: AssetTypeMatcher;

  beforeEach(() => {
    matcher = new AssetTypeMatcher();
  });

  describe('match', () => {
    it('should match residential property', () => {
      const result = matcher.match({
        title: '佛山市禅城区滨海御庭住宅拍卖',
        targetType: '住宅',
      });

      expect(result.isMatch).toBe(true);
      expect(result.matchedType).toBe('住宅');
      expect(result.confidence).toBeGreaterThan(0);
    });

    it('should match commercial property', () => {
      const result = matcher.match({
        title: '佛山市禅城区祖庙路商铺拍卖',
        targetType: '商业',
      });

      expect(result.isMatch).toBe(true);
      expect(result.matchedType).toBe('商业');
    });

    it('should match industrial property', () => {
      const result = matcher.match({
        title: '佛山市南海区工业园厂房拍卖',
        targetType: '工业',
      });

      expect(result.isMatch).toBe(true);
      expect(result.matchedType).toBe('工业');
    });

    it('should detect residential from indicators and area', () => {
      const result = matcher.match({
        title: '滨海御庭3栋201室',
        buildingArea: 120,
        targetType: '住宅',
      });

      expect(result.isMatch).toBe(true);
      expect(result.matchedType).toBe('住宅');
    });

    it('should return false for type mismatch', () => {
      const result = matcher.match({
        title: '佛山市禅城区商铺拍卖',
        targetType: '住宅',
      });

      expect(result.isMatch).toBe(false);
    });
  });

  describe('detectType', () => {
    it('should detect property type', () => {
      const result = matcher.detectType('佛山市禅城区滨海御庭住宅拍卖');
      expect(result.type).toBe('住宅');
    });
  });
});
