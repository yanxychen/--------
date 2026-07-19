import type { MatchRequest, MatchResult, AssetType } from './types';
import { Matcher } from './matcher';

export class AssetTypeMatcher {
  private matcher: Matcher;

  constructor() {
    this.matcher = new Matcher();
  }

  match(request: MatchRequest): MatchResult {
    return this.matcher.match(request);
  }

  batchMatch(
    cases: Array<{ title: string; description?: string; buildingArea?: number }>,
    targetType: string
  ): MatchResult[] {
    return this.matcher.batchMatch(cases, targetType);
  }

  isResidential(title: string, buildingArea?: number): boolean {
    return this.match({ title, buildingArea, targetType: '住宅' }).isMatch;
  }

  isCommercial(title: string, buildingArea?: number): boolean {
    return this.match({ title, buildingArea, targetType: '商业' }).isMatch;
  }

  isIndustrial(title: string, buildingArea?: number): boolean {
    return this.match({ title, buildingArea, targetType: '工业' }).isMatch;
  }

  isLand(title: string, buildingArea?: number): boolean {
    return this.match({ title, buildingArea, targetType: '土地' }).isMatch;
  }

  detectType(title: string, buildingArea?: number): { type: string; subType?: string; confidence: number } {
    const result = this.match({ title, buildingArea, targetType: '住宅' });
    return {
      type: result.matchedType,
      subType: result.matchedSubType,
      confidence: result.confidence,
    };
  }
}

export {
  type MatchRequest,
  type MatchResult,
  type AssetType,
};
