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
  startPrice?: number;
  endTime?: string;
  bidCount?: number;
}

export interface SearchRequest {
  keywords: string[];
  propertyType: string;
  assetType: string;
  maxPages?: number;
  pageSize?: number;
  platforms?: Platform[];
}

export interface SearchResult {
  cases: AuctionCase[];
  totalCount: number;
  platforms: Platform[];
  searchLog: SearchLogEntry[];
}

export interface SearchLogEntry {
  keyword: string;
  platform: Platform;
  page: number;
  resultCount: number;
  duration: number;
  success: boolean;
  error?: string;
}

export interface SearchEngineConfig {
  maxPages: number;
  pageSize: number;
  taobaoEnabled: boolean;
  jdEnabled: boolean;
  deduplicate: boolean;
}

export interface PlatformSearcher {
  search(keyword: string, options: SearchOptions): Promise<AuctionCase[]>;
}

export interface SearchOptions {
  propertyType: string;
  assetType: string;
  page: number;
  pageSize: number;
}
