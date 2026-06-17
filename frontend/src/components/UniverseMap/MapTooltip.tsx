import { useEffect, useState } from 'react';
import type { GraphNode } from '@/types';
import { formatDate, getComplexityRating } from '@/utils/colorMode';
import styles from './MapTooltip.module.css';

export interface MapTooltipProps {
  node: GraphNode | null;
  x: number;
  y: number;
}

export function MapTooltip({ node, x, y }: MapTooltipProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!node) {
      const t = setTimeout(() => setVisible(false), 200);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setVisible(true), 200);
    return () => clearTimeout(t);
  }, [node]);

  if (!visible || !node) return null;

  const rating = getComplexityRating(node.complexity);
  const chipCls = `${styles.chip} ${styles[rating.grade === 'S' || rating.grade === 'A' ? 'healthy' : rating.grade === 'B' ? 'warning' : rating.grade === 'C' ? 'danger' : 'extreme']}`;

  const offsetX = 14;
  const offsetY = 14;

  return (
    <div
      className={styles.tooltip}
      style={{ left: x + offsetX, top: y + offsetY }}
      role="tooltip"
    >
      <div className={styles.name}>
        {node.level === 'function' ? 'ƒ ' : node.level === 'module' ? '◆ ' : '◉ '}
        {node.name}
      </div>
      <div className={styles.path}>{node.file_path}</div>

      <div className={styles.row}>
        <span className={styles.label}>圈复杂度</span>
        <span className={styles.value}>
          {node.complexity}
          <span className={chipCls} style={{ marginLeft: 6 }}>
            {rating.grade} · {rating.label}
          </span>
        </span>
      </div>

      <div className={styles.row}>
        <span className={styles.label}>代码行数</span>
        <span className={styles.value}>{node.line_count}</span>
      </div>

      <div className={styles.row}>
        <span className={styles.label}>作者</span>
        <span className={styles.value}>{node.author}</span>
      </div>

      <div className={styles.row}>
        <span className={styles.label}>最后修改</span>
        <span className={styles.value}>{formatDate(node.last_modified ?? '')}</span>
      </div>

      <div className={styles.row}>
        <span className={styles.label}>测试覆盖</span>
        <span className={styles.value}>
          {node.test_coverage}%
          <div className={styles.coverageBar} style={{ display: 'inline-block', marginLeft: 6 }}>
            <div
              className={styles.coverageFill}
              style={{ width: `${node.test_coverage}%` }}
            />
          </div>
        </span>
      </div>
    </div>
  );
}
