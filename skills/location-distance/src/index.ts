import type { LocationDistanceConfig, GeocodeRequest, GeocodeResult, LocationPoint, DistanceResult, BatchDistanceRequest, BatchDistanceResult, KeywordExtractionResult } from './types';
import { Geocoder } from './geocoder';
import { DistanceCalculator } from './distance';
import { KeywordExtractor } from './keywords';

export class LocationDistance {
  private geocoder: Geocoder;
  private distanceCalculator: DistanceCalculator;
  private keywordExtractor: KeywordExtractor;

  constructor(config: LocationDistanceConfig = {}) {
    this.geocoder = new Geocoder(config);
    this.distanceCalculator = new DistanceCalculator(config);
    this.keywordExtractor = new KeywordExtractor();
  }

  async geocode(request: GeocodeRequest): Promise<GeocodeResult | null> {
    return this.geocoder.geocode(request);
  }

  async batchGeocode(addresses: string[], city?: string): Promise<(GeocodeResult | null)[]> {
    return this.geocoder.batchGeocode(addresses, city);
  }

  haversineDistance(p1: LocationPoint, p2: LocationPoint): number {
    return this.distanceCalculator.haversineDistance(p1, p2);
  }

  async drivingDistance(origin: LocationPoint, dest: LocationPoint): Promise<DistanceResult> {
    return this.distanceCalculator.drivingDistance(origin, dest);
  }

  async batchDrivingDistance(request: BatchDistanceRequest): Promise<BatchDistanceResult> {
    return this.distanceCalculator.batchDrivingDistance(request);
  }

  extractKeywords(address: string): KeywordExtractionResult {
    return this.keywordExtractor.extract(address);
  }

  async locateAndExtract(address: string, city?: string): Promise<{
    location: GeocodeResult | null;
    keywords: string[];
  }> {
    const location = await this.geocode({ address, city });
    const keywordResult = this.keywordExtractor.extract(address);

    let keywords = keywordResult.keywords;

    if (location) {
      const districtKeyword = location.district;
      const cityKeyword = location.city;

      if (districtKeyword && !keywords.includes(districtKeyword)) {
        keywords.push(districtKeyword);
      }
      if (cityKeyword && !keywords.includes(cityKeyword)) {
        keywords.push(cityKeyword);
      }
    }

    return {
      location,
      keywords: [...new Set(keywords)],
    };
  }
}

export {
  type LocationDistanceConfig,
  type GeocodeRequest,
  type GeocodeResult,
  type LocationPoint,
  type DistanceResult,
  type BatchDistanceRequest,
  type BatchDistanceResult,
  type KeywordExtractionResult,
};
