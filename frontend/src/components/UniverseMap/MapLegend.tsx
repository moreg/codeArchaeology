import type { ColorMode } from '@/types';
import styles from './MapLegend.module.css';

interface LegendRow {
  color: string;
  label: string;
}

const COMPLEXITY_ROWS: LegendRow[] = [
  { color: '#4CAF50', label: 'S 优秀 (≤5)' },
  { color: '#8BC34A', label: 'A 良好 (6-10)' },
  { color: '#FFC107', label: 'B 一般 (11-20)' },
  { color: '#FF9800', label: 'C 警告 (21-30)' },
  { color: '#F44336', label: 'D 危险 (>30)' },
];

const FREQUENCY_ROWS: LegendRow[] = [
  { color: '#3B82F6', label: '最近修改' },
  { color: '#1D4ED8', label: '中期' },
  { color: '#1E3A8A', label: '冷代码' },
];

const COVERAGE_ROWS: LegendRow[] = [
  { color: '#10B981', label: '有测试覆盖' },
  { color: '#EF4444', label: '无测试覆盖' },
];

const SHAPE_ROWS = [
  { label: '文件 (ellipse)', color: '#C9A96E' },
  { label: '模块 (hexagon)', color: '#E8B84B' },
  { label: '函数 (round-rect)', color: '#9CA3AF' },
];

export interface MapLegendProps {
  colorMode: ColorMode;
}

export function MapLegend({ colorMode }: MapLegendProps) {
  let rows: LegendRow[] = COMPLEXITY_ROWS;
  let title = '圈复杂度';

  if (colorMode === 'frequency') {
    rows = FREQUENCY_ROWS;
    title = '修改频率';
  } else if (colorMode === 'test_coverage') {
    rows = COVERAGE_ROWS;
    title = '测试覆盖';
  } else if (colorMode === 'author') {
    title = '作者分布';
  }

  return (
    <div className={styles.legend} aria-label="图例">
      <div className={styles.title}>{title}</div>
      {colorMode === 'author' ? (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>每个作者用 hash 分配唯一色相</div>
          <div className={styles.row}>
            <span className={styles.swatch} style={{ background: '#C9A96E' }} />
            <span>张师兄</span>
          </div>
          <div className={styles.row}>
            <span className={styles.swatch} style={{ background: '#10B981' }} />
            <span>李四</span>
          </div>
          <div className={styles.row}>
            <span className={styles.swatch} style={{ background: '#3B82F6' }} />
            <span>王五</span>
          </div>
        </div>
      ) : (
        <div className={styles.section}>
          {rows.map((r) => (
            <div key={r.label} className={styles.row}>
              <span className={styles.swatch} style={{ background: r.color }} />
              <span>{r.label}</span>
            </div>
          ))}
        </div>
      )}

      <div className={styles.title} style={{ marginTop: 10 }}>节点形状</div>
      <div className={styles.section}>
        {SHAPE_ROWS.map((s) => (
          <div key={s.label} className={styles.row}>
            <span className={styles.shape} style={{ color: s.color }}>●</span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
