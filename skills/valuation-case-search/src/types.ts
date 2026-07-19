export type OutputFormat = 'markdown' | 'json' | 'html';
export type PropertyType = 'residential' | 'commercial' | 'industrial' | 'land' | 'special';

export interface SearchRequest {
  address: string;
  propertyType: string;
  buildingArea?: number;
  options?: {
    output?: OutputFormat;
    minCases?: number;
  };
}

export interface StepResult<T> {
  stepName: string;
  stepIndex: number;
  success: boolean;
  data: T;
  error?: string;
  durationMs: number;
}

export interface StepStatus {
  name: string;
  index: number;
  status: 'pending' | 'running' | 'done' | 'error';
  durationMs?: number;
  error?: string;
}

export interface SearchMeta {
  totalDurationMs: number;
  steps: StepStatus[];
  totalCases: number;
  scoredCases: number;
  selfAuctionCases: number;
  filteredCases: number;
}

export interface SearchResult {
  markdown: string;
  data: V1CaseRow[];
  meta: SearchMeta;
}

export interface V1CaseRow {
  referenceLocation: string;
  landArea: string;
  buildingArea: number | string;
  marketValue: number | string;
  unitPrice: number | string;
  source: string;
  remark: string;
  priceType: string;
}

export interface LocationResult {
  longitude: number;
  latitude: number;
  keywords: string[];
}

export interface SearchResultCase {
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
  matchedType?: string;
  auctionRecords?: AuctionRecord[];
}

export interface AuctionRecord {
  round: string;
  date: string;
  startPrice: number;
  endPrice?: number;
  status: string;
}

export interface ScoredCase extends SearchResultCase {
  totalScore: number;
  distanceScore: number;
  areaScore: number;
  timeScore: number;
  scoreBreakdown: {
    itemId: string;
    distanceScore: number;
    areaScore: number;
    timeScore: number;
    totalScore: number;
    distance: number;
    areaDiffRatio: number;
    daysAgo: number;
  };
}
