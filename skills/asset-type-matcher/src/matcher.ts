import type { MatchRequest, MatchResult, AssetType } from './types';
import { TYPE_KEYWORDS, SUB_TYPE_KEYWORDS, RESIDENTIAL_INDICATORS, CONFIDENCE_SCORES } from './constants';

export class Matcher {
  match(request: MatchRequest): MatchResult {
    const { title, description, buildingArea, targetType, targetSubType } = request;
    const text = this.normalizeText(title + ' ' + (description || ''));

    if (!text.trim()) {
      return {
        isMatch: true,
        matchedType: targetType,
        matchReason: '标题为空，默认匹配',
        confidence: CONFIDENCE_SCORES.DEFAULT,
      };
    }

    const typeScores = this.calculateTypeScores(text, buildingArea);
    const bestType = this.getBestType(typeScores);

    if (!bestType) {
      return {
        isMatch: false,
        matchedType: '未知',
        matchReason: '未匹配到任何类型关键词',
        confidence: 0,
      };
    }

    const matchedSubType = this.matchSubType(text, bestType);
    let confidence = typeScores[bestType];

    if (matchedSubType && targetSubType && matchedSubType === targetSubType) {
      confidence = Math.min(100, confidence + CONFIDENCE_SCORES.SUBTYPE_HIT);
    }

    const isMatch = bestType === targetType || this.isTypeCompatible(bestType, targetType);

    return {
      isMatch,
      matchedType: bestType,
      matchedSubType: matchedSubType || undefined,
      matchReason: this.buildMatchReason(bestType, matchedSubType, text),
      confidence,
    };
  }

  private calculateTypeScores(text: string, buildingArea?: number): Record<string, number> {
    const scores: Record<string, number> = {};

    for (const [type, keywords] of Object.entries(TYPE_KEYWORDS)) {
      let score = 0;
      let hitKeyword = '';

      for (const keyword of keywords) {
        if (text.includes(keyword)) {
          score = Math.max(score, CONFIDENCE_SCORES.TYPE_HIT);
          hitKeyword = keyword;
          break;
        }
      }

      if (type === '住宅' && this.hasResidentialIndicators(text, buildingArea)) {
        score = Math.max(score, CONFIDENCE_SCORES.TYPE_HIT - 10);
      }

      if (score > 0 && buildingArea && buildingArea > 0) {
        score = Math.min(100, score + CONFIDENCE_SCORES.AREA_HINT);
      }

      scores[type] = score;
    }

    return scores;
  }

  private hasResidentialIndicators(text: string, buildingArea?: number): boolean {
    if (!buildingArea || buildingArea <= 0) return false;

    for (const indicator of RESIDENTIAL_INDICATORS) {
      if (text.includes(indicator)) {
        return true;
      }
    }

    return false;
  }

  private matchSubType(text: string, parentType: string): string | null {
    const subTypes = SUB_TYPE_KEYWORDS[parentType];
    if (!subTypes) return null;

    for (const [subType, keywords] of Object.entries(subTypes)) {
      for (const keyword of keywords) {
        if (text.includes(keyword)) {
          return subType;
        }
      }
    }

    return null;
  }

  private getBestType(typeScores: Record<string, number>): string | null {
    let bestType: string | null = null;
    let bestScore = 0;

    for (const [type, score] of Object.entries(typeScores)) {
      if (score > bestScore) {
        bestScore = score;
        bestType = type;
      }
    }

    return bestScore > 0 ? bestType : null;
  }

  private isTypeCompatible(matchedType: string, targetType: string): boolean {
    if (matchedType === targetType) return true;

    const compatible: Record<string, string[]> = {
      '住宅': ['住宅'],
      '商业': ['商业'],
      '工业': ['工业'],
      '土地': ['土地'],
      '特殊资产': ['特殊资产'],
    };

    return compatible[targetType]?.includes(matchedType) || false;
  }

  private buildMatchReason(type: string, subType: string | null, text: string): string {
    const typeKeywords = TYPE_KEYWORDS[type] || [];
    let hitKeyword = '';

    for (const keyword of typeKeywords) {
      if (text.includes(keyword)) {
        hitKeyword = keyword;
        break;
      }
    }

    if (subType) {
      return `命中关键词"${hitKeyword || subType}"，判定为${type}-${subType}`;
    }
    if (hitKeyword) {
      return `命中关键词"${hitKeyword}"，判定为${type}`;
    }
    return `根据特征判定为${type}`;
  }

  private normalizeText(text: string): string {
    return text.toLowerCase().replace(/\s+/g, '').trim();
  }

  batchMatch(cases: Array<{ title: string; description?: string; buildingArea?: number }>, targetType: string): MatchResult[] {
    return cases.map(c => this.match({
      title: c.title,
      description: c.description,
      buildingArea: c.buildingArea,
      targetType,
    }));
  }
}
