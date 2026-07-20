// Vercel-compatible stub for db.ts
// sqlite3 (native C++ module) is not supported on Vercel serverless.
// Since the real data comes from the Python backend API, caching is optional.
// This stub provides the same interface with no-op implementations.

export interface SearchHistory {
    id: number;
    address: string;
    propertyType: string;
    area: number | null;
    totalCases: number;
    createdAt: string;
}

export interface CaseCache {
    id: number;
    addressKey: string;
    referenceLocation: string;
    buildingArea: number;
    marketValue: number;
    unitPrice: number;
    sourceUrl: string;
    remark: string;
    priceType: string;
    auctionRecords: string;
    dataJson: string;
    expiresAt: number;
}

export async function addSearchHistory(
    _address: string,
    _propertyType: string,
    _area: number | null,
    _totalCases: number
): Promise<void> {
    // No-op on Vercel — search history is not persisted
}

export async function getSearchHistory(_limit: number = 10): Promise<SearchHistory[]> {
    return [];
}

export async function getCachedCases(_addressKey: string): Promise<CaseCache[]> {
    // Always return empty so searchService hits the Python API every time
    return [];
}

export async function cacheCases(_addressKey: string, _cases: any[]): Promise<void> {
    // No-op — results are not cached on Vercel
}

export async function cleanupExpiredCache(): Promise<void> {
    // No-op
}

export async function getConfig(_key: string): Promise<string | null> {
    return null;
}

export async function setConfig(_key: string, _value: string): Promise<void> {
    // No-op
}
