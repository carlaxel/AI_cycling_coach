import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Calendar, 
  Activity,
  Trophy,
  Layout,
  TrendingUp,
  Clock,
  Zap,
  Layers
} from 'lucide-react';
import { useFileSystem } from '../context/FileSystemContext';
import type { ReportFile, ReportDirectory } from '../services/fs';
import styles from './BlockReportViewer.module.css';

interface BlockReportViewerProps {
  file: ReportFile;
  onNavigate?: (file: ReportFile) => void;
}

interface BlockReportData {
  version: string;
  block_id: string;
  period: string;
  weeks: string[];
  summary: {
    weeks_count: number;
    sessions_count: number;
    total_tss: number;
    total_duration_s: number;
    avg_if: number;
    low_pct: number;
    mid_pct: number;
    high_pct: number;
  };
  fitness_trend: {
    label: string;
    ctl: number;
    atl: number;
    tsb: number;
    form_label: string;
  }[];
  peaks: {
    label: string;
    peaks: {
      label: string;
      watts: number | null;
    }[];
  }[];
  weekly_summaries: {
    label: string;
    sessions_count: number;
    total_tss: number;
    total_duration_s: number;
    avg_if: number | null;
    avg_np: number | null;
    avg_vi: number | null;
    avg_ef: number | null;
    avg_decoupling_pct: number | null;
    dominant_type: string;
    low_pct: number;
    mid_pct: number;
    high_pct: number;
  }[];
  zones: {
    name: string;
    seconds: number;
    percent: number;
  }[];
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

export const BlockReportViewer: React.FC<BlockReportViewerProps> = ({ file, onNavigate }) => {
  const { fsService } = useFileSystem();
  const [data, setData] = useState<BlockReportData | null>(null);
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
        console.error("Failed to load block report JSON:", err);
        setError("Could not load block report data.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [file.path, fsService]);

  if (loading) return <div className={styles.loading}>Loading block report...</div>;
  if (error || !data) return <div className={styles.error}>{error || 'No data found'}</div>;

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <h1>Block Analysis — {data.summary.weeks_count} Weeks</h1>
          <div className={styles.metaRow}>
            <span className={styles.metaItem}><Calendar size={14} /> {data.period}</span>
            <span className={styles.metaItem}><Layers size={14} /> Weeks: {data.weeks.join(', ')}</span>
          </div>
        </div>
        <div className={styles.tssBadge}>
          <span className={styles.tssValue}>{data.summary.total_tss.toFixed(0)}</span>
          <span className={styles.tssLabel}>Total TSS</span>
        </div>
      </div>

      {/* Fitness Trends */}
      {data.fitness_trend.length > 0 && (
        <div className={styles.section}>
          <div className={styles.cardHeader}>
            <Activity size={18} />
            <h2>Performance Management Chart (PMC) Trends</h2>
          </div>
          <div className={styles.fitnessGrid}>
            {data.fitness_trend.map(snap => (
              <div key={snap.label} className={styles.fitnessCard}>
                <div className={styles.fitnessLabel}>{snap.label}</div>
                <div className={styles.fitnessValue}>CTL: {snap.ctl.toFixed(1)}</div>
                <div className={styles.fitnessSub}>TSB: {snap.tsb.toFixed(1)}</div>
                <div className={styles.fitnessStatus}>{snap.form_label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Metrics */}
      <div className={styles.metricsGrid}>
        <MetricCard 
          label="Total Sessions" 
          value={data.summary.sessions_count} 
          icon={<Layout size={16} />} 
        />
        <MetricCard 
          label="Block Duration" 
          value={formatDuration(data.summary.total_duration_s)} 
          icon={<Clock size={16} />} 
        />
        <MetricCard 
          label="Block Avg Intensity" 
          value={data.summary.avg_if?.toFixed(3) ?? '—'} 
          icon={<Zap size={16} />} 
        />
        <MetricCard 
          label="Low Intensity (Z1-Z2)" 
          value={`${data.summary.low_pct.toFixed(1)}%`} 
          icon={<TrendingUp size={16} />} 
          subValue={`Mid: ${data.summary.mid_pct.toFixed(1)}% | High: ${data.summary.high_pct.toFixed(1)}%`}
        />
      </div>

      {/* Weekly Breakdown Table */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <Layers size={18} />
          <h2>Week-by-Week Breakdown</h2>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.blockTable}>
            <thead>
              <tr>
                <th>Week</th>
                <th>Sessions</th>
                <th>TSS</th>
                <th>Hours</th>
                <th>Avg IF</th>
                <th>Dominant Type</th>
              </tr>
            </thead>
            <tbody>
              {data.weekly_summaries.map((ws, idx) => (
                <tr key={idx}>
                  <td>{ws.label}</td>
                  <td>{ws.sessions_count}</td>
                  <td>{ws.total_tss.toFixed(0)}</td>
                  <td>{(ws.total_duration_s / 3600).toFixed(1)}h</td>
                  <td>{ws.avg_if?.toFixed(3) ?? '—'}</td>
                  <td>{ws.dominant_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Power Metric Trends */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <Zap size={18} />
          <h2>Power & Efficiency Trends</h2>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.blockTable}>
            <thead>
              <tr>
                <th>Week</th>
                <th>Avg NP</th>
                <th>Avg VI</th>
                <th>Avg EF</th>
                <th>Avg Decoupling</th>
              </tr>
            </thead>
            <tbody>
              {data.weekly_summaries.map((ws, idx) => (
                <tr key={idx}>
                  <td>{ws.label}</td>
                  <td>{ws.avg_np ? `${ws.avg_np.toFixed(0)} W` : '—'}</td>
                  <td>{ws.avg_vi?.toFixed(3) ?? '—'}</td>
                  <td>{ws.avg_ef?.toFixed(2) ?? '—'}</td>
                  <td>{ws.avg_decoupling_pct !== null ? `${ws.avg_decoupling_pct > 0 ? '+' : ''}${ws.avg_decoupling_pct.toFixed(1)}%` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Power Duration Trends */}
      {data.peaks.length > 0 && (
        <div className={styles.section}>
          <div className={styles.cardHeader}>
            <Trophy size={18} />
            <h2>Power Duration Trends</h2>
          </div>
          <div className={styles.tableWrapper}>
            <table className={styles.blockTable}>
              <thead>
                <tr>
                  <th>Week</th>
                  {data.peaks[0].peaks.map(p => <th key={p.label}>{p.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {data.peaks.map((row, idx) => (
                  <tr key={idx}>
                    <td>{row.label}</td>
                    {row.peaks.map((p, pidx) => (
                      <td key={pidx}>{p.watts ? `${p.watts} W` : '—'}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Combined Zones */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <h2>Combined Block Zone Distribution</h2>
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
