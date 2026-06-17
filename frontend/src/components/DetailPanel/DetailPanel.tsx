import { memo } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { OverviewSection } from './OverviewSection';
import { StorySection } from './StorySection';
import { GitTimeline } from './GitTimeline';
import { CodePreview } from './CodePreview';
import { RefactorSuggestion } from './RefactorSuggestion';
import styles from './DetailPanel.module.css';

/**
 * DetailPanel — 右侧详情面板（Task 5）
 *
 * 内容层级：
 *   顶部 Tab (Detail / Score) + 关闭按钮
 *   ┌─────────────┐
 *   │  Overview   │  概览（函数名/路径/指标/作者）
 *   │  Story      │  AI 故事（async）
 *   │  Timeline   │  Git 时间线（最近 5 commits）
 *   │  Code       │  Monaco 代码预览
 *   │  Refactor   │  重构建议（async）
 *   └─────────────┘
 *
 * 与父容器 ThreeColumnLayout 配合，通过 rightCollapsed 控制展开
 */

function DetailPanelInner() {
  const selectedNode = useAppStore((s) => s.selectedNode);
  const activeTab = useAppStore((s) => s.activeTab);
  const setActiveTab = useAppStore((s) => s.setActiveTab);
  const setRightCollapsed = useAppStore((s) => s.setRightCollapsed);

  // 空状态
  if (!selectedNode) {
    return (
      <div className={styles.empty} role="status">
        <div className={styles.emptyIcon} aria-hidden>
          ⬅
        </div>
        <div className={styles.emptyText}>
          点击左侧宇宙图中的节点查看详情
        </div>
        <button
          className={styles.scoreLink}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setActiveTab('score');
          }}
        >
          或查看「屎山评分」 →
        </button>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      {/* 顶部 Tab Bar */}
      <div className={styles.tabbar} role="tablist" aria-label="右侧面板视图">
        <button
          role="tab"
          aria-selected={activeTab === 'detail'}
          className={`${styles.tab} ${activeTab === 'detail' ? styles.tabActive : ''}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setActiveTab('detail');
          }}
        >
          详情
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'score'}
          className={`${styles.tab} ${activeTab === 'score' ? styles.tabActive : ''}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setActiveTab('score');
          }}
        >
          评分
        </button>
        <button
          className={styles.closeBtn}
          aria-label="关闭详情面板"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setRightCollapsed(true);
          }}
        >
          ✕
        </button>
      </div>

      {/* 内容区 */}
      <div className={styles.scroll}>
        <OverviewSection node={selectedNode} />
        <StorySection node={selectedNode} />
        <GitTimeline node={selectedNode} />
        <CodePreview node={selectedNode} />
        <RefactorSuggestion node={selectedNode} />
      </div>
    </div>
  );
}

export const DetailPanel = memo(DetailPanelInner);
export default DetailPanel;