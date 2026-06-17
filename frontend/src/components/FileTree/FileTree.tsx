import { useEffect, useMemo, useState } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { mockNodes } from '@/api/mockData';
import styles from './FileTree.module.css';

type LangFilter = 'python' | 'javascript' | 'typescript' | 'java';

const LANG_FILTERS: { id: LangFilter; label: string }[] = [
  { id: 'python', label: 'Python' },
  { id: 'javascript', label: 'JS' },
  { id: 'typescript', label: 'TS' },
  { id: 'java', label: 'Java' },
];

const LANG_ICON: Record<LangFilter, string> = {
  python: 'PY',
  javascript: 'JS',
  typescript: 'TS',
  java: 'JV',
};

function getLang(filePath: string): LangFilter {
  if (filePath.endsWith('.py')) return 'python';
  if (filePath.endsWith('.ts') || filePath.endsWith('.tsx')) return 'typescript';
  if (filePath.endsWith('.js') || filePath.endsWith('.jsx')) return 'javascript';
  if (filePath.endsWith('.java')) return 'java';
  return 'python';
}

function badgeFor(cc: number): { cls: string; label: string } {
  if (cc <= 5) return { cls: 'healthy', label: 'S' };
  if (cc <= 10) return { cls: 'healthy', label: 'A' };
  if (cc <= 20) return { cls: 'warning', label: 'B' };
  if (cc <= 30) return { cls: 'danger', label: 'C' };
  return { cls: 'extreme', label: 'D' };
}

interface FileEntry {
  id: string;
  name: string;
  path: string;
  language: LangFilter;
  complexity: number;
}

interface DirNode {
  type: 'dir';
  name: string;
  path: string;
  children: TreeNode[];
}

interface FileNode {
  type: 'file';
  entry: FileEntry;
}

type TreeNode = DirNode | FileNode;

function buildTree(files: FileEntry[]): DirNode {
  const root: DirNode = { type: 'dir', name: '', path: '', children: [] };
  for (const f of files) {
    const parts = f.path.split('/');
    let cur = root;
    let acc = '';
    for (let i = 0; i < parts.length - 1; i += 1) {
      const part = parts[i];
      if (!part) continue;
      acc = acc ? `${acc}/${part}` : part;
      let next = cur.children.find(
        (c): c is DirNode => c.type === 'dir' && c.name === part,
      );
      if (!next) {
        next = { type: 'dir', name: part, path: acc, children: [] };
        cur.children.push(next);
      }
      cur = next;
    }
    cur.children.push({ type: 'file', entry: f });
  }
  return root;
}

const STORAGE_KEY = 'code-archaeology.fileTree.expanded';

function loadExpanded(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Record<string, boolean>;
  } catch {
    /* noop */
  }
  return {};
}

export function FileTree() {
  const selectedNode = useAppStore((s) => s.selectedNode);
  const setSelectedNode = useAppStore((s) => s.setSelectedNode);
  const [search, setSearch] = useState('');
  const [activeLangs, setActiveLangs] = useState<Set<LangFilter>>(
    new Set<LangFilter>(['python']),
  );
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => loadExpanded());

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(expanded));
    } catch {
      /* noop */
    }
  }, [expanded]);

  const files: FileEntry[] = useMemo(() => {
    const seen = new Set<string>();
    const out: FileEntry[] = [];
    for (const n of mockNodes) {
      if (n.level !== 'file') continue;
      if (seen.has(n.id)) continue;
      seen.add(n.id);
      out.push({
        id: n.id,
        name: n.name,
        path: n.file_path,
        language: getLang(n.file_path),
        complexity: n.complexity,
      });
    }
    return out;
  }, []);

  const tree = useMemo(() => {
    const filtered = files.filter((f) => activeLangs.has(f.language));
    return buildTree(filtered);
  }, [files, activeLangs]);

  const matchesSearch = (entry: FileEntry): boolean => {
    if (!search.trim()) return true;
    const kw = search.toLowerCase();
    return (
      entry.name.toLowerCase().includes(kw) || entry.path.toLowerCase().includes(kw)
    );
  };

  const toggleLang = (id: LangFilter): void => {
    setActiveLangs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (next.size === 0) next.add('python');
      return next;
    });
  };

  const toggleDir = (path: string): void => {
    setExpanded((prev) => ({ ...prev, [path]: !(prev[path] !== false) }));
  };

  const renderFile = (f: FileEntry): JSX.Element => {
    const badge = badgeFor(f.complexity);
    const isSelected = selectedNode?.id === f.id;
    return (
      <div
        key={f.id}
        className={`${styles.file} ${isSelected ? styles.selected : ''}`}
        onClick={() => {
          const node = mockNodes.find((n) => n.id === f.id);
          if (node) setSelectedNode(node);
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const node = mockNodes.find((n) => n.id === f.id);
            if (node) setSelectedNode(node);
          }
        }}
        title={f.path}
      >
        <span className={styles.fileIcon} aria-hidden>
          {LANG_ICON[f.language]}
        </span>
        <span className={styles.fileName}>{f.name}</span>
        <span className={`${styles.badge} ${styles[badge.cls]}`}>{badge.label}</span>
      </div>
    );
  };

  const renderDir = (node: DirNode): JSX.Element => {
    const isExpanded = expanded[node.path] !== false;
    return (
      <div key={node.path || 'root'}>
        {node.path && (
          <div
            className={styles.dir}
            onClick={() => toggleDir(node.path)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleDir(node.path);
              }
            }}
          >
            <span className={styles.caret}>{isExpanded ? '▼' : '▶'}</span>
            <span>📁 {node.name}</span>
          </div>
        )}
        {isExpanded && (
          <div>
            {node.children.map((c) =>
              c.type === 'dir' ? renderDir(c) : renderFile(c.entry),
            )}
          </div>
        )}
      </div>
    );
  };

  const flatFiles = files.filter(matchesSearch);
  const useFlat = search.trim().length > 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>文件树</div>
        <input
          type="text"
          className={styles.searchInput}
          placeholder="搜索文件…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="搜索文件"
        />
        <div className={styles.filters}>
          {LANG_FILTERS.map((f) => (
            <button
              key={f.id}
              className={`${styles.chip} ${activeLangs.has(f.id) ? styles.active : ''}`}
              onClick={() => toggleLang(f.id)}
              aria-pressed={activeLangs.has(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.tree}>
        {useFlat ? (
          flatFiles.length === 0 ? (
            <div className={styles.empty}>没有匹配的文件</div>
          ) : (
            flatFiles.map(renderFile)
          )
        ) : (
          renderDir(tree)
        )}
        {!useFlat && files.length === 0 && (
          <div className={styles.empty}>暂无文件</div>
        )}
      </div>

      <div className={styles.footer}>
        {files.length} 个文件 · S 优秀 / A-D 风险
      </div>
    </div>
  );
}
