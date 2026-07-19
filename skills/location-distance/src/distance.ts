import type { LocationPoint, DistanceResult, BatchDistanceRequest, BatchDistanceResult, LocationDistanceConfig } from './types';
import { EARTH_RADIUS, DEFAULT_DISTANCE_MULTIPLIER, AMAP_DRIVING_URL } from './constants';

export class DistanceCalculator {
  private apiKey: string;
  private drivingUrl: string;
  private distanceMultiplier: number;

  constructor(config: LocationDistanceConfig) {
    this.apiKey = config.amapKey || '';
    this.drivingUrl = config.amapUrl ? config.amapUrl.replace('geo', 'direction/driving') : AMAP_DRIVING_URL;
    this.distanceMultiplier = config.distanceMultiplier || DEFAULT_DISTANCE_MULTIPLIER;
  }

  haversineDistance(p1: LocationPoint, p2: LocationPoint): number {
    const lat1 = this.toRad(p1.lat);
    const lat2 = this.toRad(p2.lat);
    const dLat = this.toRad(p2.lat - p1.lat);
    const dLng = this.toRad(p2.lng - p1.lng);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(dLng / 2) * Math.sin(dLng / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return EARTH_RADIUS * c;
  }

  async drivingDistance(origin: LocationPoint, dest: LocationPoint): Promise<DistanceResult> {
    const straightDist = this.haversineDistance(origin, dest);

    if (!this.apiKey) {
      return {
        straightDistance: straightDist,
        drivingDistance: straightDist * this.distanceMultiplier,
        drivingDuration: 0,
      };
    }

    try {
      const params = new URLSearchParams({
        key: this.apiKey,
        origin: `${origin.lng},${origin.lat}`,
        destination: `${dest.lng},${dest.lat}`,
        output: 'json',
        strategy: '2',
      });

      const response = await fetch(`${this.drivingUrl}?${params.toString()}`);
      const data = await response.json();

      if (data.status === '1' && data.route?.paths?.length > 0) {
        const path = data.route.paths[0];
        return {
          straightDistance: straightDist,
          drivingDistance: Number(path.distance),
          drivingDuration: Number(path.duration),
        };
      }

      return {
        straightDistance: straightDist,
        drivingDistance: straightDist * this.distanceMultiplier,
      };
    } catch (error) {
      console.warn('[DistanceCalculator] Driving distance API failed:', error);
      return {
        straightDistance: straightDist,
        drivingDistance: straightDist * this.distanceMultiplier,
      };
    }
  }

  batchStraightDistance(origin: LocationPoint, destinations: LocationPoint[]): number[] {
    return destinations.map(dest => this.haversineDistance(origin, dest));
  }

  async batchDrivingDistance(request: BatchDistanceRequest): Promise<BatchDistanceResult> {
    const { origin, destinations, maxStraightDistance } = request;
    const results: (DistanceResult & { index: number })[] = [];
    const passIndexes: number[] = [];
    const filteredIndexes: number[] = [];

    const straightDists = this.batchStraightDistance(origin, destinations);

    for (let i = 0; i < destinations.length; i++) {
      const straightDist = straightDists[i];

      if (maxStraightDistance && straightDist > maxStraightDistance * this.distanceMultiplier) {
        results.push({
          index: i,
          straightDistance: straightDist,
        });
        filteredIndexes.push(i);
        continue;
      }

      const drivingResult = await this.drivingDistance(origin, destinations[i]);
      results.push({
        index: i,
        ...drivingResult,
      });
      passIndexes.push(i);
    }

    return {
      results,
      filteredIndexes,
      passIndexes,
    };
  }

  private toRad(deg: number): number {
    return deg * (Math.PI / 180);
  }
}
