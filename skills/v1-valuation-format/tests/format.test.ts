import { v1Format, convertToV1, validateV1Format, FORMAT_VERSION, V1_HEADERS, V1_COLUMN_COUNT } from '../src';

const MOCK_CASES = [
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
    },
];

describe('V1格式校验', () => {
    test('版本号正确', () => {
        expect(FORMAT_VERSION).toBe('v1.0.0');
    });

    test('列数为8列', () => {
        expect(V1_COLUMN_COUNT).toBe(8);
        expect(V1_HEADERS.length).toBe(8);
    });

    test('列名顺序正确', () => {
        expect(V1_HEADERS[0]).toBe('参照物位置');
        expect(V1_HEADERS[1]).toBe('土地面积 (㎡)');
        expect(V1_HEADERS[2]).toBe('建筑面积 (㎡)');
        expect(V1_HEADERS[3]).toBe('市场价值(万元)');
        expect(V1_HEADERS[4]).toBe('建筑单价(元/㎡)');
        expect(V1_HEADERS[5]).toBe('数据来源');
        expect(V1_HEADERS[6]).toBe('备注');
        expect(V1_HEADERS[7]).toBe('价格类型');
    });
});

describe('格式转换', () => {
    test('正确转换数据结构', () => {
        const result = convertToV1(MOCK_CASES);
        expect(result.formatVersion).toBe(FORMAT_VERSION);
        expect(result.headers.length).toBe(8);
        expect(result.data.length).toBe(2);
        expect(result.total).toBe(2);
    });

    test('建筑单价自动计算', () => {
        const cases = [
            {
                referenceLocation: '测试',
                buildingArea: 100,
                marketValue: 50,
            },
        ];
        const result = convertToV1(cases as any);
        expect(result.data[0].unitPrice).toBe(5000);
    });

    test('缺省值正确填充', () => {
        const cases = [{}];
        const result = convertToV1(cases as any);
        expect(result.data[0].landArea).toBe('不适用');
        expect(result.data[0].priceType).toBe('普通司法拍卖');
        expect(result.data[0].buildingArea).toBe(0);
    });
});

describe('校验器', () => {
    test('正确数据通过校验', () => {
        const result = convertToV1(MOCK_CASES);
        const validation = validateV1Format(result);
        expect(validation.valid).toBe(true);
        expect(validation.errors.length).toBe(0);
    });

    test('列数错误被捕获', () => {
        const result = convertToV1(MOCK_CASES);
        const badResult = { ...result, headers: result.headers.slice(0, 7) };
        const validation = validateV1Format(badResult);
        expect(validation.valid).toBe(false);
        expect(validation.errors.length).toBeGreaterThan(0);
    });

    test('缺少字段被捕获', () => {
        const badData = [{ wrongField: 'test' }];
        const result = convertToV1(MOCK_CASES);
        const badResult = { ...result, data: badData as any };
        const validation = validateV1Format(badResult);
        expect(validation.valid).toBe(false);
    });
});

describe('输出格式', () => {
    const result = convertToV1(MOCK_CASES);

    test('Markdown输出正确', () => {
        const markdown = v1Format.toMarkdown(result);
        expect(markdown).toContain('参照物位置');
        expect(markdown).toContain('数据来源');
        expect(markdown).toContain('---');
    });

    test('JSON输出正确', () => {
        const json = v1Format.toJson(result);
        const parsed = JSON.parse(json);
        expect(parsed.formatVersion).toBe(FORMAT_VERSION);
        expect(parsed.data.length).toBe(2);
    });

    test('Excel AOA输出正确', () => {
        const aoa = v1Format.toExcelAOA(result);
        expect(aoa.length).toBe(3);
        expect(aoa[0][0]).toBe('参照物位置');
        expect(aoa[1][0]).toContain('商业用房');
    });
});