import { useState, useRef, useCallback } from 'react';
import { Upload, FileSpreadsheet, ArrowRight, Check, Loader } from 'lucide-react';
import {
  uploadFile,
  previewFile,
  getAutoMapping,
  importRecords,
  runMatching,
} from '../services/api';

const STANDARD_FIELDS = [
  { value: '', label: '-- Skip this column --' },
  { value: 'company_name', label: 'Company Name' },
  { value: 'first_name', label: 'First Name' },
  { value: 'last_name', label: 'Last Name' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
  { value: 'address_line1', label: 'Address Line 1' },
  { value: 'address_line2', label: 'Address Line 2' },
  { value: 'city', label: 'City' },
  { value: 'state', label: 'State / Province' },
  { value: 'postal_code', label: 'Postal Code' },
  { value: 'country', label: 'Country' },
  { value: 'tax_id', label: 'Tax ID / VAT' },
  { value: 'website', label: 'Website' },
];

export default function UploadPage() {
  const [step, setStep] = useState(1); // 1: upload, 2: map, 3: importing, 4: done
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [source, setSource] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [loading, setLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInput = useRef(null);

  const handleFileDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
    if (droppedFile) {
      processFile(droppedFile);
    }
  }, []);

  const processFile = async (selectedFile) => {
    setFile(selectedFile);
    setLoading(true);
    setError(null);
    try {
      // Upload file
      const uploadRes = await uploadFile(selectedFile, selectedFile.name);
      const src = uploadRes.data;
      setSource(src);

      // Get preview and auto-mapping
      const [previewRes, mapRes] = await Promise.all([
        previewFile(src.id),
        getAutoMapping(src.id),
      ]);
      setPreview(previewRes.data);
      setMapping(mapRes.data.suggested_mapping || {});
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleMappingChange = (sourceCol, stdField) => {
    setMapping((prev) => {
      const updated = { ...prev };
      if (stdField) {
        updated[sourceCol] = stdField;
      } else {
        delete updated[sourceCol];
      }
      return updated;
    });
  };

  const handleImport = async () => {
    setLoading(true);
    setError(null);
    setStep(3);
    try {
      // Import records
      const importRes = await importRecords(source.id, mapping);
      setImportResult(importRes.data);

      // Run matching
      const matchRes = await runMatching(source.id);
      setMatchResult(matchRes.data);

      setStep(4);
    } catch (err) {
      setError(err.response?.data?.detail || 'Import failed');
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep(1);
    setFile(null);
    setSource(null);
    setPreview(null);
    setMapping({});
    setImportResult(null);
    setMatchResult(null);
    setError(null);
  };

  return (
    <div>
      <div className="page-header">
        <h2>Upload Data</h2>
        <p>Import customer records from CSV or Excel files</p>
      </div>

      {error && (
        <div className="toast toast-error" style={{ position: 'relative', marginBottom: 16 }}>
          {error}
          <button onClick={() => setError(null)} style={{ marginLeft: 12, background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      {/* Step 1: Upload */}
      {step === 1 && (
        <div
          className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleFileDrop}
          onClick={() => fileInput.current?.click()}
        >
          {loading ? (
            <div className="loading-spinner">
              <div className="spinner" />
            </div>
          ) : (
            <>
              <Upload size={48} />
              <h3>Drop your file here, or click to browse</h3>
              <p>Supports CSV and Excel files (up to 50MB)</p>
            </>
          )}
          <input
            ref={fileInput}
            type="file"
            accept=".csv,.xlsx,.xls"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && processFile(e.target.files[0])}
          />
        </div>
      )}

      {/* Step 2: Column Mapping */}
      {step === 2 && preview && (
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <h3>
                <FileSpreadsheet size={18} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                {file?.name} — {preview.total_rows} rows detected
              </h3>
            </div>

            {/* Preview Table */}
            <div className="table-container" style={{ marginBottom: 24 }}>
              <table>
                <thead>
                  <tr>
                    {preview.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.sample_rows.slice(0, 3).map((row, i) => (
                    <tr key={i}>
                      {preview.columns.map((col) => (
                        <td key={col}>{row[col] ?? ''}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mapping */}
          <div className="card">
            <div className="card-header">
              <h3>Map Columns</h3>
              <span style={{ fontSize: 13, color: 'var(--gray-500)' }}>
                Map your file columns to standard customer fields
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {preview.columns.map((col) => (
                <div key={col} className="mapping-grid">
                  <div className="mapping-source">{col}</div>
                  <ArrowRight className="mapping-arrow" size={20} />
                  <select
                    className="mapping-select"
                    value={mapping[col] || ''}
                    onChange={(e) => handleMappingChange(col, e.target.value)}
                  >
                    {STANDARD_FIELDS.map((f) => (
                      <option key={f.value} value={f.value}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 12, marginTop: 24, justifyContent: 'flex-end' }}>
              <button className="btn btn-outline" onClick={handleReset}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleImport}
                disabled={Object.keys(mapping).length === 0}
              >
                <Check size={16} />
                Import & Run Matching
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Importing */}
      {step === 3 && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <div className="loading-spinner" style={{ marginBottom: 16 }}>
            <div className="spinner" />
          </div>
          <h3>Importing records and running duplicate detection...</h3>
          <p style={{ color: 'var(--gray-500)', marginTop: 8 }}>This may take a moment for large files</p>
        </div>
      )}

      {/* Step 4: Done */}
      {step === 4 && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <Check size={48} style={{ color: 'var(--success)', marginBottom: 16 }} />
          <h3 style={{ fontSize: 20, marginBottom: 8 }}>Import Complete!</h3>
          <p style={{ color: 'var(--gray-500)', marginBottom: 24 }}>
            <strong>{importResult?.record_count || 0}</strong> records imported •{' '}
            <strong>{matchResult?.match_count || 0}</strong> potential duplicates found
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            <button className="btn btn-outline" onClick={handleReset}>
              Upload Another File
            </button>
            <a href="/matches" className="btn btn-primary">
              Review Matches
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
