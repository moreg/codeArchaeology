import { create } from 'zustand';
import type {
  ColorMode,
  GraphData,
  GraphNode,
  ScanStatusValue,
  ScoreData,
  ViewLevel,
} from '@/types';

export type ActiveTab = 'detail' | 'score';

export interface AppState {
  scanId: string | null;
  projectName: string;
  viewLevel: ViewLevel;
  colorMode: ColorMode;
  selectedNode: GraphNode | null;
  searchKeyword: string;
  scanProgress: number;
  scanStatus: ScanStatusValue;
  scanTotal: number;
  currentFile: string;
  graphData: GraphData | null;
  scoreData: ScoreData | null;
  activeTab: ActiveTab;
  leftCollapsed: boolean;
  rightCollapsed: boolean;

  setScanId: (id: string | null) => void;
  setProjectName: (name: string) => void;
  setViewLevel: (level: ViewLevel) => void;
  setColorMode: (mode: ColorMode) => void;
  setSelectedNode: (node: GraphNode | null) => void;
  setSearchKeyword: (kw: string) => void;
  setScanProgress: (progress: number) => void;
  setScanStatus: (status: ScanStatusValue) => void;
  setScanTotal: (total: number) => void;
  setCurrentFile: (file: string) => void;
  setGraphData: (data: GraphData | null) => void;
  setScoreData: (data: ScoreData | null) => void;
  setActiveTab: (tab: ActiveTab) => void;
  setLeftCollapsed: (collapsed: boolean) => void;
  setRightCollapsed: (collapsed: boolean) => void;
  reset: () => void;
}

const initialState = {
  scanId: null,
  projectName: '未加载项目',
  viewLevel: 'function' as ViewLevel,
  colorMode: 'complexity' as ColorMode,
  selectedNode: null,
  searchKeyword: '',
  scanProgress: 0,
  scanStatus: 'idle' as ScanStatusValue,
  scanTotal: 0,
  currentFile: '',
  graphData: null,
  scoreData: null,
  activeTab: 'detail' as ActiveTab,
  leftCollapsed: false,
  rightCollapsed: true,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,
  setScanId: (id) => set({ scanId: id }),
  setProjectName: (name) => set({ projectName: name }),
  setViewLevel: (level) => set({ viewLevel: level }),
  setColorMode: (mode) => set({ colorMode: mode }),
  setSelectedNode: (node) =>
    set({
      selectedNode: node,
      rightCollapsed: node === null,
      activeTab: 'detail',
    }),
  setSearchKeyword: (kw) => set({ searchKeyword: kw }),
  setScanProgress: (progress) => set({ scanProgress: progress }),
  setScanStatus: (status) => set({ scanStatus: status }),
  setScanTotal: (total) => set({ scanTotal: total }),
  setCurrentFile: (file) => set({ currentFile: file }),
  setGraphData: (data) => set({ graphData: data }),
  setScoreData: (data) => set({ scoreData: data }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setLeftCollapsed: (collapsed) => set({ leftCollapsed: collapsed }),
  setRightCollapsed: (collapsed) =>
    set((state) => ({
      rightCollapsed: collapsed,
      selectedNode: collapsed ? null : state.selectedNode,
    })),
  reset: () => set(initialState),
}));
