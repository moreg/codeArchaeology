import { useEffect, useRef } from 'react';
import { useAppStore } from '@/store/useAppStore';
import type { ColorMode, ViewLevel } from '@/types';
import { colorModeLabel, viewLevelLabel } from '@/utils/colorMode';
import styles from './TopBar.module.css';

const VIEW_LEVELS: ViewLevel[] = ['file', 'module', 'function'];
const COLOR_MODES: ColorMode[] = ['complexity', 'frequency', 'author', 'test_coverage'];

export interface TopBarProps {
  onExportPNG?: () => void;
}

export function TopBar({ onExportPNG }: TopBarProps) {
  const projectName = useAppStore((s) => s.projectName);
  const setProjectName = useAppStore((s) => s.setProjectName);
  const viewLevel = useAppStore((s) => s.viewLevel);
  const setViewLevel = useAppStore((s) => s.setViewLevel);
  const colorMode = useAppStore((s) => s.colorMode);
  const setColorMode = useAppStore((s) => s.setColorMode);
  const searchKeyword = useAppStore((s) => s.searchKeyword);
  const setSearchKeyword = useAppStore((s) => s.setSearchKeyword);
  const scoreData = useAppStore((s) => s.scoreData);
  const scanProgress = useAppStore((s) => s.scanProgress);
  const scanTotal = useAppStore((s) => s.scanTotal);
  const scanStatus = useAppStore((s) => s.scanStatus);

  const searchRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        searchRef.current?.focus();
        searchRef.current?.select();
      }
      if (e.key === 'Escape' && document.activeElement === searchRef.current) {
        setSearchKeyword('');
        searchRef.current?.blur();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [setSearchKeyword]);

  const handleSwitchProject = (): void => {
    const list = ['祖传 Python 爬虫', '未加载项目'];
    const current = projectName;
    const idx = list.indexOf(current);
    const next = list[(idx + 1) % list.length] ?? list[0];
    if (next) setProjectName(next);
  };

  const scoreColor = scoreData?.rating_color ?? 'var(--gold)';
  const scoreText = scoreData ? `${scoreData.total_score}` : '—';
  const ratingText = scoreData?.rating ?? '加载中';

  return (
    <header className={styles.topbar} role="banner">
      <div className={styles.brand}>
        <div className={styles.brandIcon} aria-hidden>
          ⛏
        </div>
        <span className={styles.brandText}>代码考古学</span>
      </div>

      <div className={styles.project}>
        <div style={{ minWidth: 0 }}>
          <div className={styles.projectName} title={projectName}>
            {projectName}
          </div>
          <div className={styles.projectMeta}>
            {scanStatus === 'scanning' ? '扫描中' : scanStatus === 'done' ? '就绪' : '空闲'}
            {scanTotal > 0 && ` · ${scanTotal} 文件`}
          </div>
        </div>
        <button
          className={styles.projectSwitch}
          onClick={handleSwitchProject}
          aria-label="切换项目"
        >
          切换
        </button>
      </div>

      <div
        className={styles.segmented}
        role="tablist"
        aria-label="视图层级"
      >
        {VIEW_LEVELS.map((lv) => (
          <button
            key={lv}
            role="tab"
            aria-selected={viewLevel === lv}
            className={`${styles.segment} ${viewLevel === lv ? styles.active : ''}`}
            onClick={() => setViewLevel(lv)}
          >
            {viewLevelLabel(lv)}
          </button>
        ))}
      </div>

      <div className={styles.spacer} />

      {scanStatus === 'scanning' && scanTotal > 0 && (
        <div className={styles.progress} aria-live="polite">
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${(scanProgress / scanTotal) * 100}%` }}
            />
          </div>
          <span>
            {scanProgress}/{scanTotal}
          </span>
        </div>
      )}

      <div className={styles.toolGroup}>
        <select
          className={styles.select}
          value={colorMode}
          onChange={(e) => setColorMode(e.target.value as ColorMode)}
          aria-label="颜色模式"
        >
          {COLOR_MODES.map((m) => (
            <option key={m} value={m}>
              {colorModeLabel(m)}
            </option>
          ))}
        </select>

        <div className={styles.searchWrap}>
          <span className={styles.searchIcon} aria-hidden>
            ⌕
          </span>
          <input
            ref={searchRef}
            type="text"
            className={styles.search}
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="搜索函数 / 文件 / 作者"
            aria-label="全局搜索（Ctrl+K）"
          />
          <kbd className={styles.kbd}>Ctrl+K</kbd>
        </div>

        <button
          className={styles.iconBtn}
          onClick={onExportPNG}
          title="导出为 PNG"
          aria-label="导出为 PNG"
        >
          ⤓
        </button>
      </div>

      <div className={styles.scoreCard} title="屎山评分">
        <div className={styles.scoreNumber} style={{ color: scoreColor }}>
          {scoreText}
        </div>
        <div className={styles.scoreMeta}>
          <div className={styles.scoreLabel}>屎山指数</div>
          <div className={styles.scoreRating} style={{ color: scoreColor }}>
            {ratingText}
          </div>
        </div>
      </div>
    </header>
  );
}
