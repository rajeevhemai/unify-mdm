import { useState, useEffect } from 'react';
import {
  GitCompare,
  Check,
  X,
  Merge,
  ChevronDown,
  Filter,
} from 'lucide-react';
import { listMatches, reviewMatch, mergeRecords } from '../services/api';

const CUSTOMER_FIELDS = [
  { key: 'company_name', label: 'Company' },
  { key: 'first_name', label: 'First Name' },
  { key: 'last_name', label: 'Last Name' },
  { key: 'email', label: 'Email' },
  { key: 'phone', label: 'Phone' },
  { key: 'address_line1', label: 'Address' },
  { key: 'city', label: 'City' },
  { key: 'state', label: 'State' },
  { key: 'postal_code', label: 'Postal Code' },
  { key: 'country', label: 'Country' },
  { key: 'tax_id', label: 'Tax ID' },
  { key: 'website', label: 'Website' },
];

function ScoreBar({ score }) {
  const pct = Math.round(score * 100);
  const cls = pct >= 85 ? 'high' : pct >= 65 ? 'medium' : 'low';
  return (
    <div className="score-bar">
      <div className="score-bar-track">
        <div className={`score-bar-fill ${cls}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="score-label">{pct}%</span>
    </div>
  );
}

function FieldScore({ score }) {
  if (score === undefined || score === null) return <span style={{ color: 'var(--gray-400)' }}>—</span>;
  const pct = Math.round(score * 100);
  const color = pct >= 85 ? 'var(--success)' : pct >= 65 ? 'var(--warning)' : 'var(--danger)';
  return <span style={{ fontSize: 12, fontWeight: 600, color }}>{pct}%</span>;
}

export default function MatchReview() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');
  const [expandedId, setExpandedId] = useState(null);
  const [mergeState, setMergeState] = useState({});
  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadMatches();
  }, [filter]);

  const loadMatches = async () => {
    setLoading(true);
    try {
      const res = await listMatches(filter || undefined);
      setMatches(res.data);
    } catch (err) {
      console.error('Failed to load matches:', err);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleReview = async (matchId, status) => {
    try {
      await reviewMatch(matchId, status);
      showToast(`Match ${status}`);
      loadMatches();
    } catch (err) {
      showToast('Action failed', 'error');
    }
  };

  const handleMerge = async (match) => {
    // Build surviving values from merge selections
    const values = {};
    CUSTOMER_FIELDS.forEach(({ key }) => {
      const sel = mergeState[key];
      if (sel === 'a') {
        values[key] = match.record_a?.[key] || '';
      } else if (sel === 'b') {
        values[key] = match.record_b?.[key] || '';
      } else {
        // Auto: pick the longer/non-empty value
        const a = match.record_a?.[key] || '';
        const b = match.record_b?.[key] || '';
        values[key] = a.length >= b.length ? a : b;
      }
    });

    try {
      await mergeRecords(match.id, values);
      showToast('Records merged into golden record!');
      setExpandedId(null);
      setMergeState({});
      loadMatches();
    } catch (err) {
      showToast('Merge failed', 'error');
    }
  };

  const toggleExpand = (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      setMergeState({});
    } else {
      setExpandedId(id);
      setMergeState({});
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Review Matches</h2>
        <p>Approve, reject, or merge duplicate candidates</p>
      </div>

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {[
          { value: 'pending', label: 'Pending' },
          { value: 'approved', label: 'Approved' },
          { value: 'rejected', label: 'Rejected' },
          { value: 'merged', label: 'Merged' },
          { value: '', label: 'All' },
        ].map((f) => (
          <button
            key={f.value}
            className={`btn btn-sm ${filter === f.value ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-spinner"><div className="spinner" /></div>
      ) : matches.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <GitCompare size={48} />
            <h3>No {filter || ''} matches found</h3>
            <p>Upload data and run matching to find duplicates</p>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {matches.map((match) => (
            <div key={match.id} className="card" style={{ padding: 0 }}>
              {/* Match Summary Row */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 120px 100px 140px',
                  gap: 16,
                  padding: '16px 20px',
                  cursor: 'pointer',
                  alignItems: 'center',
                }}
                onClick={() => toggleExpand(match.id)}
              >
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>
                    {match.record_a?.company_name || match.record_a?.email || 'Record A'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--gray-500)' }}>
                    {match.record_a?.first_name} {match.record_a?.last_name}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>
                    {match.record_b?.company_name || match.record_b?.email || 'Record B'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--gray-500)' }}>
                    {match.record_b?.first_name} {match.record_b?.last_name}
                  </div>
                </div>
                <ScoreBar score={match.overall_score} />
                <span className={`badge badge-${match.status}`}>{match.status}</span>
                <ChevronDown
                  size={18}
                  style={{
                    transform: expandedId === match.id ? 'rotate(180deg)' : 'rotate(0)',
                    transition: 'transform 0.2s',
                    justifySelf: 'end',
                    color: 'var(--gray-400)',
                  }}
                />
              </div>

              {/* Expanded Detail / Merge View */}
              {expandedId === match.id && (
                <div style={{ padding: '0 20px 20px', borderTop: '1px solid var(--gray-200)' }}>
                  {/* Field-by-field comparison */}
                  <div style={{ marginTop: 16 }}>
                    <table>
                      <thead>
                        <tr>
                          <th style={{ width: 120 }}>Field</th>
                          <th>Record A</th>
                          <th>Record B</th>
                          <th style={{ width: 60 }}>Score</th>
                          {match.status === 'pending' && <th style={{ width: 80 }}>Use</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {CUSTOMER_FIELDS.map(({ key, label }) => {
                          const valA = match.record_a?.[key] || '';
                          const valB = match.record_b?.[key] || '';
                          const score = match.field_scores?.[key];
                          const differ = valA !== valB && valA && valB;
                          return (
                            <tr key={key}>
                              <td style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)' }}>
                                {label}
                              </td>
                              <td>
                                <span
                                  className={`${match.status === 'pending' ? 'merge-value' : ''} ${mergeState[key] === 'a' ? 'selected' : ''}`}
                                  onClick={() => match.status === 'pending' && setMergeState((s) => ({ ...s, [key]: 'a' }))}
                                  style={differ ? { background: '#fef9c3' } : {}}
                                >
                                  {valA || <span style={{ color: 'var(--gray-400)' }}>—</span>}
                                </span>
                              </td>
                              <td>
                                <span
                                  className={`${match.status === 'pending' ? 'merge-value' : ''} ${mergeState[key] === 'b' ? 'selected' : ''}`}
                                  onClick={() => match.status === 'pending' && setMergeState((s) => ({ ...s, [key]: 'b' }))}
                                  style={differ ? { background: '#fef9c3' } : {}}
                                >
                                  {valB || <span style={{ color: 'var(--gray-400)' }}>—</span>}
                                </span>
                              </td>
                              <td><FieldScore score={score} /></td>
                              {match.status === 'pending' && (
                                <td style={{ fontSize: 11, color: 'var(--gray-500)' }}>
                                  {mergeState[key] === 'a' ? '← A' : mergeState[key] === 'b' ? 'B →' : 'auto'}
                                </td>
                              )}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Actions */}
                  {match.status === 'pending' && (
                    <div className="match-actions" style={{ marginTop: 16 }}>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleReview(match.id, 'rejected')}
                      >
                        <X size={16} />
                        Not a Match
                      </button>
                      <button
                        className="btn btn-success btn-sm"
                        onClick={() => handleReview(match.id, 'approved')}
                      >
                        <Check size={16} />
                        Approve
                      </button>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleMerge(match)}
                      >
                        <Merge size={16} />
                        Merge into Golden Record
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
