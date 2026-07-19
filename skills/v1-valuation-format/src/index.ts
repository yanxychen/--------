import { V1Output, FormatOptions, FormatOutput, FormatFromScoredInput } from './types';
import { V1FormatConverter, convertToV1, convertFromScored } from './converter';
import { validateV1Format, validateV1Case, assertV1Format, ValidationResult } from './validator';
import { toMarkdown } from './formatters/markdown';
import { toJson, toJsonCompact } from './formatters/json';
import { toHtml } from './formatters/html';
import { toExcelData, toExcelAOA } from './formatters/excel';
import {
    V1_HEADERS,
    FORMAT_VERSION,
    V1_COLUMN_COUNT,
    V1_FORMAT_CONTRACT,
} from './constants';

export * from './types';
export {
    V1_HEADERS,
    FORMAT_VERSION,
    V1_COLUMN_COUNT,
    V1_FORMAT_CONTRACT,
    V1FormatConverter,
    convertToV1,
    convertFromScored,
    validateV1Format,
    validateV1Case,
    assertV1Format,
    toMarkdown,
    toJson,
    toJsonCompact,
    toHtml,
    toExcelData,
    toExcelAOA,
};

export const v1Format = {
    version: FORMAT_VERSION,
    headers: [...V1_HEADERS],
    columnCount: V1_COLUMN_COUNT,

    convert(cases: any[], options?: FormatOptions): V1Output {
        return convertToV1(cases, options);
    },

    convertFromScored(input: FormatFromScoredInput): V1Output {
        return convertFromScored(input);
    },

    validate(output: V1Output): ValidationResult {
        return validateV1Format(output);
    },

    assert(output: V1Output): void {
        assertV1Format(output);
    },

    format(cases: any[], options?: FormatOptions): FormatOutput {
        const output = convertToV1(cases, options);
        assertV1Format(output);

        const formatType = options?.output || 'markdown';

        switch (formatType) {
            case 'markdown':
                return toMarkdown(output, options);
            case 'json':
                return toJson(output);
            case 'html':
                return toHtml(output, options as any);
            case 'excel':
                return toExcelAOA(output, options) as unknown as FormatOutput;
            default:
                return output;
        }
    },

    formatFromScored(input: FormatFromScoredInput): FormatOutput {
        const output = convertFromScored(input);
        assertV1Format(output);

        const formatType = input.options?.output || 'markdown';

        switch (formatType) {
            case 'markdown':
                return toMarkdown(output, input.options);
            case 'json':
                return toJson(output);
            case 'html':
                return toHtml(output, input.options as any);
            case 'excel':
                return toExcelAOA(output, input.options) as unknown as FormatOutput;
            default:
                return output;
        }
    },

    toMarkdown,
    toJson,
    toJsonCompact,
    toHtml,
    toExcelData,
    toExcelAOA,
};

export default v1Format;