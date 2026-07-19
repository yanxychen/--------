import type {
  MergeRequest,
  MergeResult,
  MergedCase,
  AuctionCase,
  AuctionHistoryItem,
  MergeLogEntry,
  MergerConfig,
} from './types';
import { DEFAULT_CONFIG, ROUND_PRIORITY } from './constants';
import { CaseGrouper } from './grouper';

export class CaseMerger {
  private config: MergerConfig;
  private grouper: CaseGrouper;

  constructor(config: Partial<MergerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.grouper = new CaseGrouper(
      this.config.addressSimilarityThreshold,
      this.config.areaTolerance
    );
  }

  merge(request: MergeRequest): MergeResult {
    const { cases } = request;

    const groups = this.grouper.group(cases);

    const mergedCases: MergedCase[] = [];
    const mergeLog: MergeLogEntry[] = [];
    let mergeCount = 0;

    groups.forEach((group, index) => {
      const groupId = `group_${index}`;
      const mainCase = this.selectMainCase(group);
      const history = this.buildHistory(group);

      const merged: MergedCase = {
        ...mainCase,
        auctionHistory: history,
        mergeGroupId: groupId,
      };

      mergedCases.push(merged);

      if (group.length > 1) {
        mergeCount++;
        mergeLog.push({
          groupId,
          groupKey: mainCase.fullAddress,
          caseCount: group.length,
          caseIds: group.map(c => c.itemId),
          mainCaseId: mainCase.itemId,
          rounds: [...new Set(group.map(c => c.auctionRound))],
        });
      }
    });

    return {
      mergedCases,
      mergeCount,
      mergeLog,
    };
  }

  private selectMainCase(group: AuctionCase[]): AuctionCase {
    if (group.length === 1) {
      return group[0];
    }

    const sorted = [...group].sort((a, b) => {
      const roundA = ROUND_PRIORITY[a.auctionRound] || 0;
      const roundB = ROUND_PRIORITY[b.auctionRound] || 0;

      if (roundB !== roundA) {
        return roundB - roundA;
      }

      const timeA = this.parseTime(a.auctionTime);
      const timeB = this.parseTime(b.auctionTime);
      return timeB - timeA;
    });

    const taobaoCase = sorted.find(c => c.platform === 'taobao');
    return taobaoCase || sorted[0];
  }

  private buildHistory(group: AuctionCase[]): AuctionHistoryItem[] {
    return group
      .map(c => ({
        itemId: c.itemId,
        platform: c.platform,
        round: c.auctionRound,
        price: c.startPrice,
        time: c.auctionTime,
        status: c.auctionStatus,
        detailUrl: c.detailUrl,
      }))
      .sort((a, b) => {
        const roundA = ROUND_PRIORITY[a.round] || 0;
        const roundB = ROUND_PRIORITY[b.round] || 0;

        if (roundB !== roundA) {
          return roundB - roundA;
        }

        return this.parseTime(b.time) - this.parseTime(a.time);
      });
  }

  private parseTime(timeStr: string): number {
    if (!timeStr) return 0;

    const match = timeStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
    if (match) {
      return new Date(
        parseInt(match[1]),
        parseInt(match[2]) - 1,
        parseInt(match[3])
      ).getTime();
    }

    return 0;
  }
}

export {
  type MergeRequest,
  type MergeResult,
  type MergedCase,
  type AuctionCase,
  type AuctionHistoryItem,
  type MergeLogEntry,
  type MergerConfig,
};
