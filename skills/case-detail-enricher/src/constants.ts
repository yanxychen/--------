export const DEFAULT_CONFIG = {
  maxRetries: 2,
  concurrency: 3,
  delay: 1000,
};

export const AUCTION_STATUS = {
  UPCOMING: '即将开始',
  ONGOING: '正在进行',
  SOLD: '已成交',
  FAILED: '流拍',
  FAILED_SALE: '变卖失败',
  ENDED: '已结束',
};

export const AUCTION_ROUNDS = {
  FIRST: '一拍',
  SECOND: '二拍',
  SALE: '变卖',
};

export const PRICE_TYPE_DEFAULT = '普通司法拍卖';

export const DATE_PATTERNS = [
  /开拍时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?\s*\d{0,2}[:：]?\d{0,2})/,
  /拍卖开始时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?\s*\d{0,2}[:：]?\d{0,2})/,
  /起拍时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?\s*\d{0,2}[:：]?\d{0,2})/,
  /开始时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?\s*\d{0,2}[:：]?\d{0,2})/,
  /变卖开始时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?\s*\d{0,2}[:：]?\d{0,2})/,
  /拍卖时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?\s*\d{0,2}[:：]?\d{0,2})/,
];

export const AREA_PATTERNS = [
  /建筑面积[：:]\s*([\d.,]+\s*[㎡平方米m²M²]+)/i,
  /房屋面积[：:]\s*([\d.,]+\s*[㎡平方米m²M²]+)/i,
  /面积[：:]\s*([\d.,]+\s*[㎡平方米m²M²]+)/i,
  /(\d+\.?\d*)\s*[㎡平方米m²M²]+/,
];

export const PRICE_PATTERNS = [
  /起拍价[：:]\s*[¥￥]?\s*([\d.,]+)\s*元?/i,
  /当前价[：:]\s*[¥￥]?\s*([\d.,]+)\s*元?/i,
  /成交价[：:]\s*[¥￥]?\s*([\d.,]+)\s*元?/i,
  /市场价[：:]\s*[¥￥]?\s*([\d.,]+)\s*元?/i,
  /评估价[：:]\s*[¥￥]?\s*([\d.,]+)\s*元?/i,
];
