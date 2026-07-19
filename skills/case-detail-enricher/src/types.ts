export type Platform = 'taobao' | 'jd';

export interface AuctionCase {
  itemId: string;
  platform: Platform;
  title: string;
  currentPrice: number;
  location: string;
  detailUrl: string;
  searchKeyword: string;
  auctionStatus?: string;
  category?: string;
}

export interface EnrichedCase extends AuctionCase {
  fullAddress: string;
  buildingArea: number;
  landArea?: number;
  marketValue: number;
  unitPrice: number;
  startPrice: number;
  auctionTime: string;
  auctionStatus: string;
  auctionRound: string;
  priceType: string;
  bidCount?: number;
  court?: string;
  endTime?: string;
  assessmentPrice?: number;
}

export interface EnrichRequest {
  cases: AuctionCase[];
  platform?: Platform;
  maxRetries?: number;
  concurrency?: number;
  delay?: number;
}

export interface EnrichResult {
  enrichedCases: EnrichedCase[];
  enrichCount: number;
  failCount: number;
  failLog: FailLogEntry[];
}

export interface FailLogEntry {
  itemId: string;
  platform: Platform;
  title: string;
  error: string;
  retryCount: number;
}

export interface DetailEnricherConfig {
  maxRetries: number;
  concurrency: number;
  delay: number;
}
