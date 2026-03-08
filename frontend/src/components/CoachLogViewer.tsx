import React, { useEffect, useState } from 'react';
import { 
  Clipboard, 
  User, 
  Calendar, 
  Heart, 
  Activity,
  MessageCircle,
  Target
} from 'lucide-react';
import { useFileSystem } from '../context/FileSystemContext';
import type { ReportFile } from '../services/fs';
import styles from './CoachLogViewer.module.css';

interface CoachLogViewerProps {
  file: ReportFile;
  onNavigate?: (file: ReportFile) => void;
}

interface CoachLogSession {
  date: string;
  title: string;
  analysis: {
    plan_compliance: string;
    execution_quality: string;
    physiological_response: string;
    coach_takeaway?: string;
  };
}

interface CoachLogData {
  week_id: string;
  period: string;
  athlete: {
    weight_kg: number;
    ftp_w: number;
  };
  sessions: CoachLogSession[];
}

export const CoachLogViewer: React.FC<CoachLogViewerProps> = ({ file }) => {
  const { fsService } = useFileSystem();
  const [data, setData] = useState<CoachLogData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      if (!fsService) return;
      setLoading(true);
      try {
        const content = await fsService.readFile(file.path);
        setData(JSON.parse(content));
        setError(null);
      } catch (err) {
        console.error("Failed to load coach log JSON:", err);
        setError("Could not load coach log data.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [file.path, fsService]);

  if (loading) return <div className={styles.loading}>Loading coach log...</div>;
  if (error || !data) return <div className={styles.error}>{error || 'No data found'}</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <h1>Coach Log — {data.week_id}</h1>
          <div className={styles.metaRow}>
            <span className={styles.metaItem}><Calendar size={14} /> {data.period}</span>
            <span className={styles.metaItem}><User size={14} /> {data.athlete.weight_kg} kg | FTP: {data.athlete.ftp_w} W</span>
          </div>
        </div>
        <div className={styles.badge}>
          <Clipboard size={20} />
        </div>
      </div>

      <div className={styles.sessionList}>
        {data.sessions.map((session, index) => (
          <div key={index} className={styles.sessionCard}>
            <div className={styles.sessionHeader}>
              <div className={styles.sessionDate}>{session.date}</div>
              <h2 className={styles.sessionTitle}>{session.title}</h2>
            </div>

            <div className={styles.analysisGrid}>
              <div className={styles.analysisSection}>
                <div className={styles.sectionHeader}>
                  <Target size={16} className={styles.iconCompliance} />
                  <h3>Plan Compliance</h3>
                </div>
                <div className={styles.sectionContent}>{session.analysis.plan_compliance}</div>
              </div>

              <div className={styles.analysisSection}>
                <div className={styles.sectionHeader}>
                  <Activity size={16} className={styles.iconQuality} />
                  <h3>Execution Quality</h3>
                </div>
                <div className={styles.sectionContent}>{session.analysis.execution_quality}</div>
              </div>

              <div className={styles.analysisSection}>
                <div className={styles.sectionHeader}>
                  <Heart size={16} className={styles.iconPhysio} />
                  <h3>Physiological Response</h3>
                </div>
                <div className={styles.sectionContent}>{session.analysis.physiological_response}</div>
              </div>

              {session.analysis.coach_takeaway && (
                <div className={`${styles.analysisSection} ${styles.fullWidth}`}>
                  <div className={styles.sectionHeader}>
                    <MessageCircle size={16} className={styles.iconTakeaway} />
                    <h3>Coach's Takeaway</h3>
                  </div>
                  <div className={styles.sectionContent}>{session.analysis.coach_takeaway}</div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
