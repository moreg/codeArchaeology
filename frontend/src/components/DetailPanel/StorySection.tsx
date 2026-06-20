import { memo, useEffect, useRef, useState } from 'react';
import DOMPurify from 'dompurify';
import type { GraphNode, StoryData } from '@/types';
import { apiClient } from '@/api/client';
import { useAppStore } from '@/store/useAppStore';
import { avatarGradient, initial, stopAll } from '@/utils/helpers';
import { GitTimeline } from './GitTimeline';
import styles from './StorySection.module.css';

/**
 * StorySection — 老员工故事会（本项目的灵魂功能）
 *
 * 与后端契约对齐：
 * - StoryData.narrative 是 HTML 字符串（含 <code class="hl|danger|code"> 标签）
 * - StoryData.timeline 是 GitCommit[]
 * - StoryData.author 可选（向后兼容新字段）
 *
 * 数据流：
 * - 通过 apiClient.getStory(scanId, nodeId) 异步加载
 * - 缓存到本地 ref（避免 React StrictMode 双调用）
 * - 加载失败 / Mock 模式自动降级
 */

interface Props {
  node: GraphNode;
}

function StorySkeleton() {
  return (
    <div className={styles.skeleton}>
      <div className={`${styles.skeletonRow} skeleton`} style={{ width: '40%' }} />
      <div className={`${styles.skeletonRow} skeleton`} style={{ width: '90%' }} />
      <div className={`${styles.skeletonRow} skeleton`} style={{ width: '75%' }} />
    </div>
  );
}

function NarrativeHtml({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['code', 'span', 'strong', 'em', 'b', 'i', 'br', 'p'],
    ALLOWED_ATTR: ['class'],
  });
  return (
    <div
      className={styles.narrative}
      dangerouslySetInnerHTML={{ __html: sanitized }}
    />
  );
}

function StorySectionInner({ node }: Props) {
  const [story, setStory] = useState<StoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const lastNodeIdRef = useRef<string | null>(null);

  const scanId = useAppStore((s) => s.scanId) ?? 'demo-scan';

  useEffect(() => {
    // 同节点不重复请求
    if (lastNodeIdRef.current === node.id) return;
    lastNodeIdRef.current = node.id;

    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await apiClient.getStory(scanId, node.id);
        if (cancelled) return;
        setStory(data);
      } catch (err) {
        if (cancelled) return;
        const msg = err instanceof Error ? err.message : '未知错误';
        setError(msg);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [node.id, scanId]);

  const authorName = story?.author?.name ?? node.author ?? 'Unknown';
  const authorRole = story?.author?.role ?? '前任开发者';
  const avatarBg = avatarGradient(authorName);

  return (
    <section className={styles.section} aria-label="老员工故事会">
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div
            className={styles.avatar}
            style={{ background: avatarBg }}
            aria-label={`${authorName} 头像`}
          >
            {initial(authorName)}
          </div>
          <div className={styles.headerInfo}>
            <div className={styles.authorName}>{authorName}</div>
            <div className={styles.authorRole}>{authorRole}</div>
          </div>
        </div>
        <span className={styles.aiBadge} aria-label="由 AI 生成">
          ✨ AI 生成
        </span>
      </header>

      {loading && <StorySkeleton />}

      {!loading && error && (
        <div className={styles.errorBox} role="alert" onClick={stopAll}>
          ⚠ 加载失败：{error}
        </div>
      )}

      {!loading && !error && story && (
        <>
          {/* 故事摘要 */}
          <p className={styles.summary}>{story.summary}</p>

          {/* 演进时间线（嵌入式） */}
          <div className={styles.timelineLabel}>演进时间线</div>
          <GitTimeline commits={story.timeline} compact />

          {/* AI 叙述 */}
          <div className={styles.narrativeLabel}>AI 叙述</div>
          {story.narrative ? (
            <NarrativeHtml html={story.narrative} />
          ) : (
            <div className={styles.empty}>暂无叙述文本</div>
          )}

          {/* 降级提示（model 字段以 mock 开头即认为降级） */}
          {story.model?.startsWith('mock') && (
            <div className={styles.degraded}>
              ⚠ 无法考证：该项目未启用 git 或 AI 服务未配置
            </div>
          )}
        </>
      )}
    </section>
  );
}

export const StorySection = memo(StorySectionInner);
export default StorySection;