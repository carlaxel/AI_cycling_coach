import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Calendar, 
  Info, 
  TrendingUp, 
  Zap, 
  Clock, 
  Activity,
  Trophy,
  FileText,
  Layout
} from 'lucide-react';
import { useFileSystem } from '../context/FileSystemContext';
import type { ReportFile, ReportDirectory } from '../services/fs';
import styles from './WeeklyReportViewer.module.css';

interface WeeklyReportViewerProps {
  file: ReportFile;
  onNavigate?: (file: ReportFile) => void;
}

interface WeeklyReportData {
  version: string;
  week_id: string;
  period: string;
  ftp: number;
  weight: number;
  summary: {
    sessions_count: number;
    total_tss: number;
    total_duration_s: number;
    total_distance_m: number;
    total_ascent_m: number;
    avg_if: number;
    avg_np: number;
    avg_np_w_kg: number;
  };
  fitness: {
    ctl: number;
    atl: number;
    tsb: number;
    ctl_delta: number;
    ctl_prev: number;
    atl_prev: number;
    tsb_prev: number;
    ramp_rate: number;
    ramp_label: string;
    form_label: string;
  };
  peaks: {
    duration_s: number;
    label: string;
    watts: number;
    all_time_best: number;
  }[];
  sessions: {
    date: string;
    type: string;
    duration_s: number;
    np: number;
    if: number;
    tss: number;
    filename: string;
    is_muddle: boolean;
    is_hr_muddle: boolean;
    tss_status: string;
  }[];
  zones: {
    name: string;
    seconds: number;
    percent: number;
  }[];
  hr_zones: {
    z1_time_seconds: number;
    z2_time_seconds: number;
    z3_time_seconds: number;
    z4_time_seconds: number;
    z5_time_seconds: number;
    z6_time_seconds: number;
  };
  model_alignment: {
    low_pct: number;
    mid_pct: number;
    high_pct: number;
    low_status: string;
    mid_status: string;
    high_status: string;
  };
  commentary: {
    title: string;
    content: string;
  }[];
}

const formatDuration = (seconds: number) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
};

const formatDist = (m: number | null) => {
  if (m === null) return '—';
  return `${(m / 1000).toFixed(1)} km`;
};

const MetricCard: React.FC<{ label: string; value: string | number | null; icon?: React.ReactNode; subValue?: string }> = ({ label, value, icon, subValue }) => (
  <div className={styles.metricCard}>
    <div className={styles.metricHeader}>
      <span className={styles.metricLabel}>{label}</span>
      {icon && <span className={styles.metricIcon}>{icon}</span>}
    </div>
    <div className={styles.metricValue}>{value ?? '—'}</div>
    {subValue && <div className={styles.metricSubValue}>{subValue}</div>}
  </div>
);

