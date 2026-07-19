export type AssetType = '住宅' | '商业' | '工业' | '土地' | '特殊资产';

export interface MatchRequest {
  title: string;
  description?: string;
  buildingArea?: number;
  targetType: AssetType | string;
  targetSubType?: string;
}

export interface MatchResult {
  isMatch: boolean;
  matchedType: string;
  matchedSubType?: string;
  matchReason: string;
  confidence: number;
  matchedKeyword?: string;
}

export interface TypeKeywords {
  [type: string]: string[];
}

export interface SubTypeKeywords {
  [parentType: string]: {
    [subType: string]: string[];
  };
}
