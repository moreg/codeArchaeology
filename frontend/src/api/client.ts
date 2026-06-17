import axios, { AxiosError, type AxiosInstance } from 'axios';
import type {
  GraphData,
  RefactorData,
  SampleLoadResponse,
  ScanStatus,
  ScoreData,
  StoryData,
  ViewLevel,
  ColorMode,
  WSMessage,
  GraphNode,
} from '@/types';
import {
  mockEdges,
  mockGraphData,
  mockNodes,
  mockRefactorData,
  mockSampleLoad,
  mockScanStatus,
  mockScoreData,
  mockStoryData,
  mockStoryData2,
  mockStoryData3,
} from './mockData';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

const http: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (import.meta.env.DEV) {
      console.warn('[api] request failed:', error.message);
    }
    return Promise.reject(error);
  },
);

function delay<T>(value: T, ms = 250): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

function filterGraphByLevel(nodes: GraphNode[], level: ViewLevel): GraphNode[] {
  if (level === 'function') {
    return nodes.filter((n) => n.level === 'function' || n.level === 'file');
  }
  if (level === 'module') {
    return nodes.filter((n) => n.level === 'module' || n.level === 'file');
  }
  return nodes.filter((n) => n.level === 'file');
}

function filterEdgesByLevel(
  nodes: GraphNode[],
  edges: typeof mockEdges,
  _level: ViewLevel,
): typeof mockEdges {
  const allowed = new Set(nodes.map((n) => n.id));
  return edges.filter((e) => allowed.has(e.source) && allowed.has(e.target));
}

export const apiClient = {
  async loadSample(): Promise<SampleLoadResponse> {
    if (USE_MOCK) return delay(mockSampleLoad, 300);
    const { data } = await http.post<SampleLoadResponse>('/api/sample/load');
    return data;
  },

  async getScanStatus(scanId: string): Promise<ScanStatus> {
    if (USE_MOCK) return delay(mockScanStatus, 150);
    const { data } = await http.get<ScanStatus>(`/api/scan/${scanId}/status`);
    return data;
  },

  async getGraph(
    scanId: string,
    level: ViewLevel,
    _colorMode: ColorMode,
  ): Promise<GraphData> {
    if (USE_MOCK) {
      const nodes = filterGraphByLevel(mockNodes, level);
      const edges = filterEdgesByLevel(nodes, mockEdges, level);
      return delay({ ...mockGraphData, scan_id: scanId, level, nodes, edges }, 200);
    }
    const { data } = await http.get<GraphData>(`/api/scan/${scanId}/graph`, {
      params: { level, color_mode: _colorMode },
    });
    return data;
  },

  async getScore(scanId: string): Promise<ScoreData> {
    if (USE_MOCK) return delay(mockScoreData, 200);
    const { data } = await http.get<ScoreData>(`/api/scan/${scanId}/score`);
    return data;
  },

  async getStory(scanId: string, nodeId: string): Promise<StoryData> {
    const storyMap: Record<string, StoryData> = {
      'fn:scraper.fetch_page': mockStoryData,
      'fn:main.run': mockStoryData2,
      'fn:parser.validate': mockStoryData3,
    };
    if (USE_MOCK) {
      return delay(storyMap[nodeId] ?? mockStoryData, 400);
    }
    const { data } = await http.post<StoryData>('/api/analyze/story', {
      scan_id: scanId,
      node_id: nodeId,
    });
    return data;
  },

  async getRefactor(scanId: string, nodeId: string): Promise<RefactorData> {
    if (USE_MOCK) return delay({ ...mockRefactorData, node_id: nodeId }, 350);
    const { data } = await http.post<RefactorData>('/api/analyze/refactor', {
      scan_id: scanId,
      node_id: nodeId,
    });
    return data;
  },

  connectScanWS(
    scanId: string,
    onProgress: (msg: WSMessage) => void,
    onComplete: (msg: WSMessage) => void,
    onError: (msg: WSMessage) => void,
  ): () => void {
    if (USE_MOCK) {
      let i = 0;
      const total = mockSampleLoad.total_files;
      const interval = window.setInterval(() => {
        i += 1;
        if (i < total) {
          onProgress({
            type: 'progress',
            current: i,
            total,
            file: mockNodes[i % mockNodes.length]?.file_path ?? '',
          });
        } else {
          window.clearInterval(interval);
          onComplete({
            type: 'complete',
            scan_id: scanId,
            duration: 4200,
          });
        }
      }, 200);
      return () => window.clearInterval(interval);
    }

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host;
    const url = `${proto}://${host}/ws/scan/${scanId}`;
    let ws: WebSocket | null = null;
    let closed = false;
    try {
      ws = new WebSocket(url);
    } catch (err) {
      onError({ type: 'error', message: String(err) });
      return () => undefined;
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSMessage;
        if (data.type === 'progress') onProgress(data);
        else if (data.type === 'complete') onComplete(data);
        else onError(data);
      } catch (err) {
        onError({ type: 'error', message: String(err) });
      }
    };

    ws.onerror = () => {
      if (!closed) {
        onError({ type: 'error', message: 'WebSocket 连接失败' });
      }
    };

    ws.onclose = () => {
      closed = true;
    };

    return () => {
      closed = true;
      if (ws && ws.readyState <= WebSocket.OPEN) {
        ws.close();
      }
    };
  },
};

export type ApiClient = typeof apiClient;
