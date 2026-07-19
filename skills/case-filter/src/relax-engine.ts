import type { FilterCase, FilterLogEntry, PropertyType } from './types';
import { DISTANCE_LEVELS, TIME_LEVELS } from './constants';
import { DistanceFilter } from './distance-filter';
import { TimeFilter } from './time-filter';

export class RelaxEngine {
  private distanceFilter: DistanceFilter;
  private timeFilter: TimeFilter;

  constructor() {
    this.distanceFilter = new DistanceFilter();
    this.timeFilter = new TimeFilter();
  }

  relax(
    cases: FilterCase[],
    propertyType: PropertyType,
    minCases: number,
    mode: 'rough' | 'fine',
    selfAuctionItemIds: string[]
  ): {
    filteredCases: FilterCase[];
    filterLog: FilterLogEntry[];
    usedDistanceThreshold: number;
    usedTimeThreshold: number;
    distanceLevel: number;
    timeLevel: number;
  } {
    const distanceLevels = DISTANCE_LEVELS[propertyType];
    const timeLevels = TIME_LEVELS;

    const filterLog: FilterLogEntry[] = [];
    let currentCases = [...cases];
    let distanceLevel = 0;
    let timeLevel = 0;

    while (distanceLevel < distanceLevels.length || timeLevel < timeLevels.length) {
      const distanceThreshold = distanceLevels[Math.min(distanceLevel, distanceLevels.length - 1)];
      const timeThreshold = timeLevels[Math.min(timeLevel, timeLevels.length - 1)];

      const beforeCount = currentCases.length;

      const distanceResult = this.distanceFilter.filter(
        currentCases,
        distanceThreshold,
        mode,
        selfAuctionItemIds
      );

      const timeResult = this.timeFilter.filter(
        distanceResult.passed,
        timeThreshold,
        selfAuctionItemIds
      );

      filterLog.push({
        step: `level_d${distanceLevel + 1}_t${timeLevel + 1}`,
        distanceLevel,
        timeLevel,
        distanceThreshold,
        timeThreshold,
        beforeCount,
        afterCount: timeResult.passed.length,
        filteredCount: beforeCount - timeResult.passed.length,
      });

      if (timeResult.passed.length >= minCases) {
        return {
          filteredCases: timeResult.passed,
          filterLog,
          usedDistanceThreshold: distanceThreshold,
          usedTimeThreshold: timeThreshold,
          distanceLevel,
          timeLevel,
        };
      }

      if (distanceLevel < distanceLevels.length - 1) {
        distanceLevel++;
      } else if (timeLevel < timeLevels.length - 1) {
        timeLevel++;
      } else {
        break;
      }
    }

    const finalDistanceThreshold = distanceLevels[distanceLevels.length - 1];
    const finalTimeThreshold = timeLevels[timeLevels.length - 1];

    const finalResult = this.distanceFilter.filter(
      cases,
      finalDistanceThreshold,
      mode,
      selfAuctionItemIds
    );

    const finalTimeResult = this.timeFilter.filter(
      finalResult.passed,
      finalTimeThreshold,
      selfAuctionItemIds
    );

    return {
      filteredCases: finalTimeResult.passed,
      filterLog,
      usedDistanceThreshold: finalDistanceThreshold,
      usedTimeThreshold: finalTimeThreshold,
      distanceLevel: distanceLevels.length - 1,
      timeLevel: timeLevels.length - 1,
    };
  }
}
