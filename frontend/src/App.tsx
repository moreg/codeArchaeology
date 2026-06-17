import { useEffect } from 'react';
import { TopBar } from '@/components/TopBar/TopBar';
import { FileTree } from '@/components/FileTree/FileTree';
import { UniverseMap } from '@/components/UniverseMap/UniverseMap';
import { DetailPanel } from '@/components/DetailPanel/DetailPanel';
import { ScorePanel } from '@/components/ScorePanel/ScorePanel';
import { ThreeColumnLayout } from '@/layouts/ThreeColumnLayout';
import { useAppStore } from '@/store/useAppStore';
import { apiClient } from '@/api/client';
import type { WSMessage } from '@/types';

export function App() {
  const scanId = useAppStore((s) => s.scanId);
  const setScanId = useAppStore((s) => s.setScanId);
  const setProjectName = useAppStore((s) => s.setProjectName);
  const setGraphData = useAppStore((s) => s.setGraphData);
  const setScoreData = useAppStore((s) => s.setScoreData);
  const setScanStatus = useAppStore((s) => s.setScanStatus);
  const setScanProgress = useAppStore((s) => s.setScanProgress);
  const setScanTotal = useAppStore((s) => s.setScanTotal);
  const setCurrentFile = useAppStore((s) => s.setCurrentFile);
  const viewLevel = useAppStore((s) => s.viewLevel);
  const colorMode = useAppStore((s) => s.colorMode);
  const activeTab = useAppStore((s) => s.activeTab);

  useEffect(() => {
    let cancelled = false;
    let disconnectWS: (() => void) | null = null;
    let currentScanId: string | null = null;

    async function bootstrap(): Promise<void> {
      try {
        setScanStatus('scanning');
        const sample = await apiClient.loadSample();
        if (cancelled) return;
        currentScanId = sample.scan_id;
        setScanId(sample.scan_id);
        setProjectName(sample.project_name);
        setScanTotal(sample.total_files);

        disconnectWS = apiClient.connectScanWS(
          sample.scan_id,
          (msg: WSMessage) => {
            if (msg.type === 'progress') {
              setScanProgress(msg.current);
              setScanTotal(msg.total);
              setCurrentFile(msg.file);
            }
          },
          () => {
            setScanStatus('done');
          },
          () => {
            setScanStatus('error');
          },
        );

        const [graph, score] = await Promise.all([
          apiClient.getGraph(sample.scan_id, viewLevel, colorMode),
          apiClient.getScore(sample.scan_id),
        ]);
        if (cancelled) return;
        setGraphData(graph);
        setScoreData(score);
        setScanStatus('done');
      } catch (err) {
        if (cancelled) return;
        if (import.meta.env.DEV) {
          console.error('[app] bootstrap failed:', err);
        }
        setScanStatus('error');
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
      if (disconnectWS) disconnectWS();
      if (currentScanId) {
        // cleanup hook for future use
      }
    };
  }, [setScanId, setProjectName, setGraphData, setScoreData, setScanStatus, setScanProgress, setScanTotal, setCurrentFile]);

  useEffect(() => {
    if (!scanId) return;
    let cancelled = false;
    apiClient
      .getGraph(scanId, viewLevel, colorMode)
      .then((g) => {
        if (!cancelled) setGraphData(g);
      })
      .catch((err) => {
        if (import.meta.env.DEV) console.warn('[app] getGraph error:', err);
      });
    return () => {
      cancelled = true;
    };
  }, [viewLevel, colorMode, scanId, setGraphData]);

  const handleExportPNG = (): void => {
    const canvas = document.querySelector<HTMLCanvasElement>('canvas');
    if (!canvas) {
      window.alert('未找到画布，无法导出');
      return;
    }
    try {
      const dataUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = `code-archaeology-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      window.alert(`导出失败: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <ThreeColumnLayout
      topBar={<TopBar onExportPNG={handleExportPNG} />}
      left={<FileTree />}
      center={<UniverseMap />}
      right={activeTab === 'score' ? <ScorePanel /> : <DetailPanel />}
    />
  );
}

export default App;
