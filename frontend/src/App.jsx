import React, { useState, useEffect, useRef } from 'react';
import { Activity, Download, FileText, CheckCircle, AlertCircle, Trash2, File, Loader2 } from 'lucide-react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import FileUpload from './components/FileUpload';
import ResultsTable from './components/ResultsTable';

// Configure Axios base URL
const API_BASE_URL = import.meta.env.DEV ? 'http://localhost:8000' : '';

function App() {
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingState, setProcessingState] = useState({ status: 'idle', progress: 0, step: '' });
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  // Default filename: YYYYMMDD-extracted-invoice.xlsx
  const getTodayStr = () => {
    const date = new Date();
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}${month}${day}`;
  };

  const [downloadFilename, setDownloadFilename] = useState(`${getTodayStr()}-extracted-invoice.xlsx`);

  const pollingInterval = useRef(null);

  const handleFilesSelected = (selectedFiles) => {
    setFiles(prev => [...prev, ...selectedFiles]);
    setResults(null);
    setError(null);
    setSummary(null);
    setProcessingState({ status: 'idle', progress: 0, step: '' });
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearQueue = () => {
    setFiles([]);
    setResults(null);
    setError(null);
    setSummary(null);
    setProcessingState({ status: 'idle', progress: 0, step: '' });
  };

  const pollStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/status`);
      const state = response.data;

      setProcessingState(state);

      // 实时更新：如果有处理中的文件，立即显示结果
      if (state.result && state.result.length > 0) {
        setResults(state.result);
      }

      // 实时更新统计信息
      if (state.summary) {
        setSummary(state.summary);
      }

      if (state.status === 'completed') {
        // 处理完成，确保使用最终结果
        setResults(state.result || []);
        setSummary(state.summary || { totalFiles: 0, successfulFiles: 0, failedFiles: 0 });
        setIsProcessing(false);
        clearInterval(pollingInterval.current);
      } else if (state.status === 'error') {
        setError(state.error || 'An error occurred during processing.');
        setIsProcessing(false);
        clearInterval(pollingInterval.current);
      }
    } catch (err) {
      console.error("Polling error", err);
      // Don't stop polling on transient network errors, but maybe count them?
    }
  };

  const processFiles = async () => {
    if (files.length === 0) return;

    setIsProcessing(true);
    setError(null);
    setProcessingState({ status: 'starting', progress: 0, step: 'Initializing...' });

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      // 1. Start Processing
      await axios.post(`${API_BASE_URL}/api/process`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // 2. Start Polling
      pollingInterval.current = setInterval(pollStatus, 1000);

    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'Failed to start processing.');
      setIsProcessing(false);
    }
  };

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval.current) clearInterval(pollingInterval.current);
    };
  }, []);

  const downloadResults = () => {
    // Encode filename to handle spaces/special chars
    const encodedFilename = encodeURIComponent(downloadFilename);
    window.location.href = `${API_BASE_URL}/api/download?filename=${encodedFilename}`;
  };

  const openTemplate = () => {
    // Open template file in new window
    window.open(`${API_BASE_URL}/api/template`, '_blank');
  };

  // Calculate total amount from results if available
  const totalAmount = results
    ? results.reduce((sum, row) => sum + (row.total_amount || 0), 0)
    : 0;

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div>
          <h1 className="sidebar-title">Invoice Assistant</h1>
          <p className="sidebar-subtitle">Batch Import PDF</p>
        </div>

        <FileUpload onFilesSelected={handleFilesSelected} disabled={isProcessing} />

        <div className="file-list">
          <AnimatePresence>
            {files.map((file, index) => (
              <motion.div
                key={`${file.name}-${index}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="file-item"
              >
                <File size={16} className="file-icon" />
                <div className="file-info">
                  <p className="file-name" title={file.name}>{file.name}</p>
                  <p className="file-size">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-text-secondary hover:text-accent-error transition-colors"
                  disabled={isProcessing}
                >
                  <Trash2 size={14} />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        <div style={{ marginTop: 'auto' }}>
          <div className="flex justify-between items-center mb-2">
            <div className="text-xs text-text-secondary">
              <span>Total Files: {files.length}</span>
            </div>
            {files.length > 0 && (
              <button
                onClick={clearQueue}
                className="text-xs text-text-secondary hover:text-white transition-colors flex items-center gap-1"
                disabled={isProcessing}
                style={{ opacity: 0.7 }}
              >
                <Trash2 size={12} />
                <span>Clear Queue</span>
              </button>
            )}
          </div>

          {isProcessing && (
            <div style={{ marginBottom: 16 }}>
              <div className="flex justify-between text-xs text-white mb-1">
                <span>{processingState.step}</span>
                <span>{processingState.progress}%</span>
              </div>
              <div style={{ height: 4, background: 'rgba(255,255,255,0.1)', borderRadius: 2, overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${processingState.progress}%` }}
                  transition={{ duration: 0.5 }}
                  style={{ height: '100%', background: '#ff2d55' }}
                />
              </div>
            </div>
          )}

          <button
            onClick={processFiles}
            disabled={files.length === 0 || isProcessing}
            className="action-btn"
          >
            {isProcessing ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Activity size={18} />
                <span>Execute Extraction</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content" style={{ position: 'relative' }}>
        {/* Watermark */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0, // Cover entire main content area
          overflow: 'hidden',
          pointerEvents: 'none',
          userSelect: 'none',
          zIndex: 0
        }}>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            transform: 'rotate(-20deg) scale(1.8)',
            opacity: 0.15, // Much more visible
            color: '#404040', // Even lighter, more contrast with black background
            fontSize: 22,
            fontWeight: 'bold',
            gap: '50px 90px',
            padding: 80,
            width: '150%',
            height: '150%',
            position: 'absolute',
            top: '-25%',
            left: '-25%'
          }}>
            {Array.from({ length: 150 }).map((_, i) => (
              <span key={i}>90E75D</span>
            ))}
          </div>
        </div>

        <div className="main-header flex justify-between items-end" style={{ position: 'relative', zIndex: 1 }}>
          <div>
            <h2 className="main-title">Data Extraction Results</h2>
            <p className="main-subtitle">Structured data extracted from PDF files</p>
          </div>
          {/* Removed old download button */}
        </div>
        {/* Summary Cards */}
        <div className="summary-grid">
          <div className="summary-card">
            <span className="summary-value">{summary?.totalFiles || 0}</span>
            <span className="summary-label">Total</span>
          </div>
          <div className="summary-card">
            <span className="summary-value green">{summary?.successfulFiles || 0}</span>
            <span className="summary-label">Success</span>
          </div>
          <div className="summary-card">
            <span className="summary-value red">{summary?.failedFiles || 0}</span>
            <span className="summary-label">Fail</span>
          </div>
          <div className="summary-card" style={{ display: 'flex', flexDirection: 'column', gap: 12, justifyContent: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center' }}>
              <button
                onClick={openTemplate}
                style={{
                  background: 'rgba(48, 209, 88, 0.2)',
                  color: '#30d158',
                  border: '1px solid rgba(48, 209, 88, 0.3)',
                  borderRadius: 4,
                  padding: '6px 10px',
                  fontSize: 10,
                  fontWeight: 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 4,
                  transition: 'all 0.2s',
                  width: '100%'
                }}
              >
                <FileText size={12} />
                View Template
              </button>
              <span style={{ fontSize: 9, color: '#86868b', textAlign: 'center' }}>
                Template: 导出模板.xlsx
              </span>
            </div>
            <button
              onClick={downloadResults}
              disabled={!results}
              style={{
                background: results ? '#ff2d55' : 'rgba(255, 45, 85, 0.2)',
                color: '#fff',
                border: 'none',
                borderRadius: 4,
                padding: '8px 12px',
                fontSize: 12,
                fontWeight: 600,
                cursor: results ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 6,
                transition: 'all 0.2s'
              }}
            >
              <Download size={14} />
              Download
            </button>
          </div>
        </div>

        {/* Error Display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="error-banner mb-6"
            >
              <AlertCircle className="shrink-0" />
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Table */}
        <div className="glass-panel" style={{ padding: 0, overflow: 'hidden', background: '#1c1c1e' }}>
          <ResultsTable data={results} />
        </div>
      </main>
    </div>
  );
}

export default App;
