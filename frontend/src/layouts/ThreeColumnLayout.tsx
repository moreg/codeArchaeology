import { type ReactNode } from 'react';
import { useAppStore } from '@/store/useAppStore';
import styles from './ThreeColumnLayout.module.css';

interface ThreeColumnLayoutProps {
  topBar: ReactNode;
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
}

export function ThreeColumnLayout({ topBar, left, center, right }: ThreeColumnLayoutProps) {
  const leftCollapsed = useAppStore((s) => s.leftCollapsed);
  const rightCollapsed = useAppStore((s) => s.rightCollapsed);
  const setLeftCollapsed = useAppStore((s) => s.setLeftCollapsed);
  const setRightCollapsed = useAppStore((s) => s.setRightCollapsed);

  return (
    <div className={styles.layout}>
      {topBar}
      <div className={styles.body}>
        <aside
          className={`${styles.left} ${leftCollapsed ? styles.collapsed : ''}`}
          aria-label="文件树侧边栏"
        >
          {!leftCollapsed && left}
        </aside>
        <button
          className={`${styles.toggleLeft} ${leftCollapsed ? styles.collapsed : ''}`}
          onClick={() => setLeftCollapsed(!leftCollapsed)}
          aria-label={leftCollapsed ? '展开文件树' : '折叠文件树'}
          title={leftCollapsed ? '展开文件树' : '折叠文件树'}
        >
          {leftCollapsed ? '›' : '‹'}
        </button>

        <main className={styles.center}>{center}</main>

        <button
          className={`${styles.toggleRight} ${rightCollapsed ? styles.collapsed : ''}`}
          onClick={() => setRightCollapsed(!rightCollapsed)}
          aria-label={rightCollapsed ? '展开详情面板' : '折叠详情面板'}
          title={rightCollapsed ? '展开详情面板' : '折叠详情面板'}
        >
          {rightCollapsed ? '‹' : '›'}
        </button>

        <aside
          className={`${styles.right} ${rightCollapsed ? styles.collapsed : ''}`}
          aria-label="详情面板"
        >
          {!rightCollapsed && right}
        </aside>

        <div className={styles.warning} role="alert">
          <h3>请使用更大屏幕</h3>
          <p>三栏布局需要至少 1280px 宽度才能完整显示。</p>
        </div>
      </div>
    </div>
  );
}
