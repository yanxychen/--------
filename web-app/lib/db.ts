import sqlite3 from 'sqlite3';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { mkdirSync, existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const getDbPath = (): string => {
    const envPath = process.env.DATABASE_PATH;
    if (envPath) {
        if (envPath.startsWith('/')) {
            return envPath;
        }
        return join(process.cwd(), envPath);
    }
    return join(process.cwd(), 'data', 'example.sqlite');
};

const DB_PATH = getDbPath();

const ensureDataDir = () => {
    const dbDir = dirname(DB_PATH);
    if (!existsSync(dbDir)) {
        mkdirSync(dbDir, { recursive: true });
    }
};

ensureDataDir();

let db: sqlite3.Database | null = null;

export function getDB(): sqlite3.Database {
    if (!db) {
        db = new sqlite3.Database(DB_PATH, (err) => {
            if (err) {
                console.error('数据库连接失败:', err.message);
            } else {
                console.log('数据库连接成功');
            }
        });

        db.serialize(() => {
            db!.run(`
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT NOT NULL,
                    property_type TEXT NOT NULL,
                    area REAL,
                    total_cases INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            `);

            db!.run(`
                CREATE TABLE IF NOT EXISTS case_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address_key TEXT NOT NULL,
                    reference_location TEXT,
                    building_area REAL,
                    market_value REAL,
                    unit_price REAL,
                    source_url TEXT,
                    remark TEXT,
                    price_type TEXT,
                    auction_records TEXT,
                    data_json TEXT,
                    expires_at INTEGER NOT NULL
                );
            `);

            db!.run(`
                CREATE TABLE IF NOT EXISTS user_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            `);

            db!.run(`CREATE INDEX IF NOT EXISTS idx_case_cache_address ON case_cache(address_key);`);
            db!.run(`CREATE INDEX IF NOT EXISTS idx_case_cache_expires ON case_cache(expires_at);`);
        });
    }
    return db;
}

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

export function addSearchHistory(address: string, propertyType: string, area: number | null, totalCases: number): Promise<void> {
    return new Promise((resolve, reject) => {
        const db = getDB();
        db.run(
            'INSERT INTO search_history (address, property_type, area, total_cases) VALUES (?, ?, ?, ?)',
            [address, propertyType, area, totalCases],
            (err) => {
                if (err) reject(err);
                else resolve();
            }
        );
    });
}

export function getSearchHistory(limit: number = 10): Promise<SearchHistory[]> {
    return new Promise((resolve, reject) => {
        const db = getDB();
        db.all(
            'SELECT id, address, property_type as propertyType, area, total_cases as totalCases, created_at as createdAt FROM search_history ORDER BY created_at DESC LIMIT ?',
            [limit],
            (err, rows) => {
                if (err) reject(err);
                else resolve(rows as SearchHistory[]);
            }
        );
    });
}

export function getCachedCases(addressKey: string): Promise<CaseCache[]> {
    return new Promise((resolve, reject) => {
        const now = Math.floor(Date.now() / 1000);
        const db = getDB();
        db.all(
            'SELECT id, address_key as addressKey, reference_location as referenceLocation, building_area as buildingArea, market_value as marketValue, unit_price as unitPrice, source_url as sourceUrl, remark, price_type as priceType, auction_records as auctionRecords, data_json as dataJson, expires_at as expiresAt FROM case_cache WHERE address_key = ? AND expires_at > ?',
            [addressKey, now],
            (err, rows) => {
                if (err) reject(err);
                else resolve(rows as CaseCache[]);
            }
        );
    });
}

export function cacheCases(addressKey: string, cases: any[]): Promise<void> {
    return new Promise((resolve, reject) => {
        const db = getDB();
        const ttl = parseInt(process.env.CACHE_TTL || '86400');
        const expiresAt = Math.floor(Date.now() / 1000) + ttl;

        db.serialize(() => {
            db.run('DELETE FROM case_cache WHERE address_key = ?', [addressKey], (err) => {
                if (err) {
                    reject(err);
                    return;
                }

                const stmt = db.prepare(
                    'INSERT INTO case_cache (address_key, reference_location, building_area, market_value, unit_price, source_url, remark, price_type, auction_records, data_json, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                );

                cases.forEach(c => {
                    stmt.run(
                        addressKey,
                        c.referenceLocation,
                        c.buildingArea,
                        c.marketValue,
                        c.unitPrice,
                        c.source,
                        c.remark,
                        c.priceType,
                        JSON.stringify(c.auctionRecords || []),
                        JSON.stringify(c),
                        expiresAt
                    );
                });

                stmt.finalize((err) => {
                    if (err) reject(err);
                    else resolve();
                });
            });
        });
    });
}

export function cleanupExpiredCache(): Promise<void> {
    return new Promise((resolve, reject) => {
        const now = Math.floor(Date.now() / 1000);
        const db = getDB();
        db.run('DELETE FROM case_cache WHERE expires_at <= ?', [now], (err) => {
            if (err) reject(err);
            else resolve();
        });
    });
}

export function getConfig(key: string): Promise<string | null> {
    return new Promise((resolve, reject) => {
        const db = getDB();
        db.get('SELECT value FROM user_config WHERE key = ?', [key], (err, row: { value: string } | undefined) => {
            if (err) reject(err);
            else resolve(row ? row.value : null);
        });
    });
}

export function setConfig(key: string, value: string): Promise<void> {
    return new Promise((resolve, reject) => {
        const db = getDB();
        db.run(
            'INSERT OR REPLACE INTO user_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            [key, value],
            (err) => {
                if (err) reject(err);
                else resolve();
            }
        );
    });
}