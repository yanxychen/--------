import { addSearchHistory, getCachedCases, cacheCases, cleanupExpiredCache } from './db';

export interface AuctionRecord {
    round: string;
    date: string;
    startPrice: number;
    endPrice: number;
    status: string;
}

export interface Case {
    id: string;
    referenceLocation: string;
    landArea: string;
    buildingArea: number;
    marketValue: number;
    unitPrice: number;
    source: string;
    sourceText?: string;
    remark: string;
    priceType: string;
    auctionRecords: AuctionRecord[];
    priceAnomaly?: 'high' | 'low' | null;
    isSelfAuction?: boolean;
    score?: number;
    distanceKm?: number;
    startDate?: string;
    buildingAreaValue?: number;
    link?: string;
}

export interface SearchRequest {
    address: string;
    propertyType: 'residential' | 'commercial' | 'other';
    area?: number;
}

export interface SearchResponse {
    success: boolean;
    message: string;
    data: Case[];
    total: number;
    cacheHit: boolean;
    top3?: Case[];
    allCases?: Case[];
    selfAuctionCount?: number;
    totalCount?: number;
}

const MOCK_CASES: Case[] = [
    {
        id: '1',
        referenceLocation: '1、商业用房-赤峰市红山区哈达街办事处昭乌达路东、哈达街路南印象红山城市广场-1-1-1407不动产一处',
        landArea: '不适用',
        buildingArea: 306.62,
        marketValue: 91.99,
        unitPrice: 3000.13,
        source: 'https://sf-item.taobao.com/sf_item/1064587700541.htm',
        remark: '一拍：2026年05月30日，起拍价：1,149,825元，状态：流拍\n二拍：2026年07月19日，起拍价：919,860元，状态：即将开始\n距离抵押物约0.8公里',
        priceType: '普通司法拍卖',
        auctionRecords: [
            { round: '一拍', date: '2026年05月30日', startPrice: 1149825, endPrice: 0, status: '流拍' },
            { round: '二拍', date: '2026年07月19日', startPrice: 919860, endPrice: 0, status: '即将开始' },
        ],
    },
    {
        id: '2',
        referenceLocation: '2、商业用房-赤峰市红山区站前街办事处昭乌达路东、万商大院院内赤峰万通商业广场1-288号商厅',
        landArea: '不适用',
        buildingArea: 74.39,
        marketValue: 25.29,
        unitPrice: 3399.65,
        source: 'https://sf-item.taobao.com/sf_item/1031160224444.htm',
        remark: '一拍：2026年01月30日，起拍价：316,158元，状态：流拍\n二拍：2026年04月02日，起拍价：252,926元，状态：流拍\n距离抵押物约1.5公里',
        priceType: '普通司法拍卖',
        auctionRecords: [
            { round: '一拍', date: '2026年01月30日', startPrice: 316158, endPrice: 0, status: '流拍' },
            { round: '二拍', date: '2026年04月02日', startPrice: 252926, endPrice: 0, status: '流拍' },
        ],
    },
    {
        id: '3',
        referenceLocation: '3、商业用房-赤峰市红山区站前办事处园林路南段东侧天诚综合楼1号1-5-05013不动产一处',
        landArea: '不适用',
        buildingArea: 124.84,
        marketValue: 90.02,
        unitPrice: 7210.83,
        source: 'https://sf-item.taobao.com/sf_item/1062594789829.htm',
        remark: '一拍：2026年05月25日，起拍价：1,125,246元，状态：流拍\n二拍：2026年07月15日，起拍价：900,197元，状态：即将开始\n距离抵押物约1.5公里',
        priceType: '普通司法拍卖',
        auctionRecords: [
            { round: '一拍', date: '2026年05月25日', startPrice: 1125246, endPrice: 0, status: '流拍' },
            { round: '二拍', date: '2026年07月15日', startPrice: 900197, endPrice: 0, status: '即将开始' },
        ],
    },
    {
        id: '4',
        referenceLocation: '4、商业用房-赤峰市红山区南新街办事处新华小区5号楼2011不动产一处',
        landArea: '不适用',
        buildingArea: 123.68,
        marketValue: 85.78,
        unitPrice: 6935.64,
        source: 'https://sf-item.taobao.com/sf_item/1062614287767.htm',
        remark: '一拍：2026年06月26日，起拍价：1,072,306元，状态：流拍\n二拍：2026年07月22日，起拍价：857,845元，状态：即将开始\n距离抵押物约2.5公里',
        priceType: '普通司法拍卖',
        auctionRecords: [
            { round: '一拍', date: '2026年06月26日', startPrice: 1072306, endPrice: 0, status: '流拍' },
            { round: '二拍', date: '2026年07月22日', startPrice: 857845, endPrice: 0, status: '即将开始' },
        ],
    },
];