export const WeeklyReportViewer: React.FC<WeeklyReportViewerProps> = ({ file, onNavigate }) => {
  const { fsService } = useFileSystem();
  const [data, setData] = useState<WeeklyReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rootReportDir, setRootReportDir] = useState<ReportDirectory | null>(null);

  useEffect(() => {
    async function loadDirs() {
      if (fsService) {
        const dirs = await fsService.listReports();
        setRootReportDir(dirs);
      }
    }
    loadDirs();
  }, [fsService]);

  useEffect(() => {
    async function loadData() {
      if (!fsService) return;
      setLoading(true);
      try {
        const content = await fsService.readFile(file.path);
        setData(JSON.parse(content));
        setError(null);
      } catch (err) {
        console.error("Failed to load weekly report JSON:", err);
        setError("Could not load weekly report data.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [file.path, fsService]);

  const handleSessionClick = (e: React.MouseEvent, filename: string) => {
    if (!fsService || !rootReportDir || !onNavigate) return;
    e.preventDefault();
    
    // Resolve relative to current weekly_report.json
    const parts = file.path.split('/');
    parts.pop();
    const resolvedPath = `${parts.join('/')}/${filename}`;
    const targetFile = fsService.findFileByPath(rootReportDir, resolvedPath);
    
    if (targetFile) {
      onNavigate(targetFile);
    }
  };

  if (loading) return <div className={styles.loading}>Loading weekly report...</div>;
  if (error || !data) return <div className={styles.error}>{error || 'No data found'}</div>;

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <h1>Weekly Report — {data.week_id}</h1>
          <div className={styles.metaRow}>
            <span className={styles.metaItem}><Calendar size={14} /> {data.period}</span>
            <span className={styles.metaItem}><Info size={14} /> FTP: {data.ftp}W | {data.weight}kg</span>
          </div>
        </div>
        <div className={styles.tssBadge}>
          <span className={styles.tssValue}>{data.summary.total_tss.toFixed(0)}</span>
          <span className={styles.tssLabel}>TSS</span>
        </div>
      </div>

      {/* Fitness & PMC Section */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <Activity size={18} />
          <h2>Fitness & Form (PMC)</h2>
        </div>
        <div className={styles.fitnessGrid}>
          <div className={styles.fitnessCard}>
            <div className={styles.fitnessLabel}>CTL (Fitness)</div>
            <div className={styles.fitnessValue}>{data.fitness.ctl.toFixed(1)}</div>
            <div className={`${styles.fitnessSub} ${data.fitness.ctl_delta >= 0 ? styles.positive : styles.negative}`}>
              {data.fitness.ctl_delta >= 0 ? '+' : ''}{data.fitness.ctl_delta.toFixed(1)} this week
            </div>
          </div>
          <div className={styles.fitnessCard}>
            <div className={styles.fitnessLabel}>ATL (Fatigue)</div>
            <div className={styles.fitnessValue}>{data.fitness.atl.toFixed(1)}</div>
            <div className={styles.fitnessSub}>Prev: {data.fitness.atl_prev.toFixed(1)}</div>
          </div>
          <div className={styles.fitnessCard}>
            <div className={styles.fitnessLabel}>TSB (Form)</div>
            <div className={styles.fitnessValue}>{data.fitness.tsb.toFixed(1)}</div>
            <div className={styles.fitnessStatus}>{data.fitness.form_label}</div>
          </div>
          <div className={styles.fitnessCard}>
            <div className={styles.fitnessLabel}>Ramp Rate</div>
            <div className={styles.fitnessValue}>{data.fitness.ramp_rate.toFixed(1)}</div>
            <div className={styles.fitnessStatus}>{data.fitness.ramp_label}</div>
          </div>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className={styles.metricsGrid}>
        <MetricCard 
          label="Sessions" 
          value={data.summary.sessions_count} 
          icon={<Layout size={16} />} 
        />
        <MetricCard 
          label="Total Duration" 
          value={formatDuration(data.summary.total_duration_s)} 
          icon={<Clock size={16} />} 
        />
        <MetricCard 
          label="Total Distance" 
          value={formatDist(data.summary.total_distance_m)} 
          icon={<TrendingUp size={16} />} 
          subValue={`Elev: ${data.summary.total_ascent_m}m`}
        />
        <MetricCard 
          label="Avg Intensity" 
          value={data.summary.avg_if.toFixed(3)} 
          icon={<Zap size={16} />} 
          subValue={`NP: ${data.summary.avg_np.toFixed(0)}W (${data.summary.avg_np_w_kg.toFixed(2)} W/kg)`}
        />
      </div>

      {/* Sessions Table */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <FileText size={18} />
          <h2>Sessions Breakdown</h2>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.sessionsTable}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Duration</th>
                <th>NP</th>
                <th>IF</th>
                <th>TSS</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.sessions.map((session, idx) => (
                <tr key={idx}>
                  <td>{session.date}</td>
                  <td>
                    <a href="#" onClick={(e) => handleSessionClick(e, session.filename)} className={styles.sessionLink}>
                      {session.type}
                    </a>
                  </td>
                  <td>{formatDuration(session.duration_s)}</td>
                  <td>{session.np.toFixed(0)} W</td>
                  <td>{session.if.toFixed(2)}</td>
                  <td>{session.tss.toFixed(0)}</td>
                  <td className={session.tss_status === 'OK' ? styles.statusOk : styles.statusWarning}>
                    {session.tss_status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Alignment & Zones */}
      <div className={styles.twoColumnGrid}>
        <div className={styles.section}>
          <div className={styles.cardHeader}>
            <h2>Power Distribution</h2>
          </div>
          <div className={styles.zoneList}>
            {data.zones.map(zone => (
              <div key={zone.name} className={styles.zoneRow}>
                <div className={styles.zoneInfo}>
                  <span className={styles.zoneName}>{zone.name}</span>
                  <span className={styles.zoneTime}>{formatDuration(zone.seconds)}</span>
                </div>
                <div className={styles.zoneBarContainer}>
                  <div 
                    className={styles.zoneBar} 
                    style={{ 
                      width: `${zone.percent}%`,
                      backgroundColor: getZoneColor(zone.name)
                    }}
                  />
                  <span className={styles.zonePercent}>{zone.percent.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.section}>
          <div className={styles.cardHeader}>
            <h2>Model Alignment</h2>
          </div>
          <div className={styles.alignmentGrid}>
            <div className={styles.alignmentCard}>
              <div className={styles.alignmentLabel}>Low (Z1-Z2)</div>
              <div className={styles.alignmentValue}>{data.model_alignment.low_pct.toFixed(1)}%</div>
              <div className={data.model_alignment.low_status === 'OK' ? styles.statusOk : styles.statusWarning}>
                {data.model_alignment.low_status}
              </div>
            </div>
            <div className={styles.alignmentCard}>
              <div className={styles.alignmentLabel}>Mid (Z3-Z4)</div>
              <div className={styles.alignmentValue}>{data.model_alignment.mid_pct.toFixed(1)}%</div>
              <div className={data.model_alignment.mid_status === 'OK' ? styles.statusOk : styles.statusWarning}>
                {data.model_alignment.mid_status}
              </div>
            </div>
            <div className={styles.alignmentCard}>
              <div className={styles.alignmentLabel}>High (Z5+)</div>
              <div className={styles.alignmentValue}>{data.model_alignment.high_pct.toFixed(1)}%</div>
              <div className={data.model_alignment.high_status === 'OK' ? styles.statusOk : styles.statusWarning}>
                {data.model_alignment.high_status}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Peak Power Durations */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <Trophy size={18} />
          <h2>Peak Power Best (This Week)</h2>
        </div>
        <div className={styles.peaksGrid}>
          {data.peaks.map(peak => (
            <div key={peak.label} className={styles.peakCard}>
              <div className={styles.peakLabel}>{peak.label}</div>
              <div className={styles.peakValue}>
                {peak.watts} <span className={styles.unit}>W</span>
              </div>
              <div className={styles.peakSub}>
                All-time: {peak.all_time_best}W
              </div>
              {peak.watts >= peak.all_time_best && (
                <div className={styles.prBadge}>All-time PR</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Commentary Sections */}
      {data.commentary.map((comm, idx) => (
        <div key={idx} className={styles.section}>
          <div className={styles.commentaryCard}>
            <h2 className={styles.commentaryTitle}>{comm.title}</h2>
            <div className={styles.markdownContent}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {comm.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

const getZoneColor = (name: string) => {
  if (name.includes('Z1')) return '#94a3b8'; // Slate
  if (name.includes('Z2')) return '#22c55e'; // Green
  if (name.includes('Z3')) return '#eab308'; // Yellow
  if (name.includes('Z4')) return '#f97316'; // Orange
  if (name.includes('Z5')) return '#ef4444'; // Red
  if (name.includes('Z6')) return '#d946ef'; // Fuchsia
  if (name.includes('Z7')) return '#7c3aed'; // Violet
  return '#3b82f6';
};
