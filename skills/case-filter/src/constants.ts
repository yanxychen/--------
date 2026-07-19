import type { PropertyType, FilterConfig } from './types';

export const DEFAULT_MIN_CASES = 3;

export const DISTANCE_LEVELS: Record<PropertyType, number[]> = {
  residential: [500, 1000, 2000, 3000, 5000],
  commercial: [500, 1000, 2000, 3000, 5000],
  industrial: [1000, 3000, 5000, 10000],
  land: [1000, 3000, 5000, 10000],
  special: [1000, 3000, 5000, 10000],
};

export const TIME_LEVELS = [90, 180, 365, 730];

export const DISTANCE_LABELS: Record<PropertyType, string[]> = {
  residential: ['500m内', '1km内', '2km内', '3km内', '5km内'],
  commercial: ['500m内', '1km内', '2km内', '3km内', '5km内'],
  industrial: ['1km内', '3km内', '5km内', '10km内'],
  land: ['1km内', '3km内', '5km内', '10km内'],
  special: ['1km内', '3km内', '5km内', '10km内'],
};

export const TIME_LABELS = ['3个月内', '6个月内', '1年内', '2年内'];

export const DEFAULT_CONFIG: FilterConfig = {
  minCases: DEFAULT_MIN_CASES,
  residentialDistanceLevels: DISTANCE_LEVELS.residential,
  commercialDistanceLevels: DISTANCE_LEVELS.commercial,
  industrialDistanceLevels: DISTANCE_LEVELS.industrial,
  landDistanceLevels: DISTANCE_LEVELS.land,
  specialDistanceLevels: DISTANCE_LEVELS.special,
  timeLevels: TIME_LEVELS,
};

export const FILTER_STEPS = {
  TYPE: 'type_filter',
  DISTANCE: 'distance_filter',
  TIME: 'time_filter',
  RELAX_DISTANCE: 'relax_distance',
  RELAX_TIME: 'relax_time',
};