function convertPythonCaseToCase(pythonCase: any, index: number): Case {
    const buildingArea = pythonCase['建筑面积(m²)'] && pythonCase['建筑面积(m²)'] !== '不适用' 
        ? parseFloat(String(pythonCase['建筑面积(m²)']).replace(/,/g, '')) 
        : 0;
    const marketValue = pythonCase['市场价值(万元)'] && pythonCase['市场价值(万元)'] !== '不适用'
        ? parseFloat(String(pythonCase['市场价值(万元)']).replace(/,/g, ''))
        : 0;
    const unitPrice = pythonCase['建筑单价(元/㎡)'] && pythonCase['建筑单价(元/㎡)'] !== '不适用'
        ? parseFloat(String(pythonCase['建筑单价(元/㎡)']).replace(/,/g, ''))
        : 0;
    
    // 兼容多种字段名，确保能拿到链接和显示文本
    let sourceLink = 
        pythonCase['数据来源_链接'] || 
        pythonCase['link'] || 
        pythonCase['source_url'] ||
        pythonCase['参照物位置_链接'] ||
        pythonCase['source_link'] ||
        pythonCase['source'] ||
        '';
    
    // 如果没有链接，但有 item_id，尝试生成淘宝链接
    if (!sourceLink && pythonCase['item_id']) {
        sourceLink = `https://sf-item.taobao.com/sf_item/${pythonCase['item_id']}.htm`;
    }
    
    let sourceText = 
        pythonCase['数据来源'] || 
        pythonCase['source_text'] ||
        pythonCase['address'] ||
        '';
    
    // 如果 sourceText 为空，从参照物位置里提取纯地址（去掉序号、类型前缀）
    if (!sourceText && pythonCase['参照物位置']) {
        const refLoc = String(pythonCase['参照物位置']);
        // 匹配 "1、商业用房-地址" 格式，提取地址部分
        const match = refLoc.match(/^[0-9]+、[^-]+-(.+)$/);
        if (match) {
            sourceText = match[1];
        } else {
            // 尝试去掉序号前缀
            const match2 = refLoc.match(/^[0-9]+、(.+)$/);
            if (match2) {
                sourceText = match2[1];
            } else {
                sourceText = refLoc;
            }
        }
    }
    
    // 如果还是空，用"查看详情"
    if (!sourceText) {
        sourceText = '查看详情';
    }
    
    return {
        id: String(index + 1),
        referenceLocation: pythonCase['参照物位置'] || '',
        landArea: pythonCase['土地面积(m²)'] || '不适用',
        buildingArea,
        marketValue,
        unitPrice,
        source: sourceLink,
        sourceText,
        remark: pythonCase['备注'] || '',
        priceType: pythonCase['价格类型'] || '普通司法拍卖',
        auctionRecords: [],
        priceAnomaly: pythonCase['price_anomaly'] || null,
        isSelfAuction: pythonCase['is_self_auction'] || false,
        score: pythonCase['score'] || 0,
        distanceKm: pythonCase['distance_km'] || pythonCase['distanceKm'],
        startDate: pythonCase['start_date'] || pythonCase['startDate'],
        buildingAreaValue: buildingArea,
        link: sourceLink,
    };
}

export async function searchCases(request: SearchRequest): Promise<SearchResponse> {
    await cleanupExpiredCache();
    
    const addressKey = `${request.address}-${request.propertyType}`;
    
    // 先尝试从缓存获取（调试阶段先禁用，确保每次都是最新数据）
    // const cached = await getCachedCases(addressKey);
    // if (cached.length > 0) {
    //     ...
    // }
    
    try {
        const PYTHON_API_URL = process.env.PYTHON_API_URL;
        if (PYTHON_API_URL) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 600000);
            
            try {
                const response = await fetch(PYTHON_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        address: request.address,
                        asset_type: request.propertyType === 'residential' ? '住宅' 
                            : request.propertyType === 'commercial' ? '商业' 
                            : '其他',
                        building_area: request.area,
                    }),
                    signal: controller.signal,
                });
                clearTimeout(timeoutId);
                
                if (response.ok) {
                    const result = await response.json();
                    if (result.status === 'success') {
                        const top3Data = result.top3 || result.cases || [];
                        const top3Cases = top3Data.map((c: any, i: number) => convertPythonCaseToCase(c, i));
                        
                        const allCasesData = result.all_cases || result.cases || [];
                        const allCases = allCasesData.map((c: any, i: number) => convertPythonCaseToCase(c, i));
                        
                        await cacheCases(addressKey, allCases);
                        await addSearchHistory(request.address, request.propertyType, request.area ?? null, allCases.length);
                        
                        return {
                            success: true,
                            message: '搜索成功',
                            data: top3Cases,
                            total: allCases.length,
                            cacheHit: false,
                            top3: top3Cases,
                            allCases,
                            selfAuctionCount: result.self_auction_count || 0,
                            totalCount: result.total_count || allCases.length,
                        };
                    }
                }
            } finally {
                clearTimeout(timeoutId);
            }
        }
        
        const filteredCases = MOCK_CASES.map((c, i) => ({
            ...c,
            id: String(i + 1),
            referenceLocation: `${i + 1}、商业用房-${request.address.slice(0, 20)}...`,
            remark: c.remark.replace(/距离抵押物约[\d.]+(公里|米)/, `距离抵押物约${(0.8 + i * 0.3).toFixed(1)}公里`),
        }));
        
        await cacheCases(addressKey, filteredCases);
        await addSearchHistory(request.address, request.propertyType, request.area ?? null, filteredCases.length);
        
        return {
            success: true,
            message: '搜索成功（演示数据）',
            data: filteredCases,
            total: filteredCases.length,
            cacheHit: false,
            top3: filteredCases.slice(0, 3),
            allCases: filteredCases,
            selfAuctionCount: 0,
            totalCount: filteredCases.length,
        };
    } catch (error) {
        console.error('搜索失败:', error);
        return {
            success: false,
            message: '搜索失败，请稍后重试',
            data: [],
            total: 0,
            cacheHit: false,
            top3: [],
            allCases: [],
            selfAuctionCount: 0,
            totalCount: 0,
        };
    }
}