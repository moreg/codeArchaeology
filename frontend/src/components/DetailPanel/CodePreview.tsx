import { memo, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import type { GraphNode } from '@/types';
import { basename, inferLanguage, mockCode } from '@/utils/helpers';
import styles from './CodePreview.module.css';

/**
 * CodePreview — Monaco Editor 只读代码预览
 *
 * - 语言基于文件后缀自动推断
 * - 函数所在行使用半透明沙金背景高亮（deltaDecorations）
 * - 当前未对接后端 code snippet API，使用 mockCode() 模板降级
 *   （Task 2 后端 `/api/scan/{id}/node/{nodeId}/code` 实现后可接入）
 */

interface Props {
  node: GraphNode;
}

function CodePreviewInner({ node }: Props) {
  const [code, setCode] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    // 直接使用 mock 模板（后端未提供 code 端点）
    const fallback = mockCode(
      node.name,
      node.file_path,
      node.start_line,
      node.end_line,
    );

    // 模拟短暂加载以呈现骨架屏
    const timer = window.setTimeout(() => {
      if (!cancelled) {
        setCode(fallback);
        setLoading(false);
      }
    }, 200);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [node.id, node.name, node.file_path, node.start_line, node.end_line]);

  const language = inferLanguage(node.file_path);
  const lineCount = node.end_line - node.start_line + 1;

  const handleBeforeMount = (monaco: typeof import('monaco-editor')) => {
    monaco.editor.defineTheme('archaeology-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6b6862', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'c9a96e' },
        { token: 'string', foreground: 'a8c47f' },
        { token: 'number', foreground: 'e8b84b' },
        { token: 'type', foreground: '93c5fd' },
      ],
      colors: {
        'editor.background': '#060a14',
        'editor.foreground': '#f5f0e8',
        'editor.lineHighlightBackground': '#1a1f2e',
        'editor.lineHighlightBorder': '#1a1f2e',
        'editorLineNumber.foreground': '#4a4842',
        'editorLineNumber.activeForeground': '#c9a96e',
        'editorCursor.foreground': '#e8b84b',
        'editor.selectionBackground': '#c9a96e33',
      },
    });
  };

  const handleMount = (
    editor: import('monaco-editor').editor.IStandaloneCodeEditor,
    monaco: typeof import('monaco-editor'),
  ) => {
    const totalLines = editor.getModel()?.getLineCount() ?? 0;
    if (totalLines === 0) return;

    // 高亮整个 snippet（视为目标函数上下文）
    const highlightStart = Math.min(
      Math.max(1, totalLines - lineCount + 1),
      totalLines,
    );
    const highlightEnd = totalLines;

    editor.deltaDecorations([], [
      {
        range: new monaco.Range(highlightStart, 1, highlightEnd, 1),
        options: {
          isWholeLine: true,
          className: styles.highlightLine,
          marginClassName: styles.highlightMargin,
        },
      },
    ]);

    editor.revealLineInCenter(highlightEnd);
  };

  return (
    <section className={styles.section} aria-label="代码预览">
      <header className={styles.header}>
        <span className={styles.title}>代码预览</span>
        <span className={styles.langChip}>{language}</span>
      </header>

      <div className={styles.infoBar}>
        <span className={styles.infoPath} title={node.file_path}>
          📄 {basename(node.file_path)}
        </span>
        <span className={styles.infoRange}>
          行 {node.start_line} - {node.end_line} · 共 {lineCount} 行
        </span>
      </div>

      <div className={styles.editorWrap}>
        {loading ? (
          <div className={styles.loading}>
            <div
              className={`${styles.loadingRow} skeleton`}
              style={{ width: '85%' }}
            />
            <div
              className={`${styles.loadingRow} skeleton`}
              style={{ width: '60%' }}
            />
            <div
              className={`${styles.loadingRow} skeleton`}
              style={{ width: '90%' }}
            />
            <div
              className={`${styles.loadingRow} skeleton`}
              style={{ width: '40%' }}
            />
          </div>
        ) : (
          <Editor
            height="100%"
            language={language}
            value={code}
            theme="archaeology-dark"
            beforeMount={handleBeforeMount}
            onMount={handleMount}
            options={{
              readOnly: true,
              domReadOnly: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontFamily:
                'JetBrains Mono, IBM Plex Mono, Consolas, monospace',
              fontSize: 12,
              lineHeight: 20,
              lineNumbers: 'on',
              renderLineHighlight: 'all',
              folding: true,
              automaticLayout: true,
              scrollbar: {
                verticalScrollbarSize: 8,
                horizontalScrollbarSize: 8,
                alwaysConsumeMouseWheel: false,
              },
              padding: { top: 12, bottom: 12 },
              guides: { indentation: false },
              contextmenu: false,
              occurrencesHighlight: 'off',
              selectionHighlight: false,
            }}
            loading={
              <div className={styles.editorLoading}>
                <div
                  className="skeleton"
                  style={{ height: 20, width: '70%' }}
                />
              </div>
            }
          />
        )}
      </div>
    </section>
  );
}

export const CodePreview = memo(CodePreviewInner);
export default CodePreview;