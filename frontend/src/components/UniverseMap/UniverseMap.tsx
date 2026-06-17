import { useCallback, useState } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { useCytoscape } from '@/hooks/useCytoscape';
import type { GraphNode } from '@/types';
import { MapTooltip } from './MapTooltip';
import { MapLegend } from './MapLegend';
import { MapInfo } from './MapInfo';
import styles from './UniverseMap.module.css';

export interface UniverseMapProps {
  onExportPNG?: () => void;
}

export function UniverseMap({}: UniverseMapProps) {
  const graphData = useAppStore((s) => s.graphData);
  const colorMode = useAppStore((s) => s.colorMode);
  const selectedNode = useAppStore((s) => s.selectedNode);
  const setSelectedNode = useAppStore((s) => s.setSelectedNode);
  const searchKeyword = useAppStore((s) => s.searchKeyword);

  const [hover, setHover] = useState<{
    node: GraphNode | null;
    x: number;
    y: number;
  }>({ node: null, x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);

  const handleSelect = useCallback(
    (n: GraphNode | null) => {
      setSelectedNode(n);
    },
    [setSelectedNode],
  );

  const handleHover = useCallback(
    (n: GraphNode | null, pos: { x: number; y: number }) => {
      setHover({ node: n, x: pos.x, y: pos.y });
    },
    [],
  );

  const handleZoom = useCallback((z: number) => {
    setZoom(z);
  }, []);

  const handleDoubleClick = useCallback((n: GraphNode) => {
    if (import.meta.env.DEV) console.info('[universe-map] double-click:', n.id);
  }, []);

  const handleBackgroundDoubleClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  const containerRef = useCytoscape({
    data: graphData,
    colorMode,
    selectedNodeId: selectedNode?.id ?? null,
    searchKeyword,
    onSelect: handleSelect,
    onHover: handleHover,
    onZoom: handleZoom,
    onDoubleClick: handleDoubleClick,
    onBackgroundDoubleClick: handleBackgroundDoubleClick,
  });

  return (
    <div className={styles.canvas}>
      <div ref={containerRef} className={styles.cyContainer} />
      <MapInfo zoom={zoom} />
      <MapLegend colorMode={colorMode} />
      <MapTooltip node={hover.node} x={hover.x} y={hover.y} />
      {!graphData && (
        <div className={styles.empty}>
          <div className={styles.emptyTitle}>等待数据</div>
          <div className={styles.emptyHint}>正在加载宇宙图…</div>
        </div>
      )}
    </div>
  );
}
