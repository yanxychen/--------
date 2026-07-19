export class AreaMatcher {
  private tolerance: number;

  constructor(tolerance: number = 0.1) {
    this.tolerance = tolerance;
  }

  isMatch(targetArea: number, caseArea: number): boolean {
    if (!targetArea || targetArea <= 0 || !caseArea || caseArea <= 0) {
      return false;
    }

    const diff = Math.abs(caseArea - targetArea);
    const ratio = diff / targetArea;

    return ratio <= this.tolerance;
  }

  calculateSimilarity(targetArea: number, caseArea: number): number {
    if (!targetArea || targetArea <= 0 || !caseArea || caseArea <= 0) {
      return 0;
    }

    const diff = Math.abs(caseArea - targetArea);
    const ratio = diff / targetArea;

    if (ratio <= this.tolerance) {
      return 1 - ratio;
    }

    return Math.max(0, 1 - ratio * 2);
  }

  getMatchLevel(targetArea: number, caseArea: number): 'exact' | 'close' | 'different' | 'unknown' {
    if (!targetArea || !caseArea) return 'unknown';

    const ratio = Math.abs(caseArea - targetArea) / targetArea;

    if (ratio <= 0.05) return 'exact';
    if (ratio <= this.tolerance) return 'close';
    return 'different';
  }
}
