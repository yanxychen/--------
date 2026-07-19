export const DEFAULT_CONFIG = {
  maxPages: 3,
  pageSize: 20,
  taobaoEnabled: true,
  jdEnabled: true,
  deduplicate: true,
};

export const TAOBAO_BASE_URL = 'https://sf.taobao.com';
export const JD_BASE_URL = 'https://auction.jd.com';

export const PROPERTY_TYPE_MAP: Record<string, string> = {
  residential: '住宅',
  commercial: '商业',
  industrial: '工业',
  land: '土地',
  special: '特殊资产',
};

export const AUCTION_STATUS = {
  UPCOMING: '即将开始',
  ONGOING: '正在进行',
  ENDED: '已结束',
  SOLD: '已成交',
  FAILED: '流拍',
};

export const DEDUP_CONFIG = {
  titleSimilarityThreshold: 0.7,
  locationSimilarityThreshold: 0.8,
};
