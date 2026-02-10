import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Database,
  Upload,
  GitCompare,
  Award,
  AlertCircle,
  CheckCircle,
  XCircle,
  TrendingUp,
} from 'lucide-react';
import { getDashboardStats, getMatchStats, listSources } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [matchStats, setMatchStats] = useState(null);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, matchRes, sourcesRes] = await Promise.all([
        getDashboardStats(),
        getMatchStats(),
        listSources(),
      ]);
      setStats(statsRes.data);
      setMatchStats(matchRes.data);
      setSources(sourcesRes.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Overview of your master data management</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon primary">
            <Database size={20} />
          </div>
          <div className="stat-label">Data Sources</div>
          <div className="stat-value">{stats?.total_sources || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon primary">
            <Upload size={20} />
          </div>
          <div className="stat-label">Total Records</div>
          <div className="stat-value">{stats?.total_records || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon warning">
            <AlertCircle size={20} />
          </div>
          <div className="stat-label">Pending Matches</div>
          <div className="stat-value">{stats?.total_matches_pending || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon success">
            <Award size={20} />
          </div>
          <div className="stat-label">Golden Records</div>
          <div className="stat-value">{stats?.total_golden_records || 0}</div>
        </div>
      </div>

      {/* Second Row Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon success">
            <CheckCircle size={20} />
          </div>
          <div className="stat-label">Approved Matches</div>
          <div className="stat-value">{matchStats?.approved || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon danger">
            <XCircle size={20} />
          </div>
          <div className="stat-label">Rejected Matches</div>
          <div className="stat-value">{matchStats?.rejected || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon primary">
            <GitCompare size={20} />
          </div>
          <div className="stat-label">Merged</div>
          <div className="stat-value">{matchStats?.merged || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon warning">
            <TrendingUp size={20} />
          </div>
          <div className="stat-label">Duplicate Rate</div>
          <div className="stat-value">{stats?.duplicate_rate || 0}%</div>
        </div>
      </div>

      {/* Recent Sources */}
      <div className="card" style={{ marginTop: 8 }}>
        <div className="card-header">
          <h3>Recent Data Sources</h3>
          <Link to="/upload" className="btn btn-primary btn-sm">
            <Upload size={16} />
            Upload New
          </Link>
        </div>
        {sources.length === 0 ? (
          <div className="empty-state">
            <Database size={48} />
            <h3>No data sources yet</h3>
            <p>Upload your first CSV or Excel file to get started</p>
            <Link to="/upload" className="btn btn-primary">
              Upload Data
            </Link>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>File</th>
                  <th>Records</th>
                  <th>Status</th>
                  <th>Uploaded</th>
                </tr>
              </thead>
              <tbody>
                {sources.slice(0, 5).map((source) => (
                  <tr key={source.id}>
                    <td style={{ fontWeight: 500 }}>{source.name}</td>
                    <td>{source.file_name}</td>
                    <td>{source.record_count}</td>
                    <td>
                      <span className={`badge badge-${source.status === 'processed' ? 'approved' : 'pending'}`}>
                        {source.status}
                      </span>
                    </td>
                    <td>{new Date(source.uploaded_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
