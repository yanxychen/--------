import type { GeocodeRequest, GeocodeResult, LocationDistanceConfig } from './types';
import { AMAP_GEOCODE_URL } from './constants';

export class Geocoder {
  private apiKey: string;
  private baseUrl: string;

  constructor(config: LocationDistanceConfig) {
    this.apiKey = config.amapKey || '';
    this.baseUrl = config.amapUrl || AMAP_GEOCODE_URL;
  }

  async geocode(request: GeocodeRequest): Promise<GeocodeResult | null> {
    if (!this.apiKey) {
      return this.fallbackGeocode(request.address);
    }

    try {
      const params = new URLSearchParams({
        key: this.apiKey,
        address: request.address,
        city: request.city || '',
        output: 'json',
      });

      const response = await fetch(`${this.baseUrl}?${params.toString()}`);
      const data = await response.json();

      if (data.status === '1' && data.geocodes && data.geocodes.length > 0) {
        const geo = data.geocodes[0];
        const [lng, lat] = geo.location.split(',').map(Number);

        return {
          longitude: lng,
          latitude: lat,
          formattedAddress: geo.formatted_address,
          province: geo.province,
          city: geo.city,
          district: geo.district,
          township: geo.township,
          neighborhood: geo.neighborhood?.name,
          building: geo.building?.name,
          adcode: geo.adcode,
          level: geo.level,
        };
      }

      return null;
    } catch (error) {
      console.warn('[Geocoder] API request failed:', error);
      return this.fallbackGeocode(request.address);
    }
  }

  private fallbackGeocode(address: string): GeocodeResult | null {
    const provinceMatch = address.match(/(.+省|.+市)/);
    const cityMatch = address.match(/(.+市)/);
    const districtMatch = address.match(/(.+区|.+县)/);

    if (!cityMatch) return null;

    return {
      longitude: 0,
      latitude: 0,
      formattedAddress: address,
      province: provinceMatch?.[1] || '',
      city: cityMatch[1],
      district: districtMatch?.[1] || '',
      adcode: '',
    };
  }

  async batchGeocode(addresses: string[], city?: string): Promise<(GeocodeResult | null)[]> {
    const results = [];
    for (const address of addresses) {
      const result = await this.geocode({ address, city });
      results.push(result);
    }
    return results;
  }
}
