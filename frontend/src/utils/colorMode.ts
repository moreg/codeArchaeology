import type { ColorMode, ComplexityRating, GraphEdge, GraphNode } from '@/types';

const AUTHOR_PALETTE = [
  '#C9A96E',
  '#E8B84B',
  '#10B981',
  '#3B82F6',
  '#8B5CF6',
  '#F59E0B',
  '#EF4444',
  '#06B6D4',
  '#EC4899',
  '#84CC16',
];

function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

export function getAuthorColor(author: string): string {
  const h = hashString(author || 'unknown');
  return AUTHOR_PALETTE[h % AUTHOR_PALETTE.length];
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

function lerpColor(a: string, b: string, t: number): string {
  const pa = parseInt(a.slice(1), 16);
  const pb = parseInt(b.slice(1), 16);
  const ar = (pa >> 16) & 0xff;
  const ag = (pa >> 8) & 0xff;
  const ab = pa & 0xff;
  const br = (pb >> 16) & 0xff;
  const bg = (pb >> 8) & 0xff;
  const bb = pb & 0xff;
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return `#${((r << 16) | (g << 8) | bl).toString(16).padStart(6, '0')}`;
}

const C_GREEN = '#4CAF50';
const C_YELLOW = '#FFC107';
const C_ORANGE = '#FF9800';
const C_RED = '#F44336';

function complexityColor(cc: number): string {
  if (cc <= 5) return C_GREEN;
  if (cc <= 10) return lerpColor(C_GREEN, C_YELLOW, (cc - 5) / 5);
  if (cc <= 20) return lerpColor(C_YELLOW, C_ORANGE, (cc - 10) / 10);
  return lerpColor(C_ORANGE, C_RED, clamp((cc - 20) / 15, 0, 1));
}

function frequencyColor(lastModified: string, minT: number, maxT: number): string {
  const t = new Date(lastModified).getTime();
  if (maxT === minT) return '#3B82F6';
  const ratio = (t - minT) / (maxT - minT);
  if (ratio > 0.66) return '#3B82F6';
  if (ratio > 0.33) return '#1D4ED8';
  return '#1E3A8A';
}

export function computeTimeRange(nodes: GraphNode[]): { minT: number; maxT: number } {
  if (!nodes.length) return { minT: 0, maxT: 0 };
  let minT = Infinity;
  let maxT = -Infinity;
  for (const n of nodes) {
    const t = new Date(n.last_modified || '').getTime();
    if (t < minT) minT = t;
    if (t > maxT) maxT = t;
  }
  return { minT, maxT };
}

function testCoverageColor(coverage: number): string {
  return coverage > 0 ? '#10B981' : '#EF4444';
}

export function getNodeColor(
  node: GraphNode,
  mode: ColorMode,
  timeRange?: { minT: number; maxT: number },
): string {
  switch (mode) {
    case 'complexity':
      return complexityColor(node.complexity);
    case 'frequency':
      return frequencyColor(
        node.last_modified || '',
        timeRange?.minT ?? 0,
        timeRange?.maxT ?? 0,
      );
    case 'author':
      return getAuthorColor(node.author || '');
    case 'test_coverage':
      return testCoverageColor(node.test_coverage || 0);
    default:
      return '#888888';
  }
}

export function getNodeSize(node: GraphNode): number {
  if (node.level === 'file') {
    return clamp(20 + Math.sqrt(node.line_count) * 3, 20, 80);
  }
  if (node.level === 'module') {
    return clamp(30 + node.complexity * 1.5, 30, 100);
  }
  return clamp(12 + node.complexity * 0.4, 12, 22);
}

export function getNodeShape(node: GraphNode): string {
  switch (node.level) {
    case 'file':
      return 'ellipse';
    case 'module':
      return 'hexagon';
    case 'function':
      return 'round-rectangle';
    default:
      return 'ellipse';
  }
}

export function getEdgeWidth(edge: GraphEdge): number {
  switch (edge.call_type) {
    case 'direct':
      return clamp(1 + edge.call_count * 0.3, 1, 4);
    case 'dataflow':
      return clamp(1 + edge.call_count * 0.2, 1, 3);
    case 'callback':
      return 2;
    case 'indirect':
      return 1;
    default:
      return 1;
  }
}

export function getEdgeColor(edge: GraphEdge): string {
  switch (edge.call_type) {
    case 'direct':
      return '#888888';
    case 'indirect':
      return '#CCCCCC';
    case 'callback':
      return '#FF8C00';
    case 'dataflow':
      return '#4A90D9';
    default:
      return '#888888';
  }
}

export function getEdgeStyle(edge: GraphEdge): {
  width: number;
  color: string;
  lineStyle: 'solid' | 'dashed' | 'dotted';
  targetArrowShape: 'none' | 'triangle';
} {
  const width = getEdgeWidth(edge);
  const color = getEdgeColor(edge);
  switch (edge.call_type) {
    case 'direct':
      return { width, color, lineStyle: 'solid', targetArrowShape: 'triangle' };
    case 'indirect':
      return { width, color, lineStyle: 'dashed', targetArrowShape: 'none' };
    case 'callback':
      return { width, color, lineStyle: 'dotted', targetArrowShape: 'triangle' };
    case 'dataflow':
      return { width, color, lineStyle: 'solid', targetArrowShape: 'triangle' };
    default:
      return { width, color, lineStyle: 'solid', targetArrowShape: 'none' };
  }
}

export function getComplexityRating(cc: number): ComplexityRating {
  if (cc <= 5) return { grade: 'S', label: '优秀', color: '#4CAF50' };
  if (cc <= 10) return { grade: 'A', label: '良好', color: '#8BC34A' };
  if (cc <= 20) return { grade: 'B', label: '一般', color: '#FFC107' };
  if (cc <= 30) return { grade: 'C', label: '警告', color: '#FF9800' };
  return { grade: 'D', label: '危险', color: '#F44336' };
}

export function formatDate(iso: string): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function colorModeLabel(mode: ColorMode): string {
  switch (mode) {
    case 'complexity':
      return '圈复杂度';
    case 'frequency':
      return '修改频率';
    case 'author':
      return '作者分布';
    case 'test_coverage':
      return '测试覆盖';
    default:
      return mode;
  }
}

export function viewLevelLabel(level: 'file' | 'module' | 'function'): string {
  switch (level) {
    case 'file':
      return '文件级';
    case 'module':
      return '模块级';
    case 'function':
      return '函数级';
    default:
      return level;
  }
}
