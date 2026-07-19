export const DEFAULT_CONFIG = {
  addressSimilarityThreshold: 0.8,
  areaTolerance: 0.1,
};

export const ROUND_PRIORITY: Record<string, number> = {
  '变卖': 3,
  '二拍': 2,
  '一拍': 1,
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

export const GROUP_KEY_PATTERNS = {
  COMMUNITY: /(.+?小区|.+?花园|.+?苑|.+?府|.+?城|.+?庭|.+?公馆|.+?雅居)/,
  BUILDING: /(\d+[栋座号楼幢])/,
  ROAD: /(.+?[路街道])(\d+号)?/,
};
