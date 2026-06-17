import { memo, useMemo } from 'react';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from 'chart.js';
import type { ScoreData } from '@/types';
import styles from './RadarChart.module.css';

// 注册 Chart.js 组件
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
);

const DIMENSION_LABEL: Record<keyof ScoreData['dimensions'], string> = {
  complexity: '圈复杂度',
  duplication: '重复代码率',
  comment: '注释覆盖率',
  author_centrality: '作者集中度',
  test_coverage: '测试覆盖率',
};

type DimKey = keyof ScoreData['dimensions'];

interface Props {
  dimensions: ScoreData['dimensions'];
}

function RadarChartInner({ dimensions }: Props) {
  const dimKeys: DimKey[] = useMemo(
    () => [
      'complexity',
      'duplication',
      'comment',
      'author_centrality',
      'test_coverage',
    ],
    [],
  );

  const labels = useMemo(
    () => dimKeys.map((k) => DIMENSION_LABEL[k]),
    [dimKeys],
  );

  const data: ChartData<'radar', number[], string> = useMemo(
    () => ({
      labels,
      datasets: [
        {
          label: '得分',
          data: dimKeys.map((k) => dimensions[k]),
          backgroundColor: 'rgba(201, 169, 110, 0.18)',
          borderColor: '#C9A96E',
          borderWidth: 2,
          pointBackgroundColor: '#E8B84B',
          pointBorderColor: '#060A14',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
        },
      ],
    }),
    [dimensions, dimKeys, labels],
  );

  const options: ChartOptions<'radar'> = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1A1F2E',
          titleColor: '#C9A96E',
          bodyColor: '#F5F0E8',
          borderColor: 'rgba(201, 169, 110, 0.4)',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 6,
          displayColors: false,
          callbacks: {
            label: (ctx) => `得分：${ctx.parsed.r}`,
          },
        },
      },
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: {
            stepSize: 25,
            color: 'rgba(201, 169, 110, 0.5)',
            backdropColor: 'transparent',
            font: { size: 10 },
          },
          grid: {
            color: 'rgba(201, 169, 110, 0.15)',
            lineWidth: 1,
          },
          angleLines: {
            color: 'rgba(201, 169, 110, 0.2)',
            lineWidth: 1,
          },
          pointLabels: {
            color: '#C9A96E',
            font: {
              family:
                'DM Sans, -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif',
              size: 12,
              weight: 500,
            },
            padding: 12,
          },
        },
      },
    }),
    [],
  );

  return (
    <section className={styles.section} aria-label="五维度雷达图">
      <h3 className={styles.title}>五维度评分雷达</h3>

      <div className={styles.chartWrap}>
        <Radar data={data} options={options} aria-label="五维度雷达图" />
      </div>

      {/* 维度数据列表（屏幕阅读器 + 直观展示） */}
      <ul className={styles.dimList} aria-label="五维度详细得分">
        {dimKeys.map((k) => (
          <li key={k} className={styles.dimItem}>
            <div className={styles.dimLabel}>{DIMENSION_LABEL[k]}</div>
            <div className={styles.dimBarWrap}>
              <div
                className={styles.dimBar}
                style={{ width: `${dimensions[k]}%` }}
                aria-hidden
              />
            </div>
            <div className={styles.dimValue}>
              <strong>{dimensions[k]}</strong>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export const RadarChart = memo(RadarChartInner);
export default RadarChart;