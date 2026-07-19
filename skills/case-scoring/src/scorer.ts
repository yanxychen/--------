import type {
  ScoringCase,
  ScoredCase,
  ScoreBreakdown,
  ScoringRequest,
  ScoringResult,
  ScoreConfig,
  SortPriority,
  PropertyType,
} from './types';
import { DEFAULT_CONFIG, DEFAULT_SORT_PRIORITY, PROPERTY_TYPE_DISTANCE_MULTIPLIER } from './constants';

export class CaseScorer {
  private config: ScoreConfig;
  private propertyType: PropertyType;
  private targetArea: number;
  private sortPriority: SortPriority[];

  constructor(options: {
    propertyType: PropertyType;
    targetArea: number;
    config?: Partial<ScoreConfig>;
    sortPriority?: SortPriority[];
  }) {
    this.propertyType = options.propertyType;
    this.targetArea = options.targetArea;
    this.config = { ...DEFAULT_CONFIG, ...options.config };
    this.sortPriority = options.sortPriority || DEFAULT_SORT_PRIORITY;
  }

  scoreAndSort(request: ScoringRequest): ScoringResult {
    const { cases, selfAuctionItemIds = [] } = request;

    const selfAuctionCases = cases.filter(c => selfAuctionItemIds.includes(c.itemId));
    const otherCases = cases.filter(c => !selfAuctionItemIds.includes(c.itemId));

    const scoredCases = otherCases.map(c => this.scoreCase(c));
    const sortedCases = this.sortCases(scoredCases);

    const scoreBreakdowns = sortedCases.map(c => c.scoreBreakdown);

    return {
      scoredCases: sortedCases,
      selfAuctionCases,
      scoreBreakdowns,
      sortPriority: this.sortPriority,
    };
  }

  private scoreCase(caseItem: ScoringCase): ScoredCase {
    const distanceScore = this.calculateDistanceScore(caseItem);
    const areaScore = this.calculateAreaScore(caseItem);
    const timeScore = this.calculateTimeScore(caseItem);
    const totalScore = distanceScore + areaScore + timeScore;

    const distance = caseItem.drivingDistance ?? caseItem.straightDistance ?? 99999;
    const areaDiffRatio = this.targetArea > 0
      ? Math.abs(caseItem.buildingArea - this.targetArea) / this.targetArea
      : 1;
    const daysAgo = this.calculateDaysAgo(caseItem.auctionTime);

    const breakdown: ScoreBreakdown = {
      itemId: caseItem.itemId,
      distanceScore,
      areaScore,
      timeScore,
      totalScore,
      distance,
      areaDiffRatio,
      daysAgo,
    };

    return {
      ...caseItem,
      totalScore,
      distanceScore,
      areaScore,
      timeScore,
      scoreBreakdown: breakdown,
    };
  }

  private calculateDistanceScore(caseItem: ScoringCase): number {
    const distance = caseItem.drivingDistance ?? caseItem.straightDistance;

    if (distance === undefined || distance === null) {
      return this.config.distanceScores[this.config.distanceScores.length - 1];
    }

    const multiplier = PROPERTY_TYPE_DISTANCE_MULTIPLIER[this.propertyType] || 1;
    const adjustedDistance = distance * multiplier;

    for (let i = 0; i < this.config.distanceThresholds.length; i++) {
      if (adjustedDistance <= this.config.distanceThresholds[i]) {
        return this.config.distanceScores[i];
      }
    }

    return this.config.distanceScores[this.config.distanceScores.length - 1];
  }

  private calculateAreaScore(caseItem: ScoringCase): number {
    const area = caseItem.buildingArea;

    if (!area || area <= 0 || this.targetArea <= 0) {
      return this.config.areaScores[this.config.areaScores.length - 1];
    }

    const diffRatio = Math.abs(area - this.targetArea) / this.targetArea;

    for (let i = 0; i < this.config.areaDiffThresholds.length; i++) {
      if (diffRatio <= this.config.areaDiffThresholds[i]) {
        return this.config.areaScores[i];
      }
    }

    return this.config.areaScores[this.config.areaScores.length - 1];
  }

  private calculateTimeScore(caseItem: ScoringCase): number {
    const daysAgo = this.calculateDaysAgo(caseItem.auctionTime);

    if (daysAgo < 0) {
      return this.config.timeScores[0];
    }

    for (let i = 0; i < this.config.timeThresholds.length; i++) {
      if (daysAgo <= this.config.timeThresholds[i]) {
        return this.config.timeScores[i];
      }
    }

    return this.config.timeScores[this.config.timeScores.length - 1];
  }

  private calculateDaysAgo(auctionTime: string): number {
    if (!auctionTime) {
      return 9999;
    }

    const auctionDate = new Date(auctionTime);
    if (isNaN(auctionDate.getTime())) {
      return 9999;
    }

    const now = new Date();
    const diffTime = now.getTime() - auctionDate.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    return diffDays;
  }

  private sortCases(cases: ScoredCase[]): ScoredCase[] {
    return [...cases].sort((a, b) => {
      for (const priority of this.sortPriority) {
        const cmp = this.compareByPriority(a, b, priority);
        if (cmp !== 0) return cmp;
      }
      return 0;
    });
  }

  private compareByPriority(a: ScoredCase, b: ScoredCase, priority: SortPriority): number {
    switch (priority) {
      case 'totalScore':
        return b.totalScore - a.totalScore;
      case 'distance':
        const distA = a.drivingDistance ?? a.straightDistance ?? 99999;
        const distB = b.drivingDistance ?? b.straightDistance ?? 99999;
        return distA - distB;
      case 'area':
        const diffA = Math.abs(a.buildingArea - this.targetArea);
        const diffB = Math.abs(b.buildingArea - this.targetArea);
        return diffA - diffB;
      case 'time':
        const timeA = this.calculateDaysAgo(a.auctionTime);
        const timeB = this.calculateDaysAgo(b.auctionTime);
        return timeA - timeB;
      default:
        return 0;
    }
  }
}
