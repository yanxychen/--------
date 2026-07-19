import type {
  FilterRequest,
  FilterResult,
  FilterCase,
  PropertyType,
  FilterLogEntry,
} from './types';
import { DEFAULT_CONFIG } from './constants';
import { TypeFilter } from './type-filter';
import { RelaxEngine } from './relax-engine';

export class CaseFilter {
  private config = DEFAULT_CONFIG;
  private typeFilter: TypeFilter;
  private relaxEngine: RelaxEngine;

  constructor() {
    this.typeFilter = new TypeFilter();
    this.relaxEngine = new RelaxEngine();
  }

  filter(request: FilterRequest): FilterResult {
    const {
      cases,
      propertyType,
      assetType,
      selfAuctionItemIds = [],
      minCases = this.config.minCases,
      mode = 'fine',
    } = request;

    const filterLog: FilterLogEntry[] = [];

    const typeResult = this.typeFilter.filter(cases, assetType);
    filterLog.push({
      step: 'type_filter',
      distanceLevel: -1,
      timeLevel: -1,
      distanceThreshold: 0,
      timeThreshold: 0,
      beforeCount: cases.length,
      afterCount: typeResult.passed.length,
      filteredCount: typeResult.filtered.length,
    });

    const relaxResult = this.relaxEngine.relax(
      typeResult.passed,
      propertyType as PropertyType,
      minCases,
      mode,
      selfAuctionItemIds
    );

    return {
      filteredCases: relaxResult.filteredCases,
      filterLog: [...filterLog, ...relaxResult.filterLog],
      usedDistanceThreshold: relaxResult.usedDistanceThreshold,
      usedTimeThreshold: relaxResult.usedTimeThreshold,
      distanceLevel: relaxResult.distanceLevel,
      timeLevel: relaxResult.timeLevel,
    };
  }

  roughFilter(request: Omit<FilterRequest, 'mode'>): FilterResult {
    return this.filter({ ...request, mode: 'rough' });
  }

  fineFilter(request: Omit<FilterRequest, 'mode'>): FilterResult {
    return this.filter({ ...request, mode: 'fine' });
  }
}

export {
  type FilterRequest,
  type FilterResult,
  type FilterCase,
  type PropertyType,
  type FilterLogEntry,
};
