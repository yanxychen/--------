export type SortPriority = 'totalScore' | 'distance' | 'area' | 'time';
export type PropertyType = 'residential' | 'commercial' | 'industrial' | 'land' | 'special';

export interface ScoringCase {
  itemId: string;
  platform: 'taobao' | 'jd';
  title: string;
  fullAddress: string;
  buildingArea: number;
  marketValue: number;
  auctionTime: string;
  auctionStatus: string;
  auctionRound: string;
  drivingDistance?: number;
  straightDistance?: number;
  sourceUrl: string;
}

export interface ScoreBreakdown {
  itemId: string;
  distanceScore: number;
  areaScore: number;
  timeScore: number;
  totalScore: number;
  distance: number;
  areaDiffRatio: number;
  daysAgo: number;
}

export interface ScoredCase extends ScoringCase {
  totalScore: number;
  distanceScore: number;
  areaScore: number;
  timeScore: number;
  scoreBreakdown: ScoreBreakdown;
}

export interface ScoringRequest {
  cases: ScoringCase[];
  propertyType: PropertyType;
  targetArea: number;
  selfAuctionItemIds?: string[];
  sortPriority?: SortPriority[];
}

export interface ScoringResult {
  scoredCases: ScoredCase[];
  selfAuctionCases: ScoringCase[];
  scoreBreakdowns: ScoreBreakdown[];
  sortPriority: SortPriority[];
}

export interface ScoreConfig {
  distanceWeight: number;
  areaWeight: number;
  timeWeight: number;
  distanceThresholds: number[];
  distanceScores: number[];
  areaDiffThresholds: number[];
  areaScores: number[];
  timeThresholds: number[];
  timeScores: number[];
}
