export type Platform = 'taobao' | 'jd';
export type AuctionRound = '一拍' | '二拍' | '变卖';

export interface AuctionCase {
  itemId: string;
  platform: Platform;
  title: string;
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
  detailUrl: string;
}

export interface AuctionHistoryItem {
  itemId: string;
  platform: Platform;
  round: string;
  price: number;
  time: string;
  status: string;
  detailUrl: string;
}

export interface MergedCase extends AuctionCase {
  auctionHistory: AuctionHistoryItem[];
  mergeGroupId: string;
}

export interface MergeRequest {
  cases: AuctionCase[];
}

export interface MergeResult {
  mergedCases: MergedCase[];
  mergeCount: number;
  mergeLog: MergeLogEntry[];
}

export interface MergeLogEntry {
  groupId: string;
  groupKey: string;
  caseCount: number;
  caseIds: string[];
  mainCaseId: string;
  rounds: string[];
}

export interface MergerConfig {
  addressSimilarityThreshold: number;
  areaTolerance: number;
}
