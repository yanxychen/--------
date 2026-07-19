export const EARTH_RADIUS = 6371000;

export const DEFAULT_DISTANCE_MULTIPLIER = 1.8;

export const AMAP_GEOCODE_URL = 'https://restapi.amap.com/v3/geocode/geo';
export const AMAP_DRIVING_URL = 'https://restapi.amap.com/v3/direction/driving';

export const KEYWORD_LEVELS = {
  FULL_COMMUNITY: 'fullCommunity',
  COMMUNITY: 'community',
  BUSINESS: 'business',
  DISTRICT: 'district',
  CITY: 'city',
} as const;

export const ADDRESS_SUFFIXES = {
  COMMUNITY: ['花园', '小区', '苑', '府', '邸', '城', '庭', '家园', '佳园', '名苑', '豪庭', '公馆', '公寓'],
  DISTRICT: ['区', '县', '市'],
  TOWN: ['街道', '镇', '乡'],
  BUILDING: ['栋', '座', '号楼', '室', '号'],
  ROAD: ['路', '街', '道', '巷', '大道'],
};
