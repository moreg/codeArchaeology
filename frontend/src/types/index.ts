/**
 * 全局类型定义 — 代码考古学
 * 与后端 FastAPI 契约 + 前端 mock 数据契约对齐（参见 spec.md）
 */

// ============ 节点 ============
export type NodeLevel = 'file' | 'module' | 'function';

export type ColorMode = 'complexity' | 'frequency' | 'author' | 'test_coverage';

export interface GraphNode {
  id: string;
  name: string;
  level: NodeLevel;
  file_path: string;
  start_line: number;
  end_line: number;
  complexity: number;
  line_count: number;
  author?: string;
  author_email?: string;
  last_modified?: string;
  last_commit_hash?: string;
  test_coverage?: number;
  modified_count?: number;
  rating?: RatingLetter;
  language?: string;
  parent_id?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  call_type: 'direct' | 'indirect' | 'callback' | 'dataflow';
  call_count: number;
}

export interface GraphData {
  scan_id: string;
  level: ViewLevel;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export type RatingLetter = 'S' | 'A' | 'B' | 'C' | 'D';

export interface ComplexityRating {
  grade: RatingLetter;
  label: string;
  color: string;
}

// ============ Git Commit ============
/** 与 mockData.ts 契约对齐：commit_hash + date + author + message */
export interface GitCommit {
  commit_hash: string;
  date: string;
  author: string;
  message: string;
}

// ============ Story (老员工故事会) ============
/** 与 mockData.ts 契约对齐：timeline 是 GitCommit[]，narrative 是 HTML 字符串 */
export interface StoryData {
  node_id: string;
  summary: string;
  timeline: GitCommit[];
  narrative: string;
  model: string;
  generated_at: string;
  // 兼容旧字段（DetailPanel 内部使用）
  generated_by?: 'llm' | 'mock';
  author?: {
    name: string;
    role: string;
    avatar_color?: [string, string];
  };
}

// ============ Refactor ============
/** 与 mockData.ts 契约对齐：suggestion + diff + estimated_reduction */
export type RefactorPriority = 'high' | 'medium' | 'low';

export interface RefactorData {
  node_id: string;
  suggestion: string;
  priority: RefactorPriority;
  diff: string;
  estimated_reduction: string;
  // 兼容旧字段
  title?: string;
  description?: string;
  expected_benefit?: string;
  diff_preview?: string;
  steps?: string[];
  generated_by?: 'llm' | 'mock';
}

// ============ Score (屎山评分) ============
/** 与 mockData.ts 契约对齐：dimensions 是平铺的数字对象 */
export interface ScoreData {
  scan_id: string;
  total_score: number;
  rating: string;
  rating_color: string;
  dimensions: {
    complexity: number;
    duplication: number;
    comment: number;
    author_centrality: number;
    test_coverage: number;
  };
  hot_spots: HotSpot[];
  // 兼容字段
  rating_label?: string;
  generated_at?: string;
}

export type HotSpotSeverity = 'extreme' | 'high' | 'medium' | 'low';

export interface HotSpot {
  rank: number;
  file_path: string;
  function_name: string;
  severity: HotSpotSeverity;
  severity_color: string;
  complexity: number;
  suggestion: string;
  // 兼容字段
  node_id?: string;
}

// ============ 视图等级 ============
export type ViewLevel = 'file' | 'module' | 'function';

// ============ Scan / Project ============
export type ScanStatusValue = 'idle' | 'scanning' | 'done' | 'error';

export interface ScanStatus {
  scan_id: string;
  progress: number;
  total: number;
  current_file: string;
  status: ScanStatusValue | 'running' | 'completed' | 'failed';
}

export interface SampleLoadResponse {
  scan_id: string;
  project_name: string;
  project_path: string;
  total_files: number;
}

// ============ WebSocket ============
export type WSMessage =
  | { type: 'progress'; current: number; total: number; file: string }
  | { type: 'complete'; scan_id: string; duration: number }
  | { type: 'error'; message: string };

// ============ Active Tab (右侧面板) ============
export type RightPanelTab = 'detail' | 'score';