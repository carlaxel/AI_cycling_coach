import { useState, useEffect } from 'react';
import { FolderOpen } from 'lucide-react';
import styles from './App.module.css';
import { useFileSystem } from './context/FileSystemContext';
import { Sidebar } from './components/Sidebar';
import { MarkdownViewer } from './components/MarkdownViewer';
import { SessionViewer } from './components/SessionViewer';
import { CoachLogViewer } from './components/CoachLogViewer';
import { WeeklyReportViewer } from './components/WeeklyReportViewer';
import { BlockReportViewer } from './components/BlockReportViewer';
import type { ReportFile, ReportDirectory } from './services/fs';

function ConnectScreen() {
  const { connect, error } = useFileSystem();

  return (
    <div className={styles.landingContainer}>
      <h1 className={styles.title}>Cycling Power AI Viewer</h1>
      <p className={styles.description}>
        This is a local, frontend-only viewer for your cycling training reports. 
        Because it runs completely in your browser without a backend, you need to 
        grant it access to read the project's folder.
      </p>
      
      <button onClick={connect} className={styles.connectButton}>
        <FolderOpen size={20} />
        Connect Project Folder
      </button>

      {error && <div className={styles.error}>{error}</div>}
    </div>
  );
}

function MainDashboard() {
  const { disconnect, fsService } = useFileSystem();
  const [rootReportDir, setRootReportDir] = useState<ReportDirectory | null>(null);
  const [selectedFile, setSelectedFile] = useState<ReportFile | null>(null);
  const [loading, setLoading] = useState(true);

  // Initial load of the report structure
  useEffect(() => {
    async function load() {
      if (fsService) {
        setLoading(true);
        const dirs = await fsService.listReports();
        setRootReportDir(dirs);
        setLoading(false);
      }
    }
    load();
  }, [fsService]);

  // Handle Hash/URL synchronization
  useEffect(() => {
    if (!rootReportDir || !fsService) return;

    const syncHash = () => {
      const hash = window.location.hash.slice(1); // remove '#'
      if (hash) {
        const file = fsService.findFileByPath(rootReportDir, decodeURIComponent(hash));
        if (file) {
          setSelectedFile(file);
        }
      } else {
        setSelectedFile(null);
      }
    };

    // Initial sync
    syncHash();

    window.addEventListener('hashchange', syncHash);
    return () => window.removeEventListener('hashchange', syncHash);
  }, [rootReportDir, fsService]);

  const handleSelectFile = (file: ReportFile | null) => {
    if (file) {
      window.location.hash = encodeURIComponent(file.path);
    } else {
      window.location.hash = '';
    }
  };

  return (
    <div className={styles.appContainer}>
      <Sidebar 
        onSelectFile={handleSelectFile} 
        activeFilePath={selectedFile?.path}
        rootReportDir={rootReportDir}
        loading={loading}
      />
      
      <div className={styles.mainContent}>
        <div className={styles.topBar}>
          <h2 className={styles.topBarTitle}>
            {selectedFile ? selectedFile.name : 'Dashboard'}
          </h2>
          <button onClick={disconnect} className={styles.disconnectBtn}>Disconnect</button>
        </div>
        
        <div className={styles.contentArea}>
          {selectedFile ? (
            selectedFile.name.endsWith('.json') ? (
              selectedFile.name.includes('coach_log') ? (
                <CoachLogViewer file={selectedFile} onNavigate={handleSelectFile} />
              ) : selectedFile.name.includes('weekly_report') ? (
                <WeeklyReportViewer file={selectedFile} onNavigate={handleSelectFile} />
              ) : selectedFile.name.includes('block_') ? (
                <BlockReportViewer file={selectedFile} onNavigate={handleSelectFile} />
              ) : (
                <SessionViewer file={selectedFile} onNavigate={handleSelectFile} />
              )
            ) : (
              <MarkdownViewer file={selectedFile} onNavigate={handleSelectFile} />
            )
          ) : (
            <div className={styles.dashboardHome}>
              <h1>Performance Dashboard</h1>
              <p>Select a session or weekly report from the sidebar to begin analysis.</p>
              
              <div className={styles.dashboardGrid}>
                <div className={styles.welcomeCard}>
                  <h3>Structured Analysis</h3>
                  <p>JSON session reports provide high-fidelity metrics, interval breakdowns, and historical PR tracking.</p>
                </div>
                <div className={styles.welcomeCard}>
                  <h3>Weekly Summaries</h3>
                  <p>Review your training blocks and coach logs in Markdown format for qualitative insights.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function App() {
  const { isConnected, isRestoring } = useFileSystem();

  if (isRestoring) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: 'var(--bg-color)', color: 'var(--text-color)' }}>
        Loading your workspace...
      </div>
    );
  }

  if (!isConnected) {
    return <ConnectScreen />;
  }

  return <MainDashboard />;
}

export default App;
