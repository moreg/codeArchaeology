import { memo, useCallback } from 'react';
import type { HotSpot, HotSpotSeverity } from '@/types';
import { basename, stopAll } from '@/utils/helpers';
import styles from './HotSpotList.module.css';

/**
 * HotSpotList — Top 10 热点列表
 *
 * 与 mockData 契约对齐：
 * - HotSpot.severity: 'extreme' | 'high' | 'medium' | 'low'
 * - HotSpot.node_id 是可选字段（mockData 没有，DetailPanel 用 file_path + function_name 推断）
 */

interface Props {
  hotSpots: HotSpot[];
  onHotSpotClick: (nodeId: string) => void;
}

function rankColor(rank: number): { bg: string; fg: string } {
  if (rank === 1) return { bg: 'rgba(244, 67, 54, 0.2)', fg: '#F44336' };
  if (rank <= 3) return { bg: 'rgba(255, 152, 0, 0.2)', fg: '#FF9800' };
  if (rank <= 6) return { bg: 'rgba(255, 193, 7, 0.2)', fg: '#FFC107' };
  return { bg: 'rgba(76, 175, 80, 0.2)', fg: '#4CAF50' };
}

const SEVERITY_LABEL: Record<HotSpotSeverity, string> = {
  extreme: '紧急',
  high: '高',
  medium: '中',
  low: '低',
};

function HotSpotItemInner({
  spot,
  onClick,
}: {
  spot: HotSpot;
  onClick: (id: string) => void;
}) {
  const rc = rankColor(spot.rank);
  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      stopAll(e);
      // node_id 可能为空，回退用 file_path + function_name 拼接伪 ID
      const id = spot.node_id ?? `${spot.file_path}::${spot.function_name}`;
      onClick(id);
    },
    [onClick, spot.node_id, spot.file_path, spot.function_name],
  );

  return (
    <li
      className={styles.item}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`热点 ${spot.rank}: ${spot.function_name}（${spot.file_path}）`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          stopAll(e);
          const id = spot.node_id ?? `${spot.file_path}::${spot.function_name}`;
          onClick(id);
        }
      }}
    >
      <div
        className={styles.severityBar}
        style={{ backgroundColor: spot.severity_color }}
        aria-hidden
      />
      <div
        className={styles.rank}
        style={{ backgroundColor: rc.bg, color: rc.fg }}
      >
        {spot.rank}
      </div>
      <div className={styles.body}>
        <div className={styles.fileLine}>
          <span className={styles.fileName} title={spot.file_path}>
            📄 {basename(spot.file_path)}
          </span>
          <span className={styles.severityChip}>
            {SEVERITY_LABEL[spot.severity]}
          </span>
        </div>
        <div className={styles.funcName}>{spot.function_name}</div>
        <div className={styles.suggestion}>{spot.suggestion}</div>
        <div className={styles.metaLine}>
          <span className={styles.ccBadge}>
            <span className={styles.ccLabel}>CC</span>
            <span className={styles.ccValue}>{spot.complexity}</span>
          </span>
          <span className={styles.pathHint} title={spot.file_path}>
            {spot.file_path}
          </span>
        </div>
      </div>
    </li>
  );
}

const HotSpotItem = memo(HotSpotItemInner);

function HotSpotListInner({ hotSpots, onHotSpotClick }: Props) {
  const top10 = hotSpots.slice(0, 10);

  if (top10.length === 0) {
    return (
      <section className={styles.section} aria-label="热点列表">
        <header className={styles.header}>
          <h3 className={styles.title}>热点 Top 10</h3>
          <span className={styles.count}>0</span>
        </header>
        <div className={styles.empty}>暂无热点 🎉</div>
      </section>
    );
  }

  return (
    <section className={styles.section} aria-label="热点列表">
      <header className={styles.header}>
        <h3 className={styles.title}>热点 Top 10（按严重程度排序）</h3>
        <span className={styles.count}>{top10.length}</span>
      </header>

      <ul className={styles.list}>
        {top10.map((spot) => (
          <HotSpotItem
            key={`${spot.rank}-${spot.file_path}-${spot.function_name}`}
            spot={spot}
            onClick={onHotSpotClick}
          />
        ))}
      </ul>
    </section>
  );
}

export const HotSpotList = memo(HotSpotListInner);
export default HotSpotList;