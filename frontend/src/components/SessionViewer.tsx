import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Zap, 
  Heart, 
  Clock, 
  Map as MapIcon, 
  TrendingUp, 
  MessageSquare,
  Info,
  Calendar,
  Thermometer,
  RotateCw,
  Trophy
} from 'lucide-react';
import { useFileSystem } from '../context/FileSystemContext';
import type { ReportFile, ReportDirectory } from '../services/fs';
import styles from './SessionViewer.module.css';

interface SessionViewerProps {
  file: ReportFile;
  onNavigate?: (file: ReportFile) => void;
}

// Data Interfaces matching the Python models
interface PeakPowerEntry {
  label: string;
  watts: number;
  pct_ftp: number | null;
  w_kg: number | null;
  is_pr: boolean;
  improvement_watts: number | null;
  previous_best: number | null;
}

interface LapData {
  lap_number: number;
  timer_time_s: number;
  elapsed_time_s: number;
  paused_time_s: number;
  avg_power: number | null;
  normalized_power: number | null;
  total_work_kj: number | null;
  target_power_low: number | null;
  target_power_high: number | null;
  target_interpretation: string;
  avg_hr: number | null;
  max_hr: number | null;
  avg_cadence: number | null;
  avg_temp: number | null;
  distance_m: number | null;
}

interface ZoneData {
  name: string;
  lower_pct: number;
  upper_pct: number;
  seconds: number;
  percent: number;
}

interface WorkInterval {
  lap_number: number;
  avg_power: number;
  target_low: number;
  target_high: number;
  deviation_watts: number;
  deviation_pct: number;
  in_target: boolean;
  timer_time_s: number;
  avg_hr: number | null;
  ef: number | null;
}

interface SessionData {
  metadata: {
    source_fit: string;
    date: string;
    venue: string;
    sport: string;
    sub_sport: string | null;
  };
  historical_context: {
    ftp: number;
    weight: number;
  };
  stats: {
    elapsed_duration_s: number;
    timer_duration_s: number;
    paused_duration_s: number;
    distance_m: number | null;
    calories: number | null;
    total_work_kj: number | null;
    ascent_m: number | null;
    avg_temp: number | null;
    avg_cadence: number | null;
    max_cadence: number | null;
    avg_speed_mps: number | null;
  };
  power: {
    avg_power: number;
    max_power: number;
    normalized_power: number;
    variability_index: number;
    intensity_factor: number;
    tss: number;
    avg_w_kg: number | null;
    np_w_kg: number | null;
  };
  hr: {
    avg_hr: number | null;
    max_hr: number | null;
    efficiency_factor: number | null;
    aerobic_decoupling_pct: number | null;
    aerobic_decoupling_interpretation: string | null;
    zones: Record<string, number> | null;
  };
  pedaling?: {
    left_power_pct: number | null;
    right_power_pct: number | null;
    left_torque_effectiveness: number | null;
    right_torque_effectiveness: number | null;
    left_pedal_smoothness: number | null;
    right_pedal_smoothness: number | null;
  };
  peaks: PeakPowerEntry[];
  laps: LapData[];
  interval_analysis?: {
    mean_work_power: number;
    cv_pct: number;
    fade_pct: number;
    compliance_pct: number;
    mean_deviation_watts: number;
    cardiac_drift_pct: number | null;
    pwhr_drift_pct: number | null;
    work_intervals: WorkInterval[];
  };
  zones: ZoneData[];
  commentary: {
    session_type: string;
    narrative: string;
    is_muddle?: boolean;
    tss_status?: string;
  };
  enrichment: {
    athlete_comment: string | null;
  };
}

