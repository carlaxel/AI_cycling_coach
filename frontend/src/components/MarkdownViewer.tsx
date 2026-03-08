import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useFileSystem } from '../context/FileSystemContext';
import type { ReportFile, ReportDirectory } from '../services/fs';
import styles from './MarkdownViewer.module.css';

interface MarkdownViewerProps {
  file: ReportFile;
  onNavigate: (file: ReportFile) => void;
}

export const MarkdownViewer: React.FC<MarkdownViewerProps> = ({ file, onNavigate }) => {
  const { fsService } = useFileSystem();
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [rootReportDir, setRootReportDir] = useState<ReportDirectory | null>(null);

  useEffect(() => {
    async function load() {
      if (fsService) {
        const dirs = await fsService.listReports();
        setRootReportDir(dirs);
      }
    }
    load();
  }, [fsService]);

  useEffect(() => {
    async function loadContent() {
      if (fsService) {
        setLoading(true);
        try {
          const text = await fsService.readFile(file.path);
          setContent(text);
        } catch (e) {
          console.error("Failed to read file", e);
          setContent("# Error\nFailed to load file content.");
        } finally {
          setLoading(false);
        }
      }
    }
    loadContent();
  }, [file, fsService]);

  const handleLinkClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string | undefined) => {
    if (!href || href.startsWith('http') || href.startsWith('#')) return;

    e.preventDefault();
    if (!fsService || !rootReportDir) return;

    // Resolve relative path
    const parts = file.path.split('/');
    parts.pop(); // Remove filename
    
    // Simple relative path resolution (handles './' and direct file names)
    let targetPath = href.startsWith('./') ? href.slice(2) : href;
    const resolvedPath = parts.length > 0 ? `${parts.join('/')}/${targetPath}` : targetPath;

    const targetFile = fsService.findFileByPath(rootReportDir, resolvedPath);
    if (targetFile) {
      onNavigate(targetFile);
    } else {
      console.warn("Could not find file at resolved path:", resolvedPath);
    }
  };

  if (loading) {
    return <div className={styles.viewerContainer}>Loading...</div>;
  }

  return (
    <div className={styles.viewerContainer}>
      <div className={styles.markdown}>
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ node, ...props }) => (
              <a 
                {...props} 
                onClick={(e) => handleLinkClick(e, props.href)} 
              />
            )
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
};
