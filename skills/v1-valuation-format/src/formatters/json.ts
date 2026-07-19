import { V1Output } from '../types';

export function toJson(output: V1Output, pretty: boolean = true): string {
    return pretty ? JSON.stringify(output, null, 2) : JSON.stringify(output);
}

export function toJsonCompact(output: V1Output): string {
    return JSON.stringify(output);
}