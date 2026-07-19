import type { PropertyType } from './types';

export const STEP_NAMES = [
  'location-distance',
  'case-search-engine',
  'asset-type-matcher',
  'case-detail-enricher',
  'self-auction-detector',
  'case-merger',
  'case-filter',
  'case-scoring',
  'v1-valuation-format',
] as const;

export const STEP_COUNT = STEP_NAMES.length;

export const DEFAULT_MIN_CASES = 3;

export const DEFAULT_OUTPUT_FORMAT = 'markdown' as const;

export const PROPERTY_TYPE_MAP: Record<string, PropertyType> = {
  '住宅': 'residential',
  '住宅类': 'residential',
  '商业': 'commercial',
  '商业类': 'commercial',
  '工业': 'industrial',
  '工业类': 'industrial',
  '土地': 'land',
  '土地类': 'land',
  '特殊资产': 'special',
  '其他': 'special',
};
