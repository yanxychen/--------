import type { PropertyType, ScoreConfig, SortPriority } from './types';

export const DEFAULT_SORT_PRIORITY: SortPriority[] = ['totalScore', 'distance', 'time'];

export const DISTANCE_WEIGHT = 50;
export const AREA_WEIGHT = 30;
export const TIME_WEIGHT = 20;

export const DISTANCE_THRESHOLDS = [500, 1000, 2000, 3000, 5000];
export const DISTANCE_SCORES = [50, 45, 37.5, 30, 15, 5];

export const AREA_DIFF_THRESHOLDS = [0.1, 0.2, 0.3, 0.5];
export const AREA_SCORES = [30, 25, 20, 12, 5];

export const TIME_THRESHOLDS = [90, 180, 365, 540, 730];
export const TIME_SCORES = [20, 17, 13, 8, 4, 1];

export const DISTANCE_LABELS = ['500m内', '1km内', '2km内', '3km内', '5km内', '5km以上'];
export const AREA_DIFF_LABELS = ['10%以内', '20%以内', '30%以内', '50%以内', '50%以上'];
export const TIME_LABELS = ['3个月内', '6个月内', '1年内', '1.5年内', '2年内', '2年以上'];

export const DEFAULT_CONFIG: ScoreConfig = {
  distanceWeight: DISTANCE_WEIGHT,
  areaWeight: AREA_WEIGHT,
  timeWeight: TIME_WEIGHT,
  distanceThresholds: DISTANCE_THRESHOLDS,
  distanceScores: DISTANCE_SCORES,
  areaDiffThresholds: AREA_DIFF_THRESHOLDS,
  areaScores: AREA_SCORES,
  timeThresholds: TIME_THRESHOLDS,
  timeScores: TIME_SCORES,
};

export const PROPERTY_TYPE_DISTANCE_MULTIPLIER: Record<PropertyType, number> = {
  residential: 1,
  commercial: 1,
  industrial: 2,
  land: 2,
  special: 2,
};
