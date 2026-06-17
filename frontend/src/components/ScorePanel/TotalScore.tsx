import { memo, useCallback, useState } from 'react';
import type { ScoreData } from '@/types';
import { apiClient } from '@/api/client';
import { useAppStore } from '@/store/useAppStore';
import styles from './TotalScore.module.css';

/**
 * TotalScore — 综合评分大数字
 *
 * 与 mockData 契约对齐：
 * - ScoreData.total_score
 * - ScoreData.rating（字符串：例如 '屎山警告'）
 * - ScoreData.rating_color
 * - ScoreData.dimensions.{key} 是平铺的数字
 *
 * 不依赖 mockData 的旧字段 rating_label
 */

interface Props {
  scoreData: ScoreData;
}

function TotalScoreInner({ scoreData }: Props) {
  const setScoreData = useAppStore((s) => s.setScoreData);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  const handleRefresh = useCallback(
    async (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setRefreshing(true);
      setRefreshError(null);
      try {
        const data = await apiClient.getScore(scoreData.scan_id);
        setScoreData(data);
      } catch (err) {
        setRefreshError(err instanceof Error ? err.message : '刷新失败');
      } finally {
        setRefreshing(false);
      }
    },
    [scoreData.scan_id, setScoreData],
  );

  // 5 维度均值
  const dimNumbers = [
    scoreData.dimensions.complexity,
    scoreData.dimensions.duplication,
    scoreData.dimensions.comment,
    scoreData.dimensions.author_centrality,
    scoreData.dimensions.test_coverage,
  ];
  const avg = Math.round(dimNumbers.reduce((a, b) => a + b, 0) / dimNumbers.length);

  const totalColor = scoreData.rating_color || '#C9A96E';

  return (
    <section
      className={styles.section}
      style={{ borderTopColor: totalColor }}
      aria-label="综合评分"
    >
      <div className={styles.row}>
        <div className={styles.numberBlock}>
          <div
            className={styles.bigNumber}
            style={{
              color: totalColor,
              textShadow: `0 0 24px ${totalColor}55`,
            }}
            aria-label={`综合评分 ${scoreData.total_score} 分`}
          >
            {scoreData.total_score}
          </div>
          <div className={styles.subtitle}>综合屎山评分</div>
        </div>

        <div className={styles.metaBlock}>
          <div
            className={styles.ratingLabel}
            style={{
              backgroundColor: `${totalColor}22`,
              color: totalColor,
              borderColor: `${totalColor}55`,
            }}
          >
            {scoreData.rating}
          </div>
          <button
            className={`${styles.refreshBtn} ${refreshing ? styles.refreshing : ''}`}
            onClick={handleRefresh}
            aria-label="刷新评分"
            disabled={refreshing}
          >
            <span className={styles.refreshIcon} aria-hidden>
              ↻
            </span>
            <span>{refreshing ? '计算中…' : '刷新'}</span>
          </button>
          {refreshError && (
            <div className={styles.error}>⚠ {refreshError}</div>
          )}
        </div>
      </div>

      <div className={styles.dimHint}>
        五维度平均分：<strong style={{ color: totalColor }}>{avg}</strong> · 共 5
        个分析维度
      </div>
    </section>
  );
}

export const TotalScore = memo(TotalScoreInner);
export default TotalScore;