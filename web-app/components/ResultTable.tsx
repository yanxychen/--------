'use client';

import { useState, useMemo } from 'react';
import { ExternalLink, Download, ChevronLeft, ChevronRight, FileSpreadsheet, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import type { Case } from '@/lib/searchService';

interface ResultTableProps {
    top3Cases: Case[];
    allCases: Case[];
    searchAddress: string;
    searchPropertyType: string;
    onBack: () => void;
    isExporting: boolean;
    onExport: () => void;
    selfAuctionCount?: number;
    totalCount?: number;
}

const tableHeaders = [
        '参照物位置',
        '土地面积 (㎡)',
        '建筑面积 (㎡)',
        '市场价值(万元)',
        '建筑单价(元/㎡)',
        '数据来源',
        '距离(km)',
        '备注',
        '价格类型',
    ];

type SortKey = 'score' | 'buildingArea' | 'startDate' | 'distanceKm' | 'unitPrice';
type SortOrder = 'asc' | 'desc';

export default function ResultTable({
    top3Cases,
    allCases,
    searchAddress,
    searchPropertyType,
    onBack,
    isExporting,
    onExport,
    selfAuctionCount = 0,
    totalCount = 0,
}: ResultTableProps) {
    const [sortKey, setSortKey] = useState<SortKey>('startDate');
    const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
    const [currentPage, setCurrentPage] = useState(1);
    const pageSize = 10;

    const propertyTypeLabels: Record<string, string> = {
        commercial: '商业',
        residential: '住宅',
        other: '其他',
    };

    const formatNumber = (num: number | string | null | undefined, decimals: number = 2): string => {
        if (num === null || num === undefined || num === '') return '-';
        const n = typeof num === 'string' ? parseFloat(num.replace(/,/g, '')) : num;
        if (isNaN(n) || !isFinite(n)) return '-';
        return n.toLocaleString('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        });
    };

    const sortedAllCases = useMemo(() => {
        const cases = [...allCases];
        cases.sort((a, b) => {
            let valA: number = 0;
            let valB: number = 0;

            switch (sortKey) {
                case 'score':
                    valA = a.score || 0;
                    valB = b.score || 0;
                    break;
                case 'buildingArea':
                    valA = a.buildingAreaValue || a.buildingArea || 0;
                    valB = b.buildingAreaValue || b.buildingArea || 0;
                    break;
                case 'startDate':
                    valA = a.startDate ? new Date(a.startDate).getTime() : 0;
                    valB = b.startDate ? new Date(b.startDate).getTime() : 0;
                    break;
                case 'distanceKm':
                    valA = a.distanceKm || 9999;
                    valB = b.distanceKm || 9999;
                    break;
                case 'unitPrice':
                    valA = a.unitPrice || 0;
                    valB = b.unitPrice || 0;
                    break;
            }

            if (sortOrder === 'asc') {
                return valA - valB;
            } else {
                return valB - valA;
            }
        });
        return cases;
    }, [allCases, sortKey, sortOrder]);

    const totalPages = Math.ceil(sortedAllCases.length / pageSize);
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const pagedCases = sortedAllCases.slice(startIndex, endIndex);

    const handleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortKey(key);
            setSortOrder('desc');
        }
    };

    const SortIcon = ({ active, order }: { active: boolean; order: SortOrder }) => {
        if (!active) return <ArrowUpDown className="w-3 h-3 ml-1 opacity-50" />;
        return order === 'asc' 
            ? <ArrowUp className="w-3 h-3 ml-1" />
            : <ArrowDown className="w-3 h-3 ml-1" />;
    };

    const renderTableRow = (item: Case, showIndex?: number) => (
        <tr
            key={item.id}
            className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                item.isSelfAuction ? 'bg-amber-50' : ''
            }`}
        >
            <td className="px-4 py-3 text-sm align-top min-w-[200px] max-w-[400px]">
                <div className="whitespace-pre-wrap break-all">{item.referenceLocation}</div>
                {item.isSelfAuction && (
                    <span className="inline-block ml-2 px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
                        抵押物自身
                    </span>
                )}
            </td>
            <td className="px-4 py-3 text-sm text-gray-600 align-top">
                {item.landArea}
            </td>
            <td className="px-4 py-3 text-sm font-medium align-top">
                {formatNumber(item.buildingArea)}
            </td>
            <td className="px-4 py-3 text-sm font-medium align-top">
                {formatNumber(item.marketValue)}
            </td>
            <td className={`px-4 py-3 text-sm font-medium align-top ${
                item.priceAnomaly === 'high' || item.priceAnomaly === 'low'
                    ? 'bg-yellow-200 font-bold'
                    : ''
            }`}>
                {formatNumber(item.unitPrice)}
                {item.priceAnomaly === 'high' && (
                    <span className="block text-xs text-red-600">⚠️ 偏高</span>
                )}
                {item.priceAnomaly === 'low' && (
                    <span className="block text-xs text-blue-600">⚠️ 偏低</span>
                )}
            </td>
            <td className="px-4 py-3 align-top">
                {(() => {
                    const link = item.link || (item as any).source || '';
                    if (link) {
                        return (
                            <a
                                href={link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary-600 hover:text-primary-700 text-xs break-all underline underline-offset-2 cursor-pointer hover:bg-primary-50 rounded px-1 py-0.5 inline-flex items-center gap-1"
                            >
                                查看详情
                                <ExternalLink className="w-3 h-3 flex-shrink-0" />
                            </a>
                        );
                    }
                    return <span className="text-gray-600 text-xs">无链接</span>;
                })()}
            </td>
            <td className="px-4 py-3 text-sm text-gray-600 align-top whitespace-nowrap">
                {item.distanceKm !== undefined && item.distanceKm !== null ? (
                    <span>{item.distanceKm.toFixed(1)} km</span>
                ) : (
                    '-'
                )}
            </td>
            <td className="px-4 py-3 text-sm text-gray-600 align-top max-w-xs">
                <div className="whitespace-pre-line">{item.remark}</div>
            </td>
            <td className="px-4 py-3 text-sm align-top">
                {item.priceType}
            </td>
        </tr>
    );

    return (
        <div className="w-full space-y-8">
            {/* 顶部操作栏 */}
            <div className="flex items-center justify-between">
                <button
                    onClick={onBack}
                    className="flex items-center gap-2 text-gray-600 hover:text-primary-600 transition-colors"
                >
                    <ChevronLeft className="w-5 h-5" />
                    返回搜索
                </button>

                <button
                    onClick={onExport}
                    disabled={isExporting || allCases.length === 0}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                        isExporting || allCases.length === 0
                            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            : 'bg-gold-500 text-white hover:bg-gold-600'
                    }`}
                >
                    {isExporting ? (
                        <>
                            <Download className="w-4 h-4" />
                            导出中...
                        </>
                    ) : (
                        <>
                            <FileSpreadsheet className="w-4 h-4" />
                            导出Excel
                        </>
                    )}
                </button>
            </div>

            {/* 搜索信息 */}
            <div className="flex flex-wrap gap-3">
                <span className="px-4 py-2 bg-gray-100 rounded-full text-sm font-medium text-gray-700">
                    搜索地址：{searchAddress}
                </span>
                <span className="px-4 py-2 bg-gray-100 rounded-full text-sm font-medium text-gray-700">
                    物业类型：{propertyTypeLabels[searchPropertyType] || searchPropertyType}
                </span>
                <span className="px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
                    共 {totalCount} 个案例
                </span>
                {selfAuctionCount > 0 && (
                    <span className="px-4 py-2 bg-amber-100 text-amber-700 rounded-full text-sm font-medium">
                        抵押物自身拍卖：{selfAuctionCount} 个
                    </span>
                )}
            </div>

            {/* Top3 精选案例 */}
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-primary-600 to-primary-500 text-white">
                    <h2 className="text-lg font-bold flex items-center gap-2">
                        ⭐ 精选案例（Top 3）
                        <span className="text-sm font-normal opacity-80">按评分排序，最具参考价值</span>
                    </h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-primary-50">
                            <tr>
                                {tableHeaders.map((header) => (
                                    <th
                                        key={header}
                                        className="px-4 py-3 text-left text-sm font-semibold text-primary-800"
                                    >
                                        {header}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {top3Cases.length > 0 ? (
                                top3Cases.map((item, index) => renderTableRow(item, index + 1))
                            ) : (
                                <tr>
                                    <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                                        暂无精选案例
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 全部案例 */}
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-gray-800">
                            📋 全部案例
                            <span className="text-sm font-normal text-gray-500 ml-2">
                                共 {sortedAllCases.length} 个
                            </span>
                        </h2>
                        <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-500">排序：</span>
                            <button
                                onClick={() => handleSort('startDate')}
                                className={`px-3 py-1 rounded-lg flex items-center transition-colors ${
                                    sortKey === 'startDate'
                                        ? 'bg-primary-100 text-primary-700 font-medium'
                                        : 'text-gray-600 hover:bg-gray-100'
                                }`}
                            >
                                时间
                                <SortIcon active={sortKey === 'startDate'} order={sortOrder} />
                            </button>
                            <button
                                onClick={() => handleSort('score')}
                                className={`px-3 py-1 rounded-lg flex items-center transition-colors ${
                                    sortKey === 'score'
                                        ? 'bg-primary-100 text-primary-700 font-medium'
                                        : 'text-gray-600 hover:bg-gray-100'
                                }`}
                            >
                                评分
                                <SortIcon active={sortKey === 'score'} order={sortOrder} />
                            </button>
                            <button
                                onClick={() => handleSort('distanceKm')}
                                className={`px-3 py-1 rounded-lg flex items-center transition-colors ${
                                    sortKey === 'distanceKm'
                                        ? 'bg-primary-100 text-primary-700 font-medium'
                                        : 'text-gray-600 hover:bg-gray-100'
                                }`}
                            >
                                距离
                                <SortIcon active={sortKey === 'distanceKm'} order={sortOrder} />
                            </button>
                            <button
                                onClick={() => handleSort('buildingArea')}
                                className={`px-3 py-1 rounded-lg flex items-center transition-colors ${
                                    sortKey === 'buildingArea'
                                        ? 'bg-primary-100 text-primary-700 font-medium'
                                        : 'text-gray-600 hover:bg-gray-100'
                                }`}
                            >
                                面积
                                <SortIcon active={sortKey === 'buildingArea'} order={sortOrder} />
                            </button>
                            <button
                                onClick={() => handleSort('unitPrice')}
                                className={`px-3 py-1 rounded-lg flex items-center transition-colors ${
                                    sortKey === 'unitPrice'
                                        ? 'bg-primary-100 text-primary-700 font-medium'
                                        : 'text-gray-600 hover:bg-gray-100'
                                }`}
                            >
                                单价
                                <SortIcon active={sortKey === 'unitPrice'} order={sortOrder} />
                            </button>
                        </div>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-100">
                            <tr>
                                {tableHeaders.map((header) => (
                                    <th
                                        key={header}
                                        className="px-4 py-3 text-left text-sm font-semibold text-gray-700"
                                    >
                                        {header}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {pagedCases.length > 0 ? (
                                pagedCases.map((item, index) => renderTableRow(item, startIndex + index + 1))
                            ) : (
                                <tr>
                                    <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                                        暂无案例
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {totalPages > 1 && (
                    <div className="flex items-center justify-center gap-2 px-4 py-4 bg-gray-50">
                        <button
                            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                            disabled={currentPage === 1}
                            className="p-2 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </button>
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                            <button
                                key={page}
                                onClick={() => setCurrentPage(page)}
                                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                                    page === currentPage
                                        ? 'bg-primary-600 text-white'
                                        : 'text-gray-600 hover:bg-gray-200'
                                }`}
                            >
                                {page}
                            </button>
                        ))}
                        <button
                            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                            disabled={currentPage === totalPages}
                            className="p-2 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
