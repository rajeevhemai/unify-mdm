import { useState, useEffect } from 'react';
import {
  Award,
  Download,
  Search,
  ChevronDown,
  Database,
  FileSpreadsheet,
} from 'lucide-react';
import {
  listGoldenRecords,
  exportGoldenRecords,
  promoteUnmatched,
  getGoldenRecordCount,
} from '../services/api';

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

export default function GoldenRecords() {
  const [records, setRecords] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadRecords();
  }, [search]);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const [res, countRes] = await Promise.all([
        listGoldenRecords(0, 100, search),
        getGoldenRecordCount(),
      ]);
      setRecords(res.data);
      setTotalCount(countRes.data.count);
    } catch (err) {
      console.error('Failed to load golden records:', err);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleExport = async () => {
    try {
      const res = await exportGoldenRecords();
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'golden_records_export.csv';
      a.click();
      window.URL.revokeObjectURL(url);
      showToast('Export downloaded!');
    } catch (err) {
      showToast('Export failed', 'error');
    }
  };

  const handlePromoteUnmatched = async () => {
    try {
      const res = await promoteUnmatched();
      showToast(`Promoted ${res.data.count} records to golden records`);
      loadRecords();
    } catch (err) {
      showToast('Promotion failed', 'error');
    }
  };

  let searchTimeout;
  const handleSearchChange = (e) => {
    clearTimeout(searchTimeout);
    const val = e.target.value;
    searchTimeout = setTimeout(() => setSearch(val), 300);
  };

  return (
    <div>
      <div className="page-header">
        <h2>Golden Records</h2>
        <p>Your single source of truth — {totalCount} canonical records</p>
      </div>

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      {/* Actions Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search records..."
            onChange={handleSearchChange}
          />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-outline btn-sm" onClick={handlePromoteUnmatched}>
            <Database size={16} />
            Promote Unmatched
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleExport}>
            <Download size={16} />
            Export CSV
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner"><div className="spinner" /></div>
      ) : records.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <Award size={48} />
            <h3>No golden records yet</h3>
            <p>Merge matched records or promote unmatched records to create golden records</p>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Contact</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Location</th>
                  <th>Sources</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <>
                    <tr
                      key={record.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setExpandedId(expandedId === record.id ? null : record.id)}
                    >
                      <td style={{ fontWeight: 600 }}>{record.company_name || '—'}</td>
                      <td>{[record.first_name, record.last_name].filter(Boolean).join(' ') || '—'}</td>
                      <td>{record.email || '—'}</td>
                      <td>{record.phone || '—'}</td>
                      <td>{[record.city, record.country].filter(Boolean).join(', ') || '—'}</td>
                      <td>
                        <span className="badge badge-merged">{record.source_count} source{record.source_count !== 1 ? 's' : ''}</span>
                      </td>
                      <td>
                        <ChevronDown
                          size={16}
                          style={{
                            transform: expandedId === record.id ? 'rotate(180deg)' : 'rotate(0)',
                            transition: 'transform 0.2s',
                            color: 'var(--gray-400)',
                          }}
                        />
                      </td>
                    </tr>
                    {expandedId === record.id && (
                      <tr key={`${record.id}-detail`}>
                        <td colSpan={7} style={{ padding: '16px 20px', background: 'var(--gray-50)' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                            {/* All Fields */}
                            <div>
                              <h4 style={{ fontSize: 13, fontWeight: 600, color: 'var(--gray-500)', marginBottom: 12, textTransform: 'uppercase' }}>
                                Golden Record Details
                              </h4>
                              {CUSTOMER_FIELDS.map(({ key, label }) => (
                                <div key={key} className="match-field">
                                  <span className="match-field-label">{label}</span>
                                  <span className="match-field-value">
                                    {record[key] || <span style={{ color: 'var(--gray-400)' }}>—</span>}
                                  </span>
                                </div>
                              ))}
                            </div>
                            {/* Source Records */}
                            <div>
                              <h4 style={{ fontSize: 13, fontWeight: 600, color: 'var(--gray-500)', marginBottom: 12, textTransform: 'uppercase' }}>
                                Source Records ({record.source_records?.length || 0})
                              </h4>
                              {record.source_records?.map((sr, i) => (
                                <div key={sr.id} style={{
                                  padding: 12,
                                  background: 'white',
                                  borderRadius: 'var(--radius)',
                                  border: '1px solid var(--gray-200)',
                                  marginBottom: 8,
                                }}>
                                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
                                    {sr.company_name || sr.email || `Record ${i + 1}`}
                                  </div>
                                  <div style={{ fontSize: 12, color: 'var(--gray-500)' }}>
                                    {sr.first_name} {sr.last_name} • {sr.email}
                                  </div>
                                  <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 4 }}>
                                    Source: {sr.source_id?.slice(0, 8)}... • Row #{sr.source_row_number}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
