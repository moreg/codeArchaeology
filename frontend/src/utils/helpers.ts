import type { RatingLetter } from '@/types';

/**
 * 圈复杂度评级映射
 * CC <= 5 → S, 6-10 → A, 11-20 → B, 21-30 → C, > 30 → D
 * 与 utils/colorMode.ts 中 getComplexityRating 互补（保留兼容）
 */
export function ratingFromComplexity(cc: number): RatingLetter {
  if (cc <= 5) return 'S';
  if (cc <= 10) return 'A';
  if (cc <= 20) return 'B';
  if (cc <= 30) return 'C';
  return 'D';
}

export const RATING_COLOR: Record<RatingLetter, string> = {
  S: '#4CAF50',
  A: '#8BC34A',
  B: '#FFC107',
  C: '#FF9800',
  D: '#F44336',
};

export const RATING_LABEL: Record<RatingLetter, string> = {
  S: '极简',
  A: '良好',
  B: '可接受',
  C: '需重构',
  D: '危险',
};

/**
 * 推断文件语言（基于后缀）
 */
export function inferLanguage(filePath: string): string {
  const ext = filePath.split('.').pop()?.toLowerCase() ?? '';
  const map: Record<string, string> = {
    py: 'python',
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    java: 'java',
    go: 'go',
    rs: 'rust',
    rb: 'ruby',
    php: 'php',
    c: 'c',
    h: 'c',
    cpp: 'cpp',
    cc: 'cpp',
    hpp: 'cpp',
    cs: 'csharp',
    swift: 'swift',
    kt: 'kotlin',
    sh: 'shell',
    bash: 'shell',
    yml: 'yaml',
    yaml: 'yaml',
    json: 'json',
    md: 'markdown',
    html: 'html',
    css: 'css',
    sql: 'sql',
  };
  return map[ext] ?? 'plaintext';
}

/**
 * 相对时间格式化（如 "3 天前"）
 */
export function relativeTime(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return iso;
  const diffMs = Date.now() - t;
  const sec = Math.floor(diffMs / 1000);
  if (sec < 60) return `${sec} 秒前`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} 天前`;
  const mon = Math.floor(day / 30);
  if (mon < 12) return `${mon} 个月前`;
  const yr = Math.floor(day / 365);
  return `${yr} 年前`;
}

/**
 * 截断字符串（带省略号）
 */
export function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return s.slice(0, n - 1) + '…';
}

/**
 * 颜色字符串 → 头像渐变（基于字符串哈希稳定映射）
 */
export function avatarGradient(seed: string): string {
  const palette = [
    ['#C9A96E', '#E8B84B'],
    ['#6366F1', '#8B5CF6'],
    ['#0EA5E9', '#22D3EE'],
    ['#F59E0B', '#EF4444'],
    ['#10B981', '#06B6D4'],
    ['#EC4899', '#F43F5E'],
    ['#8B5CF6', '#3B82F6'],
  ];
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  const [a, b] = palette[hash % palette.length]!;
  return `linear-gradient(135deg, ${a} 0%, ${b} 100%)`;
}

/**
 * 文件 basename
 */
export function basename(p: string): string {
  return p.split(/[\\/]/).pop() ?? p;
}

/**
 * 初始化字符串首字母（用于头像 fallback）
 */
export function initial(s: string): string {
  if (!s) return '?';
  const ch = s.trim().charAt(0);
  return /[A-Za-z0-9]/.test(ch) ? ch.toUpperCase() : ch;
}

/**
 * 复制到剪贴板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    return true;
  } catch {
    return false;
  }
}

/**
 * 安全阻止冒泡 + 默认行为
 */
export function stopAll(e: React.SyntheticEvent | Event) {
  e.preventDefault();
  e.stopPropagation();
}

/**
 * mock 代码（CodePreview 后端未返回时的降级）
 */
export function mockCode(
  name: string,
  filePath: string,
  startLine: number,
  endLine: number,
): string {
  return `# ${filePath}\n# 行号: ${startLine}-${endLine}\n\ndef ${name}(self, *args, **kwargs):\n    # TODO: 重构这个超长函数\n    ...\n`;
}