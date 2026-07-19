import type { FilterCase, PropertyType } from './types';

export class TypeFilter {
  filter(cases: FilterCase[], assetType: string): {
    passed: FilterCase[];
    filtered: FilterCase[];
  } {
    const passed: FilterCase[] = [];
    const filtered: FilterCase[] = [];

    for (const c of cases) {
      if (this.isTypeMatch(c, assetType)) {
        passed.push(c);
      } else {
        filtered.push(c);
      }
    }

    return { passed, filtered };
  }

  private isTypeMatch(caseItem: FilterCase, assetType: string): boolean {
    if (caseItem.matchedType && caseItem.matchedType === assetType) {
      return true;
    }

    const title = caseItem.title + caseItem.fullAddress;
    const typeKeywords = this.getTypeKeywords(assetType);

    for (const keyword of typeKeywords) {
      if (title.includes(keyword)) {
        return true;
      }
    }

    return false;
  }

  private getTypeKeywords(assetType: string): string[] {
    const keywords: Record<string, string[]> = {
      '住宅': ['住宅', '公寓', '别墅', '小区', '花园', '家园', '苑', '府', '邸', '城', '庭'],
      '商业': ['商业', '商铺', '门面', '店铺', '商场', '购物中心', '写字楼', '办公', '酒店', '宾馆'],
      '工业': ['工业', '厂房', '仓库', '厂区', '工业园', '产业园'],
      '土地': ['土地', '用地', '地块', '宗地'],
      '特殊资产': ['采矿权', '林权', '海域使用权'],
    };

    return keywords[assetType] || [];
  }
}
