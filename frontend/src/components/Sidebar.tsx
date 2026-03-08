import React, { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, Folder, Zap, ClipboardList, BookOpen, Activity } from 'lucide-react';
import type { ReportDirectory, ReportFile } from '../services/fs';
import styles from './Sidebar.module.css';
import { clsx } from 'clsx';

const FileIcon: React.FC<{ file: ReportFile }> = ({ file }) => {
  if (file.name.includes('coach_log')) return <ClipboardList size={14} className={styles.iconCoach} />;
  if (file.name.includes('weekly_report')) return <Activity size={14} className={styles.iconWeekly} />;
  if (file.name.includes('block_')) return <BookOpen size={14} className={styles.iconBlock} />;
  if (file.name.endsWith('.json')) return <Zap size={14} className={styles.iconSession} />;
  if (file.name.endsWith('.md')) return <BookOpen size={14} className={styles.iconMarkdown} />;
  return <FileText size={14} />;
};

interface SidebarProps {
  onSelectFile: (file: ReportFile) => void;
  activeFilePath?: string;
  rootReportDir: ReportDirectory | null;
  loading: boolean;
}

const DirectoryNode: React.FC<{ dir: ReportDirectory; onSelectFile: (f: ReportFile) => void; activeFilePath?: string; defaultOpen?: boolean }> = ({ dir, onSelectFile, activeFilePath, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={styles.dirNode}>
      <div className={styles.dirTitle} onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <Folder size={14} />
        {dir.name}
      </div>
      
      {isOpen && (
        <div className={styles.fileList}>
          {dir.directories.map((subDir, index) => (
            <DirectoryNode key={subDir.path} dir={subDir} onSelectFile={onSelectFile} activeFilePath={activeFilePath} defaultOpen={index === 0} />
          ))}
          {dir.files.map(file => (
            <div 
              key={file.path}
              className={clsx(styles.fileNode, activeFilePath === file.path && styles.activeFile)}
              onClick={() => onSelectFile(file)}
            >
              <FileIcon file={file} />
              <span className={styles.fileName}>{file.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({ onSelectFile, activeFilePath, rootReportDir, loading }) => {
  return (
    <div className={styles.sidebar}>
      <div className={styles.header}>
        <Folder size={18} />
        Reports
      </div>
      <div className={styles.content}>
        {loading ? (
          <div className={styles.loading}>Loading reports...</div>
        ) : rootReportDir ? (
          <DirectoryNode dir={rootReportDir} onSelectFile={onSelectFile} activeFilePath={activeFilePath} defaultOpen={true} />
        ) : (
          <div className={styles.loading}>No reports found.</div>
        )}
      </div>
    </div>
  );
};
