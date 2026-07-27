'use client';

function safeFormatNumber(value: number | string | undefined | null, decimals: number = 2): string {
    if (value === undefined || value === null) return '-';
    if (typeof value === 'string') return value;
    if (isNaN(value) || !isFinite(value)) return '-';
    if (value === 0) return '-';
    return value.toFixed(decimals);
}

export async function exportToExcel(cases: any[], selectedIds: Set<string>, filename: string = '抵押物估值案例') {
    // 动态导入 xlsx（浏览器端）
    const XLSX = await import('xlsx');

    const selected = cases.filter(c => selectedIds.has(c.id));

    if (selected.length === 0) {
        alert('请先勾选要导出的案例');
        return;
    }

    const header = [
        '参照物位置',
        '土地面积 (m²)',
        '建筑面积 (m²)',
        '市场价值(万元)',
        '建筑单价(元/m²)',
        '数据来源',
        '备注',
        '价格类型',
    ];

    const rows = selected.map(c => [
        c.referenceLocation || '',
        c.landArea || '-',
        safeFormatNumber(c.buildingArea),
        safeFormatNumber(c.marketValue),
        safeFormatNumber(c.unitPrice),
        c.source || c.link || '',
        c.remark || '',
        c.priceType || '普通司法拍卖',
    ]);

    const wsData = [header, ...rows];
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    ws['!cols'] = [
        { wch: 60 }, { wch: 15 }, { wch: 15 },
        { wch: 15 }, { wch: 18 }, { wch: 40 },
        { wch: 80 }, { wch: 15 },
    ];

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '估值案例');

    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'binary' });

    // 转 Blob 并下载
    const buf = new ArrayBuffer(wbout.length);
    const view = new Uint8Array(buf);
    for (let i = 0; i < wbout.length; i++) view[i] = wbout.charCodeAt(i) & 0xFF;

    const blob = new Blob([buf], { type: 'application/octet-stream' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    a.download = `${filename}_${timestamp}.xlsx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}
