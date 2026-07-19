import { V1_HEADERS, FORMAT_VERSION, FieldMapping } from './types';

export { V1_HEADERS, FORMAT_VERSION };

export const DEFAULT_NUMBER_PRECISION = 2;

export const DEFAULT_LAND_AREA = '不适用';

export const DEFAULT_PRICE_TYPE = '普通司法拍卖';

export const SELF_AUCTION_PRICE_TYPE = '抵押物自身拍卖';

export const SELF_AUCTION_PREFIX = '【自身拍卖】';

export const NO_DATA_PLACEHOLDER = '-';

export const DEFAULT_FIELD_MAPPING: FieldMapping = {
    referenceLocation: 'fullAddress',
    landArea: 'landArea',
    buildingArea: 'buildingArea',
    marketValue: 'marketValue',
    unitPrice: 'unitPrice',
    source: 'sourceUrl',
    remark: 'remark',
    priceType: 'priceType',
    auctionRecords: 'auctionRecords',
    drivingDistance: 'drivingDistance',
    straightDistance: 'straightDistance',
    auctionTime: 'auctionTime',
    auctionRound: 'auctionRound',
    auctionStatus: 'auctionStatus',
};

export const COLUMN_WIDTHS = {
    referenceLocation: 60,
    landArea: 15,
    buildingArea: 15,
    marketValue: 15,
    unitPrice: 18,
    source: 50,
    remark: 80,
    priceType: 15,
};

export const ROUND_ORDER = ['一拍', '二拍', '变卖'];

export const V1_FORMAT_CONTRACT = {
    columnCount: 8,
    columnOrder: V1_HEADERS,
    version: FORMAT_VERSION,
    rules: {
        buildingArea: '保留2位小数，单位㎡，无则填"-"',
        marketValue: '保留2位小数，单位万元，取最新拍卖价，无则填"-"',
        unitPrice: '保留2位小数，= 市场价值(万元) × 10000 ÷ 建筑面积(㎡)',
        landArea: '无则填"不适用"',
        source: '完整URL，可点击跳转',
        remark: '多轮拍卖记录 + 距离信息',
    },
};