const formatDuration = (seconds: number) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${s}s`;
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

export const SessionViewer: React.FC<SessionViewerProps> = ({ file, onNavigate }) => {
  const { fsService } = useFileSystem();
  const [data, setData] = useState<SessionData | null>(null);
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
        setData(jsonParseWithInfinities(content));
        setError(null);
      } catch (err) {
        console.error("Failed to load session JSON:", err);
        setError("Could not load session data.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [file.path, fsService]);

  const handleLogLinkClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (!fsService || !rootReportDir || !onNavigate) return;
    
    e.preventDefault();
    
    // Convention: coach_log.json is in the same directory as the session JSON
    const parts = file.path.split('/');
    parts.pop(); // remove filename
    const logPath = `${parts.join('/')}/coach_log.json`;
    
    const targetFile = fsService.findFileByPath(rootReportDir, logPath);
    
    if (targetFile) {
      onNavigate(targetFile);
    } else {
      console.warn("Could not find coach log at convention path:", logPath);
    }
  };

  // Helper to handle JSON with "Infinity" (which is invalid JSON but Python may produce it via json.dumps)
  const jsonParseWithInfinities = (text: string) => {
    const cleaned = text.replace(/:\s*Infinity/g, ': null').replace(/:\s*-Infinity/g, ': null').replace(/:\s*NaN/g, ': null');
    return JSON.parse(cleaned);
  };

  if (loading) return <div className={styles.loading}>Loading structured data...</div>;
  if (error || !data) return <div className={styles.error}>{error || 'No data found'}</div>;

  return (
    <div className={styles.container}>
      {/* Header Info */}
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <h1>{data.commentary.session_type} Session</h1>
          <div className={styles.metaRow}>
            <span className={styles.metaItem}><Calendar size={14} /> {data.metadata.date}</span>
            <span className={styles.metaItem}><MapIcon size={14} /> {data.metadata.venue}</span>
            <span className={styles.metaItem}><Info size={14} /> FTP: {data.historical_context.ftp}W</span>
          </div>
        </div>
        <div className={styles.tssBadge}>
          <span className={styles.tssValue}>{data.power.tss.toFixed(0)}</span>
          <span className={styles.tssLabel}>TSS</span>
        </div>
      </div>

      {/* Qualitative Link & Athlete Enrichment */}
      <div className={styles.enrichmentGrid}>
        <div className={styles.coachCard}>
          <div className={styles.cardHeader}>
            <TrendingUp size={18} className={styles.coachIcon} />
            <h2>Analysis</h2>
          </div>
          <p className={styles.logDescription}>
            Detailed qualitative analysis (Plan Compliance, Execution Quality, and Physiological Response) is available in the weekly Coach Log.
          </p>
          <a href="#" onClick={handleLogLinkClick} className={styles.logLink}>
            Open Coach Log for {data.metadata.date}
          </a>
        </div>
        
        {data.enrichment.athlete_comment && (
          <div className={styles.athleteCard}>
            <div className={styles.cardHeader}>
              <MessageSquare size={18} className={styles.athleteIcon} />
              <h2>Athlete Feedback</h2>
            </div>
            <blockquote className={styles.quote}>
              {data.enrichment.athlete_comment}
            </blockquote>
          </div>
        )}
      </div>

      {/* Main Stats Grid */}
      <div className={styles.metricsGrid}>
        <MetricCard 
          label="Normalized Power" 
          value={`${data.power.normalized_power.toFixed(0)} W`} 
          icon={<TrendingUp size={16} />} 
          subValue={`Avg: ${data.power.avg_power.toFixed(0)} W`}
        />
        <MetricCard 
          label="Intensity Factor" 
          value={data.power.intensity_factor.toFixed(3)} 
          icon={<Zap size={16} />} 
          subValue={`VI: ${data.power.variability_index.toFixed(3)}`}
        />
        <MetricCard 
          label="Duration" 
          value={formatDuration(data.stats.timer_duration_s)} 
          icon={<Clock size={16} />} 
          subValue={`Elapsed: ${formatDuration(data.stats.elapsed_duration_s)}`}
        />
        <MetricCard 
          label="Work" 
          value={`${data.stats.total_work_kj?.toFixed(0)} kJ`} 
          icon={<TrendingUp size={16} />} 
          subValue={data.stats.calories ? `${data.stats.calories} kcal` : undefined}
        />
        <MetricCard 
          label="Avg Heart Rate" 
          value={data.hr.avg_hr ? `${data.hr.avg_hr} bpm` : '—'} 
          icon={<Heart size={16} />} 
          subValue={data.hr.max_hr ? `Max: ${data.hr.max_hr} bpm` : undefined}
        />
        <MetricCard 
          label="Aerobic Efficiency" 
          value={data.hr.efficiency_factor?.toFixed(2) ?? '—'} 
          icon={<TrendingUp size={16} />} 
          subValue={data.hr.aerobic_decoupling_pct !== null ? `Drift: ${data.hr.aerobic_decoupling_pct > 0 ? '+' : ''}${data.hr.aerobic_decoupling_pct.toFixed(1)}%` : undefined}
        />
        <MetricCard 
          label="Avg Cadence" 
          value={data.stats.avg_cadence ? `${data.stats.avg_cadence.toFixed(0)} rpm` : '—'} 
          icon={<RotateCw size={16} />} 
          subValue={data.stats.max_cadence ? `Max: ${data.stats.max_cadence} rpm` : undefined}
        />
        <MetricCard 
          label="Temperature" 
          value={data.stats.avg_temp ? `${data.stats.avg_temp}°C` : '—'} 
          icon={<Thermometer size={16} />} 
        />
      </div>

      {/* Narrative Section */}
      <div className={styles.section}>
        <div className={styles.narrativeCard}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {data.commentary.narrative}
          </ReactMarkdown>
        </div>
      </div>

      {/* Power Zones */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <h2>Power Zone Distribution</h2>
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

      {/* Peak Power Durations */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <Trophy size={18} />
          <h2>Peak Power Durations</h2>
        </div>
        <div className={styles.peaksGrid}>
          {data.peaks.map(peak => (
            <div key={peak.label} className={styles.peakCard}>
              <div className={styles.peakLabel}>{peak.label}</div>
              <div className={styles.peakValue}>
                {peak.watts} <span className={styles.unit}>W</span>
                {peak.is_pr && <span className={styles.prBadge}>PR</span>}
              </div>
              <div className={styles.peakSub}>
                {peak.w_kg?.toFixed(2)} W/kg · {peak.pct_ftp?.toFixed(0)}% FTP
              </div>
              {peak.is_pr && peak.improvement_watts && (
                <div className={styles.improvement}>+{peak.improvement_watts}W improvement</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Laps Table */}
      <div className={styles.section}>
        <div className={styles.cardHeader}>
          <h2>Laps & Intervals</h2>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.lapsTable}>
            <thead>
              <tr>
                <th>Lap</th>
                <th>Time</th>
                <th>Avg Power</th>
                <th>NP</th>
                <th>Target</th>
                <th>Avg HR</th>
                <th>Cadence</th>
                <th>Distance</th>
              </tr>
            </thead>
            <tbody>
              {data.laps.map(lap => (
                <tr key={lap.lap_number}>
                  <td>{lap.lap_number}</td>
                  <td>{formatDuration(lap.timer_time_s)}</td>
                  <td>{lap.avg_power?.toFixed(0)} W</td>
                  <td>{lap.normalized_power?.toFixed(0)} W</td>
                  <td className={lap.target_interpretation.includes('✓') ? styles.targetCheck : ''}>
                    {lap.target_interpretation}
                  </td>
                  <td>{lap.avg_hr ?? '—'}</td>
                  <td>{lap.avg_cadence?.toFixed(0) ?? '—'}</td>
                  <td>{formatDist(lap.distance_m)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
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
