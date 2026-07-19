export interface AuctionCase {
  itemId: string;
  platform: 'taobao' | 'jd';
  title: string;
  fullAddress: string;
  buildingArea: number;
  longitude?: number;
  latitude?: number;
  detailUrl: string;
}

export interface DetectRequest {
  cases: AuctionCase[];
  targetAddress: string;
  targetArea?: number;
  targetLng?: number;
  targetLat?: number;
}

export interface DetectResult {
  selfAuctionCases: AuctionCase[];
  selfAuctionItemIds: string[];
  otherCases: AuctionCase[];
  matchDetails: MatchDetail[];
}

export type MatchType = 'address_area' | 'address_only' | 'area_only' | 'location' | 'none';

export interface MatchDetail {
  itemId: string;
  isSelfAuction: boolean;
  matchType: MatchType;
  addressSimilarity: number;
  areaSimilarity: number;
  locationDistance?: number;
  confidence: number;
}

export interface DetectorConfig {
  addressSimilarityThreshold: number;
  areaTolerance: number;
  locationDistanceThreshold: number;
  highConfidenceThreshold: number;
  mediumConfidenceThreshold: number;
}
