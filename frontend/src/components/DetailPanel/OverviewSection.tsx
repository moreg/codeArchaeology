import { memo, useState, useCallback } from 'react';
import type { GraphNode } from '@/types';
import {
  RATING_COLOR,
  RATING_LABEL,
  avatarGradient,
  basename,
  copyToClipboard,
  initial,
  ratingFromComplexity,
  relativeTime,
  stopAll,
} from '@/utils/helpers';
import styles from './OverviewSection.module.css';

/**
 * OverviewSection — 概览区
 *
 * - 函数名（大字 24px mono + 沙金）
 * - 文件路径（点击复制，1.5s "✓ 已复制" tooltip）
 * - 三个 metric card：圈复杂度 / 代码行数 / 测试覆盖
 * - 作者头像 + 姓名 + 角色 chip
 * - 最后修改时间 + commit hash（点击复制）
 */

interface Props {
  node: GraphNode;
}

function CopyChip({
  value,
  label,
}: {
  value: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(
    async (e: React.MouseEvent) => {
      stopAll(e);
      const ok = await copyToClipboard(value);
      if (ok) {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }
    },
    [value],
  );

  return (
    <button
      className={styles.copyChip}
      onClick={handleCopy}
      onMouseDown={stopAll}
      aria-label={label ? `${label}：${value}` : `复制 ${value}`}
    >
      <span className={styles.copyValue}>{value}</span>
      <span
        className={`${styles.copyTooltip} ${copied ? styles.copyTooltipShow : ''}`}
        aria-live="polite"
      >
        {copied ? '✓ 已复制' : label ?? '点击复制'}
      </span>
    </button>
  );
}

function MetricCard({
  label,
  value,
  chip,
  chipColor,
}: {
  label: string;
  value: string | number;
  chip?: string;
  chipColor?: string;
}) {
  return (
    <div className={styles.metric}>
      <div className={styles.metricLabel}>{label}</div>
      <div className={styles.metricValue}>{value}</div>
      {chip && chipColor && (
        <span
          className={styles.metricChip}
          style={{
            backgroundColor: `${chipColor}22`,
            color: chipColor,
            borderColor: `${chipColor}55`,
          }}
        >
          {chip}
        </span>
      )}
    </div>
  );
}

function OverviewSectionInner({ node }: Props) {
  const rating = node.rating ?? ratingFromComplexity(node.complexity);
  const ratingColor = RATING_COLOR[rating];
  const coverage = node.test_coverage ?? 0;
  const coveragePct = Math.round(coverage * 100);

  const authorName = node.author ?? 'Unknown';
  const avatarBg = avatarGradient(authorName);
  const shortHash = (node.last_commit_hash ?? node.id ?? 'unknown').slice(0, 8);

  return (
    <section className={styles.section} aria-label="节点概览">
      {/* 函数名 */}
      <h2 className={styles.funcName}>{node.name}</h2>

      {/* 文件路径 */}
      <div className={styles.pathRow}>
        <span className={styles.pathIcon} aria-hidden>
          📄
        </span>
        <CopyChip value={node.file_path} label="复制文件路径" />
      </div>

      {/* 三个 metric card */}
      <div className={styles.metrics}>
        <MetricCard
          label="圈复杂度"
          value={node.complexity}
          chip={`${rating} · ${RATING_LABEL[rating]}`}
          chipColor={ratingColor}
        />
        <MetricCard
          label="代码行数"
          value={`${node.start_line}-${node.end_line}`}
        />
        <MetricCard
          label="测试覆盖"
          value={`${coveragePct}%`}
          chip={coveragePct > 0 ? `${coveragePct}%` : '无覆盖'}
          chipColor={coveragePct >= 60 ? '#4CAF50' : coveragePct >= 30 ? '#FFC107' : '#F44336'}
        />
      </div>

      {/* 作者行 */}
      <div className={styles.authorRow}>
        <div
          className={styles.avatar}
          style={{ background: avatarBg }}
          aria-label={`${authorName} 头像`}
        >
          {initial(authorName)}
        </div>
        <div className={styles.authorInfo}>
          <div className={styles.authorName}>{authorName}</div>
          <div className={styles.authorRole}>
            <span className={styles.roleChip}>前任开发者</span>
          </div>
        </div>
      </div>

      {/* 最后修改 + commit hash */}
      <div className={styles.modifiedRow}>
        <span className={styles.modifiedLabel}>最后修改</span>
        <span className={styles.modifiedTime}>
          {node.last_modified ? relativeTime(node.last_modified) : '—'}
        </span>
      </div>
      {node.last_commit_hash && (
        <div className={styles.hashRow}>
          <span className={styles.hashLabel}>commit</span>
          <CopyChip value={shortHash} label="复制 commit hash" />
        </div>
      )}

      {/* 文件 basename + 元信息 */}
      <div className={styles.metaRow}>
        <span className={styles.metaTag}>📁 {basename(node.file_path)}</span>
        <span className={styles.metaTag}>
          🌐 {node.language ?? 'unknown'}
        </span>
      </div>
    </section>
  );
}

export const OverviewSection = memo(OverviewSectionInner);
export default OverviewSection;