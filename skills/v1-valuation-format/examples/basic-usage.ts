import v1Format from '../src';

// 示例1：使用任意结构数据 + 字段映射
const rawCases = [
    {
        id: '1',
        title: '赤峰市红山区哈达街办事处昭乌达路东商业用房',
        area: 306.62,
        price: 919900,
        url: 'https://sf-item.taobao.com/sf_item/1064587700541.htm',
        note: '一拍流拍，二拍即将开始',
        type: '司法拍卖',
    },
];

const result = v1Format.format(rawCases, {
    output: 'markdown',
    fieldMapping: {
        referenceLocation: 'title',
        buildingArea: 'area',
        marketValue: 'price',
        source: 'url',
        remark: 'note',
        priceType: 'type',
    },
});

console.log('=== 示例1：任意结构数据 ===');
console.log(result);

const validated = v1Format.validate(result as any);
console.log('校验通过:', validated.valid);

// 示例2：使用评分后的案例数据（与 case-scoring Skill 衔接）
const scoredCases = [
    {
        itemId: 'case-001',
        platform: 'taobao' as const,
        title: 'XX小区3室2厅',
        fullAddress: '北京市朝阳区XX小区1号楼101室',
        buildingArea: 105,
        marketValue: 5000000,
        auctionTime: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
        auctionStatus: '已成交',
        auctionRound: '一拍',
        drivingDistance: 800,
        sourceUrl: 'https://zc-item.taobao.com/auction/item_detail.htm?itemId=case-001',
        totalScore: 85.5,
        distanceScore: 45,
        areaScore: 25,
        timeScore: 15.5,
        scoreBreakdown: {
            itemId: 'case-001',
            distanceScore: 45,
            areaScore: 25,
            timeScore: 15.5,
            totalScore: 85.5,
            distance: 800,
            areaDiffRatio: 0.05,
            daysAgo: 60,
        },
    },
];

const selfAuctionCases = [
    {
        itemId: 'self-001',
        platform: 'taobao' as const,
        title: 'YY花园2室1厅（抵押物自身）',
        fullAddress: '北京市朝阳区YY花园2号楼202室',
        buildingArea: 85,
        marketValue: 4200000,
        auctionTime: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        auctionStatus: '一拍中',
        auctionRound: '一拍',
        drivingDistance: 0,
        sourceUrl: 'https://zc-item.taobao.com/auction/item_detail.htm?itemId=self-001',
    },
];

console.log('\n=== 示例2：评分后案例（含自身拍卖） ===');
const scoredResult = v1Format.formatFromScored({
    scoredCases,
    selfAuctionCases,
    options: {
        output: 'markdown',
        selfAuctionFirst: true,
        showScore: true,
    },
});

console.log(scoredResult);

// 示例3：JSON格式输出
const jsonResult = v1Format.formatFromScored({
    scoredCases,
    selfAuctionCases,
    options: {
        output: 'json',
    },
});

console.log('\n=== 示例3：JSON格式输出 ===');
console.log(JSON.stringify(jsonResult, null, 2));