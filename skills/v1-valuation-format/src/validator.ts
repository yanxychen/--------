import { V1Output, V1Case, V1_COLUMN_COUNT } from './types';
import { V1_HEADERS, FORMAT_VERSION } from './constants';

export interface ValidationResult {
    valid: boolean;
    errors: string[];
    warnings: string[];
}

export function validateV1Format(output: V1Output): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (output.formatVersion !== FORMAT_VERSION) {
        errors.push(`版本号不匹配: 期望 ${FORMAT_VERSION}, 实际 ${output.formatVersion}`);
    }

    if (!Array.isArray(output.headers)) {
        errors.push('headers 必须是数组');
    } else if (output.headers.length !== V1_COLUMN_COUNT) {
        errors.push(`列数不匹配: 期望 ${V1_COLUMN_COUNT} 列, 实际 ${output.headers.length} 列`);
    } else {
        V1_HEADERS.forEach((header, index) => {
            if (output.headers[index] !== header) {
                errors.push(`第 ${index + 1} 列名不匹配: 期望 "${header}", 实际 "${output.headers[index]}"`);
            }
        });
    }

    if (!Array.isArray(output.data)) {
        errors.push('data 必须是数组');
    } else {
        output.data.forEach((item, index) => {
            const itemErrors = validateV1Case(item, index);
            errors.push(...itemErrors);
        });
    }

    if (output.total !== output.data?.length) {
        warnings.push(`total 与 data.length 不一致: total=${output.total}, length=${output.data?.length}`);
    }

    return {
        valid: errors.length === 0,
        errors,
        warnings,
    };
}

export function validateV1Case(item: V1Case, index: number = 0): string[] {
    const errors: string[] = [];
    const prefix = `第 ${index + 1} 条数据`;

    if (!item || typeof item !== 'object') {
        errors.push(`${prefix}: 不是有效的对象`);
        return errors;
    }

    const requiredFields: (keyof V1Case)[] = [
        'referenceLocation',
        'landArea',
        'buildingArea',
        'marketValue',
        'unitPrice',
        'source',
        'remark',
        'priceType',
    ];

    requiredFields.forEach((field) => {
        if (!(field in item)) {
            errors.push(`${prefix}: 缺少必填字段 "${field}"`);
        }
    });

    if (typeof item.referenceLocation !== 'string') {
        errors.push(`${prefix}: referenceLocation 必须是字符串`);
    } else if (!item.referenceLocation) {
        errors.push(`${prefix}: referenceLocation 不能为空`);
    }

    if (typeof item.landArea !== 'string') {
        errors.push(`${prefix}: landArea 必须是字符串`);
    }

    if (typeof item.buildingArea !== 'number' || isNaN(item.buildingArea)) {
        errors.push(`${prefix}: buildingArea 必须是数字`);
    } else if (item.buildingArea < 0) {
        errors.push(`${prefix}: buildingArea 不能为负数`);
    }

    if (typeof item.marketValue !== 'number' || isNaN(item.marketValue)) {
        errors.push(`${prefix}: marketValue 必须是数字`);
    } else if (item.marketValue < 0) {
        errors.push(`${prefix}: marketValue 不能为负数`);
    }

    if (typeof item.unitPrice !== 'number' || isNaN(item.unitPrice)) {
        errors.push(`${prefix}: unitPrice 必须是数字`);
    }

    if (typeof item.source !== 'string') {
        errors.push(`${prefix}: source 必须是字符串`);
    }

    if (typeof item.remark !== 'string') {
        errors.push(`${prefix}: remark 必须是字符串`);
    }

    if (typeof item.priceType !== 'string') {
        errors.push(`${prefix}: priceType 必须是字符串`);
    }

    return errors;
}

export function assertV1Format(output: V1Output): void {
    const result = validateV1Format(output);
    if (!result.valid) {
        throw new Error(`V1格式校验失败:\n${result.errors.join('\n')}`);
    }
}