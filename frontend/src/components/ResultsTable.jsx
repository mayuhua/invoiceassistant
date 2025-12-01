import React from 'react';
import { FileText, CheckCircle, AlertCircle } from 'lucide-react';

const ResultsTable = ({ data }) => {
    if (!data || !Array.isArray(data) || data.length === 0) return null;

    return (
        <div className="table-container" style={{ maxHeight: 'calc(100vh - 300px)', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                    <tr>
                        <th style={{ paddingLeft: 24 }}>Source File</th>
                        <th>Invoice #</th>
                        <th>Vendor</th>
                        <th>Date</th>
                        <th style={{ textAlign: 'right' }}>Amount</th>
                        <th style={{ textAlign: 'right' }}>Tax</th>
                        <th style={{ textAlign: 'center', paddingRight: 24 }}>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, index) => {
                        const hasError = row.processing_errors && row.processing_errors.length > 0;
                        const isError = hasError && row.processing_errors !== '[]';

                        return (
                            <tr key={index}>
                                <td style={{ paddingLeft: 24 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <FileText size={16} style={{ color: '#86868b' }} />
                                        <span title={row.filename || 'Unknown'} style={{ color: '#ffffff' }}>
                                            {(row.filename && typeof row.filename === 'string')
                                                ? (row.filename.length > 30 ? '...' + row.filename.slice(-30) : row.filename)
                                                : 'Unknown file'}
                                        </span>
                                    </div>
                                </td>
                                <td style={{ color: '#ffffff' }}>{row.invoice_number || '-'}</td>
                                <td style={{ color: '#ffffff' }}>{row.vendor_name || '-'}</td>
                                <td style={{ color: '#86868b' }}>{row.invoice_date || '-'}</td>
                                <td style={{ fontFamily: 'monospace', textAlign: 'right', color: '#ffffff' }}>
                                    {row.total_amount ? `${row.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '-'}
                                </td>
                                <td style={{ fontFamily: 'monospace', textAlign: 'right', color: '#86868b' }}>
                                    {row.tax_amount ? `${row.tax_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '0.00'}
                                </td>
                                <td style={{ textAlign: 'center', paddingRight: 24 }}>
                                    {isError ? (
                                        <div style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            width: 32,
                                            height: 32,
                                            borderRadius: '50%',
                                            background: 'rgba(255, 69, 58, 0.2)',
                                            color: '#ff453a'
                                        }} title={Array.isArray(row.processing_errors) ? row.processing_errors.join(', ') : row.processing_errors || 'Failed'}>
                                            <span style={{ fontSize: 12, fontWeight: 'bold' }}>Fail</span>
                                        </div>
                                    ) : (
                                        <div style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            width: 32,
                                            height: 32,
                                            borderRadius: '50%',
                                            background: 'rgba(48, 209, 88, 0.2)',
                                            color: '#30d158'
                                        }} title="Success">
                                            <span style={{ fontSize: 12, fontWeight: 'bold' }}>OK</span>
                                        </div>
                                    )}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export default ResultsTable;
