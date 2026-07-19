export type FilterMode = 'rough' | 'fine';
export type PropertyType = 'residential' | 'commercial' | 'industrial' | 'land' | 'special';

export interface FilterCase {
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
  matchedType?: string;
}

export interface FilterRequest {
  cases: FilterCase[];
  propertyType: PropertyType;
  assetType: string;
  selfAuctionItemIds?: string[];
  minCases?: number;
  mode?: FilterMode;
}

export interface FilterResult {
  filteredCases: FilterCase[];
  filterLog: FilterLogEntry[];
  usedDistanceThreshold: number;
  usedTimeThreshold: number;
  distanceLevel: number;
  timeLevel: number;
}

export interface FilterLogEntry {
  step: string;
  distanceLevel: number;
  timeLevel: number;
  distanceThreshold: number;
  timeThreshold: number;
  beforeCount: number;
  afterCount: number;
  filteredCount: number;
}

export interface DistanceLevel {
  level: number;
  threshold: number;
  label: string;
}

export interface TimeLevel {
  level: number;
  threshold: number;
  label: string;
}

export interface FilterConfig {
  minCases: number;
  residentialDistanceLevels: number[];
  commercialDistanceLevels: number[];
  industrialDistanceLevels: number[];
  landDistanceLevels: number[];
  specialDistanceLevels: number[];
  timeLevels: number[];
}
