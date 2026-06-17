import { memo } from 'react';
import type { GitCommit, GraphNode } from '@/types';
import { copyToClipboard, relativeTime, stopAll } from '@/utils/helpers';
import styles from './GitTimeline.module.css';

/**
 * GitTimeline — Git 提交垂直时间线
 *
 * 支持两种模式：
 * - 独立模式（直接传 commits）
 * - 节点模式（从 GraphNode 提取 last_modified + last_commit_hash，回退显示）
 *
 * compact=true 时为嵌入式（无外边距/标题）
 */

interface Props {
  commits?: GitCommit[];
  node?: GraphNode;
  compact?: boolean;
}

function GitTimelineInner({ commits, node, compact }: Props) {
  // 若未传 commits，则用 node 上的 last_modified + last_commit_hash 兜底
  const items: GitCommit[] =
    commits ??
    (node?.last_modified
      ? [
          {
            commit_hash: node.last_commit_hash ?? node.id ?? '',
            date: node.last_modified,
            author: node.author ?? 'Unknown',
            message: `${node.name} · ${node.file_path}`,
          },
        ]
      : []);

  const display = items.slice(0, 5);

  if (!compact) {
    return (
      <section className={styles.section} aria-label="Git 提交时间线">
        <h3 className={styles.title}>Git 时间线 · 最近 5 次提交</h3>
        <TimelineBody commits={display} />
      </section>
    );
  }

  return <TimelineBody commits={display} />;
}

function TimelineBody({ commits }: { commits: GitCommit[] }) {
  if (commits.length === 0) {
    return (
      <div className={styles.empty}>
        📭 暂无 Git 提交记录（项目未启用 git 或文件未提交）
      </div>
    );
  }

  return (
    <div className={styles.timeline}>
      {commits.map((c, idx) => (
        <TimelineItem
          key={`${c.commit_hash}-${idx}`}
          commit={c}
          isLast={idx === commits.length - 1}
        />
      ))}
    </div>
  );
}

function TimelineItem({
  commit,
  isLast,
}: {
  commit: GitCommit;
  isLast: boolean;
}) {
  const handleCopy = async (e: React.MouseEvent) => {
    stopAll(e);
    await copyToClipboard(commit.commit_hash);
  };

  const shortHash = commit.commit_hash.slice(0, 8);

  return (
    <div className={styles.item}>
      <div className={styles.left}>
        <div className={styles.dot} aria-hidden />
        {!isLast && <div className={styles.line} aria-hidden />}
      </div>
      <div className={styles.right}>
        <div className={styles.row1}>
          <button
            className={styles.hash}
            onClick={handleCopy}
            onMouseDown={stopAll}
            aria-label={`复制 commit hash ${shortHash}`}
          >
            {shortHash}
          </button>
          <span className={styles.date}>{relativeTime(commit.date)}</span>
        </div>
        <div className={styles.message} title={commit.message}>
          {commit.message}
        </div>
        <div className={styles.meta}>
          <span className={styles.author}>👤 {commit.author}</span>
        </div>
      </div>
    </div>
  );
}

export const GitTimeline = memo(GitTimelineInner);
export default GitTimeline;