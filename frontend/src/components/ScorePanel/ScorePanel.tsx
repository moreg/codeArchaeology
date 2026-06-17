import { memo } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { TotalScore } from './TotalScore';
import { RadarChart } from './RadarChart';
import { HotSpotList } from './HotSpotList';
import styles from './ScorePanel.module.css';

/**
 * ScorePanel — 屎山评分面板（Task 6）
 *
 * 包含 3 个子组件：
 *   1. TotalScore     — 综合评分大数字
 *   2. RadarChart     — 五维度雷达
 *   3. HotSpotList    — Top 10 热点
 *
 * 顶部 Tab (Detail / Score) + 关闭按钮，与 DetailPanel 共享设计语言
 */

function ScorePanelInner() {
  const scoreData = useAppStore((s) => s.scoreData);
  const activeTab = useAppStore((s) => s.activeTab);
  const setActiveTab = useAppStore((s) => s.setActiveTab);
  const setRightCollapsed = useAppStore((s) => s.setRightCollapsed);

  const handleHotSpotClick = (nodeId: string) => {
    // 热点点击：切到 detail tab
    // 实际 UniverseMap 也会监听来自右侧的导航事件（后续 Task 4/5 集成）
    setActiveTab('detail');
    // 保留 nodeId 用于未来扩展（DetailPanel 可通过 store.selectedNode 决定）
    void nodeId;
  };

  return (
    <div className={styles.panel}>
      {/* 顶部金色渐变条 */}
      <div className={styles.goldBar} aria-hidden />

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
          aria-label="关闭评分面板"
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
        {!scoreData ? (
          <ScoreSkeleton />
        ) : (
          <>
            <TotalScore scoreData={scoreData} />
            <RadarChart dimensions={scoreData.dimensions} />
            <HotSpotList
              hotSpots={scoreData.hot_spots}
              onHotSpotClick={handleHotSpotClick}
            />
          </>
        )}
      </div>
    </div>
  );
}

function ScoreSkeleton() {
  return (
    <div className={styles.skeletonWrap}>
      <div className={`${styles.skHeader} skeleton`} />
      <div className={`${styles.skChart} skeleton`} />
      <div className={`${styles.skList} skeleton`} />
    </div>
  );
}

export const ScorePanel = memo(ScorePanelInner);
export default ScorePanel;