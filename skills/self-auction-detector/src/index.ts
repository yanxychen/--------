import type {
  DetectRequest,
  DetectResult,
  MatchDetail,
  MatchType,
  AuctionCase,
  DetectorConfig,
} from './types';
import { DEFAULT_CONFIG } from './constants';
import { AddressMatcher } from './address-matcher';
import { AreaMatcher } from './area-matcher';

export class SelfAuctionDetector {
  private config: DetectorConfig;
  private addressMatcher: AddressMatcher;
  private areaMatcher: AreaMatcher;

  constructor(config: Partial<DetectorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.addressMatcher = new AddressMatcher();
    this.areaMatcher = new AreaMatcher(this.config.areaTolerance);
  }

  detect(request: DetectRequest): DetectResult {
    const { cases, targetAddress, targetArea, targetLng, targetLat } = request;

    const selfAuctionCases: AuctionCase[] = [];
    const selfAuctionItemIds: string[] = [];
    const otherCases: AuctionCase[] = [];
    const matchDetails: MatchDetail[] = [];

    for (const caseItem of cases) {
      const detail = this.matchCase(caseItem, targetAddress, targetArea, targetLng, targetLat);
      matchDetails.push(detail);

      if (detail.isSelfAuction) {
        selfAuctionCases.push(caseItem);
        selfAuctionItemIds.push(caseItem.itemId);
      } else {
        otherCases.push(caseItem);
      }
    }

    return {
      selfAuctionCases,
      selfAuctionItemIds,
      otherCases,
      matchDetails,
    };
  }

  private matchCase(
    caseItem: AuctionCase,
    targetAddress: string,
    targetArea?: number,
    targetLng?: number,
    targetLat?: number
  ): MatchDetail {
    const addressSimilarity = this.addressMatcher.calculateSimilarity(
      caseItem.fullAddress || caseItem.title,
      targetAddress
    );

    const areaSimilarity = targetArea && caseItem.buildingArea
      ? this.areaMatcher.calculateSimilarity(targetArea, caseItem.buildingArea)
      : 0;

    let locationDistance: number | undefined;
    if (targetLng && targetLat && caseItem.longitude && caseItem.latitude) {
      locationDistance = this.haversineDistance(
        targetLng, targetLat,
        caseItem.longitude, caseItem.latitude
      );
    }

    const { isSelfAuction, matchType, confidence } = this.determineMatch(
      addressSimilarity,
      areaSimilarity,
      locationDistance,
      targetArea !== undefined,
      caseItem.buildingArea > 0
    );

    return {
      itemId: caseItem.itemId,
      isSelfAuction,
      matchType,
      addressSimilarity,
      areaSimilarity,
      locationDistance,
      confidence,
    };
  }

  private determineMatch(
    addressSimilarity: number,
    areaSimilarity: number,
    locationDistance: number | undefined,
    hasTargetArea: boolean,
    hasCaseArea: boolean
  ): { isSelfAuction: boolean; matchType: MatchType; confidence: number } {
    const addressMatch = addressSimilarity >= this.config.addressSimilarityThreshold;
    const areaMatch = areaSimilarity >= (1 - this.config.areaTolerance);
    const locationMatch = locationDistance !== undefined &&
      locationDistance <= this.config.locationDistanceThreshold;

    if (addressMatch && hasTargetArea && hasCaseArea && areaMatch) {
      return {
        isSelfAuction: true,
        matchType: 'address_area',
        confidence: this.calculateConfidence(addressSimilarity, areaSimilarity, locationMatch),
      };
    }

    if (addressSimilarity >= 0.9 && (!hasTargetArea || !hasCaseArea)) {
      return {
        isSelfAuction: true,
        matchType: 'address_only',
        confidence: Math.min(95, addressSimilarity * 90 + 10),
      };
    }

    if (locationMatch && hasTargetArea && hasCaseArea && areaMatch) {
      return {
        isSelfAuction: true,
        matchType: 'location',
        confidence: 80,
      };
    }

    if (addressMatch) {
      return {
        isSelfAuction: true,
        matchType: 'address_only',
        confidence: 75,
      };
    }

    return {
      isSelfAuction: false,
      matchType: 'none',
      confidence: Math.max(0, addressSimilarity * 50),
    };
  }

  private calculateConfidence(
    addressSimilarity: number,
    areaSimilarity: number,
    locationMatch: boolean
  ): number {
    let confidence = 0;

    confidence += addressSimilarity * 50;
    confidence += areaSimilarity * 30;

    if (locationMatch) {
      confidence += 20;
    }

    return Math.min(100, Math.max(0, Math.round(confidence)));
  }

  private haversineDistance(lng1: number, lat1: number, lng2: number, lat2: number): number {
    const R = 6371000;
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lng2 - lng1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  }
}

export {
  type DetectRequest,
  type DetectResult,
  type MatchDetail,
  type MatchType,
  type AuctionCase,
  type DetectorConfig,
};
