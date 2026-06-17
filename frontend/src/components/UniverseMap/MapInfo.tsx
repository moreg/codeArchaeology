import { useAppStore } from '@/store/useAppStore';
import styles from './MapInfo.module.css';

export interface MapInfoProps {
  zoom: number;
}

export function MapInfo({ zoom }: MapInfoProps) {
  const graphData = useAppStore((s) => s.graphData);
  const selectedNode = useAppStore((s) => s.selectedNode);

  const nodeCount = graphData?.nodes.length ?? 0;
  const edgeCount = graphData?.edges.length ?? 0;
  const level = graphData?.level ?? 'function';

  return (
    <div className={styles.info} aria-label="画布信息">
      <div className={styles.title}>画布</div>
      <div className={styles.row}>
        <span>层级</span>
        <span className={styles.value}>{level}</span>
      </div>
      <div className={styles.row}>
        <span>节点</span>
        <span className={styles.value}>{nodeCount}</span>
      </div>
      <div className={styles.row}>
        <span>边</span>
        <span className={styles.value}>{edgeCount}</span>
      </div>
      <div className={styles.row}>
        <span>选中</span>
        <span
          className={styles.idValue}
          title={selectedNode ? selectedNode.id : '未选择'}
        >
          {selectedNode ? selectedNode.id : '—'}
        </span>
      </div>
      <div className={styles.zoom}>
        <span>ZOOM</span>
        <span>{zoom.toFixed(2)}x</span>
      </div>
    </div>
  );
}
