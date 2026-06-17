import { memo, useEffect, useRef, useState } from 'react';
import type { GraphNode, RefactorData, RefactorPriority } from '@/types';
import { apiClient } from '@/api/client';
import { useAppStore } from '@/store/useAppStore';
import { stopAll } from '@/utils/helpers';
import styles from './RefactorSuggestion.module.css';

/**
 * RefactorSuggestion — 重构建议卡片
 *
 * 与 mockData 契约对齐：
 * - RefactorData.suggestion / .diff / .estimated_reduction 是字符串字段
 * - RefactorData.priority 是 'high' | 'medium' | 'low'
 * - RefactorData.title / .description / .steps 等是兼容字段（可选）
 *
 * 数据流：
 * - 通过 apiClient.getRefactor(scanId, nodeId) 异步加载
 * - 用 localStorage 缓存「已应用」状态（避免 store 扩展）
 * - 失败自动降级到 mock
 */

interface Props {
  node: GraphNode;
}

const PRIORITY_LABEL: Record<RefactorPriority, string> = {
  high: '高优先级',
  medium: '中优先级',
  low: '低优先级',
};

const PRIORITY_COLOR: Record<RefactorPriority, string> = {
  high: '#F44336',
  medium: '#FFC107',
  low: '#4CAF50',
};

function RefactorSkeleton() {
  return (
    <div className={styles.skeleton}>
      <div className={`${styles.skRow} skeleton`} style={{ width: '50%' }} />
      <div className={`${styles.skRow} skeleton`} style={{ width: '90%' }} />
      <div className={`${styles.skRow} skeleton`} style={{ width: '75%' }} />
    </div>
  );
}

function RefactorSuggestionInner({ node }: Props) {
  const [data, setData] = useState<RefactorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const lastNodeIdRef = useRef<string | null>(null);

  const scanId = useAppStore((s) => s.scanId) ?? 'demo-scan';

  const appliedKey = `refactor-applied:${node.id}`;
  const [applied, setApplied] = useState<boolean>(() => {
    try {
      return window.localStorage.getItem(appliedKey) === 'true';
    } catch {
      return false;
    }
  });

  useEffect(() => {
    if (lastNodeIdRef.current === node.id) return;
    lastNodeIdRef.current = node.id;

    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const refactor = await apiClient.getRefactor(scanId, node.id);
        if (cancelled) return;
        setData(refactor);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : '未知错误');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [node.id, scanId]);

  const handleApply = (e: React.MouseEvent) => {
    stopAll(e);
    setApplied(true);
    try {
      window.localStorage.setItem(appliedKey, 'true');
    } catch {
      // ignore
    }
  };

  const toggleDiff = (e: React.MouseEvent) => {
    stopAll(e);
    setExpanded((v) => !v);
  };

  if (loading) {
    return (
      <section className={styles.section} aria-label="重构建议">
        <h3 className={styles.title}>重构建议</h3>
        <RefactorSkeleton />
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className={styles.section} aria-label="重构建议">
        <h3 className={styles.title}>重构建议</h3>
        <div className={styles.errorBox} role="alert">
          ⚠ 加载失败：{error ?? '无数据'}
        </div>
      </section>
    );
  }

  const priorityColor = PRIORITY_COLOR[data.priority];
  const titleText = data.title ?? `重构 ${node.name}`;
  const descriptionText = data.description ?? data.suggestion;
  const benefitText = data.expected_benefit ?? data.estimated_reduction;
  const diffText = data.diff_preview ?? data.diff;

  return (
    <section className={styles.section} aria-label="重构建议">
      <header className={styles.header}>
        <span
          className={styles.priorityChip}
          style={{
            backgroundColor: `${priorityColor}22`,
            color: priorityColor,
            borderColor: `${priorityColor}55`,
          }}
        >
          {PRIORITY_LABEL[data.priority]}
        </span>
        <h3 className={styles.heading}>{titleText}</h3>
      </header>

      {/* 左侧色条 */}
      <div
        className={styles.colorBar}
        style={{ backgroundColor: priorityColor }}
        aria-hidden
      />

      <p className={styles.description}>{descriptionText}</p>

      {/* 步骤（兼容旧字段） */}
      {data.steps && data.steps.length > 0 && (
        <div className={styles.stepsBlock}>
          <div className={styles.subLabel}>执行步骤</div>
          <ol className={styles.steps}>
            {data.steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </div>
      )}

      {/* 预计收益 */}
      {benefitText && (
        <div className={styles.benefitRow}>
          <span className={styles.benefitLabel}>预计收益</span>
          <span className={styles.benefitChip}>📈 {benefitText}</span>
        </div>
      )}

      {/* diff 预览（折叠） */}
      {diffText && (
        <div className={styles.diffBlock}>
          <button
            className={styles.diffToggle}
            onClick={toggleDiff}
            aria-expanded={expanded}
          >
            <span className={styles.diffArrow}>{expanded ? '▼' : '▶'}</span>
            <span>Diff 预览</span>
          </button>
          {expanded && (
            <pre className={styles.diffContent}>
              <code>{diffText}</code>
            </pre>
          )}
        </div>
      )}

      {/* 操作按钮 */}
      <div className={styles.actions}>
        <button
          className={`${styles.applyBtn} ${applied ? styles.applyBtnDone : ''}`}
          onClick={handleApply}
          disabled={applied}
          aria-label={applied ? '已标记为已应用' : '标记为已应用'}
        >
          {applied ? '✓ 已标记为已应用' : '标记为已应用'}
        </button>
        {data.generated_by === 'mock' && (
          <span className={styles.mockTag}>Mock 数据</span>
        )}
      </div>
    </section>
  );
}

// 局部辅助 hook 已移除

export const RefactorSuggestion = memo(RefactorSuggestionInner);
export default RefactorSuggestion;