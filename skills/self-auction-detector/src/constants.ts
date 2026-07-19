export const DEFAULT_CONFIG = {
  addressSimilarityThreshold: 0.85,
  areaTolerance: 0.1,
  locationDistanceThreshold: 100,
  highConfidenceThreshold: 90,
  mediumConfidenceThreshold: 70,
};

export const MATCH_TYPE_LABELS: Record<string, string> = {
  address_area: '地址+面积双匹配',
  address_only: '地址匹配',
  area_only: '面积匹配',
  location: '位置匹配',
  none: '不匹配',
};

export const ADDRESS_NOISE_PATTERNS = [
  /\d+室\d+厅\d+卫/g,
  /\d+单元\d+室/g,
  /\d+楼\d+层/g,
  /第\d+层/g,
  /\d+号房/g,
  /房号[:：]?\d+/g,
  /单元号[:：]?\d+/g,
  /[（(].*?[）)]/g,
];

export const ADDRESS_NORMALIZE_MAP: Record<string, string> = {
  '号': '',
  '栋': '座',
  '号楼': '座',
  '幢': '座',
  '座': '座',
  '＃': '号',
  '#': '号',
};
