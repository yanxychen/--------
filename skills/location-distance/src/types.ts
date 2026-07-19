export interface GeocodeRequest {
  address: string;
  city?: string;
}

export interface GeocodeResult {
  longitude: number;
  latitude: number;
  formattedAddress: string;
  province: string;
  city: string;
  district: string;
  township?: string;
  neighborhood?: string;
  building?: string;
  adcode?: string;
  level?: string;
}

export interface LocationPoint {
  lng: number;
  lat: number;
}

export interface DistanceResult {
  straightDistance: number;
  drivingDistance?: number;
  drivingDuration?: number;
}

export interface BatchDistanceRequest {
  origin: LocationPoint;
  destinations: LocationPoint[];
  maxStraightDistance?: number;
}

export interface BatchDistanceResult {
  results: (DistanceResult & { index: number }[];
  filteredIndexes: number[];
  passIndexes: number[];
}

export interface KeywordExtractionResult {
  keywords: string[];
  levels: {
    fullCommunity: string;
    community: string;
    business: string;
    district: string;
    city: string;
  };
}

export interface LocationDistanceConfig {
  amapKey?: string;
  amapUrl?: string;
  distanceMultiplier?: number;
}
