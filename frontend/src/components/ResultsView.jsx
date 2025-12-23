import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';

const ResultsView = () => {
    const { id } = useParams();
    const [results, setResults] = useState(null);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [exportOpen, setExportOpen] = useState(false);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const statusRes = await axios.get(`${import.meta.env.VITE_API_URL || ''}/api/scan/${id}`);
                setStatus(statusRes.data);

                if (statusRes.data.state === 'COMPLETED') {
                    const res = await axios.get(`${import.meta.env.VITE_API_URL || ''}/api/scan/${id}/results`, { params: { format: 'JSON' } });
                    setResults(res.data);
                }
            } catch (error) {
                console.error("Failed to fetch results", error);
            } finally {
                setLoading(false);
            }
        };

        fetchResults();
        const interval = setInterval(() => {
            if (status && status.state !== 'COMPLETED' && status.state !== 'FAILED' && status.state !== 'STOPPED') {
                fetchResults();
            }
        }, 5000);
        return () => clearInterval(interval);

    }, [id, status?.state]);

    const handleExport = async (format) => {
        try {
            const response = await axios.get(`${import.meta.env.VITE_API_URL || ''}/api/scan/${id}/results`, {
                params: { format: format },
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            const ext = format === 'SARIF' ? 'sarif' : 'json';
            link.setAttribute('download', `scan-report-${id}.${ext}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            setExportOpen(false);
        } catch (error) {
            console.error("Download failed", error);
            alert("Export failed");
        }
    };

    const handleStop = async () => {
        if (!confirm('Are you sure you want to stop this scan?')) return;
        try {
            await axios.post(`${import.meta.env.VITE_API_URL || ''}/api/scan/${id}/stop`);
            alert('Stop signal sent');
            const res = await axios.get(`${import.meta.env.VITE_API_URL || ''}/api/scan/${id}`);
            setStatus(res.data);
        } catch (e) {
            alert('Failed to stop scan');
        }
    };

    const getRiskClass = (risk) => {
        switch (risk.toLowerCase()) {
            case 'high': return 'text-rose-600 bg-rose-50 border-rose-200';
            case 'medium': return 'text-orange-600 bg-orange-50 border-orange-200';
            case 'low': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
            case 'informational': return 'text-blue-600 bg-blue-50 border-blue-200';
            default: return 'text-slate-600 bg-slate-50 border-slate-200';
        }
    };

    if (status?.state === 'FAILED') {
        return (
            <div className="max-w-4xl mx-auto mt-12 mb-12 text-center">
                <div className="bg-red-50 text-red-700 p-8 rounded-xl border border-red-200">
                    <svg className="w-16 h-16 mx-auto mb-4 opacity-75" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                    </svg>
                    <h2 className="text-2xl font-bold mb-2">Scan Failed</h2>
                    <p className="mb-6">The security analysis encountered an unexpected error and could not complete.</p>
                    <Link
                        to="/"
                        className="inline-block bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                    >
                        Return to Dashboard
                    </Link>
                </div>
            </div>
        );
    }

    if (loading && !status) return <div className="p-10 text-center text-slate-500">Loading...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-200 pb-6">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Link to="/" className="text-slate-400 hover:text-slate-600 transition-colors">Dashboard</Link>
                        <span className="text-slate-300">/</span>
                        <span className="font-mono text-sm text-slate-500">{id}</span>
                    </div>
                    <h1 className="text-xl font-bold text-slate-900">Scan Results</h1>
                </div>
                <div className="flex gap-2 relative">
                    {status?.state === 'RUNNING' && (
                        <button
                            onClick={handleStop}
                            className="bg-white border border-rose-300 text-rose-700 px-4 py-2 rounded text-sm font-medium hover:bg-rose-50 shadow-sm flex items-center gap-2"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path></svg>
                            Stop Scan
                        </button>
                    )}
                    {status?.state === 'COMPLETED' && (
                        <div className="flex gap-2">
                            {/* Recommended Download Button */}
                            {status?.report_format && status.report_format !== 'JSON' && (
                                <button
                                    onClick={() => handleExport(status.report_format)}
                                    className="bg-indigo-600 text-white border border-transparent px-4 py-2 rounded text-sm font-medium hover:bg-indigo-700 shadow-sm flex items-center gap-2"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                                    Download {status.report_format}
                                </button>
                            )}

                            <div className="relative">
                                <button
                                    onClick={() => setExportOpen(!exportOpen)}
                                    className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded text-sm font-medium hover:bg-slate-50 shadow-sm flex items-center gap-2"
                                >
                                    {status?.report_format && status.report_format !== 'JSON' ? 'Other Formats' : 'Export Report'}
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                                </button>
                                {exportOpen && (
                                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-slate-100 z-10 py-1">
                                        <button onClick={() => handleExport('JSON')} className="block w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">JSON (Raw)</button>
                                        <button onClick={() => handleExport('SARIF')} className="block w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">SARIF (GitHub)</button>
                                        <button onClick={() => handleExport('OCSF')} className="block w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">OCSF (Schema)</button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {status?.state !== 'COMPLETED' && (
                <div className="bg-white border border-slate-200 rounded p-6 text-center">
                    {status?.state === 'STOPPED' ? (
                        <div className="text-rose-600 font-bold mb-2">Scan Terminated by User</div>
                    ) : (
                        <>
                            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900 mb-4"></div>
                            <h3 className="text-lg font-medium">Scan in Progress: {status?.progress}%</h3>
                            <p className="text-slate-500 text-sm mt-1">{status?.state} - Orchestrating ZAP Engine...</p>
                        </>
                    )}
                </div>
            )}

            {/* Summary Section */}
            {status?.state === 'COMPLETED' && results?.summary?.severity_counts && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Severity Breakdown */}
                    <div className="bg-white border border-slate-200 rounded p-6">
                        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide mb-4">Severity Breakdown</h3>
                        <div className="grid grid-cols-2 gap-4">
                            {Object.entries(results.summary.severity_counts).map(([risk, count]) => (
                                count > 0 && (
                                    <div key={risk} className={`p-4 rounded border text-center ${getRiskClass(risk)} bg-opacity-10 border-opacity-50`}>
                                        <div className="text-2xl font-bold">{count}</div>
                                        <div className="text-xs uppercase font-medium opacity-75">{risk}</div>
                                    </div>
                                )
                            ))}
                        </div>
                    </div>

                    {/* Vulnerability Types */}
                    <div className="bg-white border border-slate-200 rounded p-6">
                        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide mb-4">Top Vulnerability Types</h3>
                        <div className="space-y-3">
                            {results.summary.type_counts && Object.entries(results.summary.type_counts)
                                .sort(([, a], [, b]) => b - a)
                                .slice(0, 5)
                                .map(([type, count]) => (
                                    <div key={type} className="flex justify-between items-center text-sm border-b border-slate-100 last:border-0 pb-2 last:pb-0">
                                        <span className="text-slate-700 font-medium truncate pr-4">{type}</span>
                                        <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-xs font-bold">{count}</span>
                                    </div>
                                ))
                            }
                        </div>
                    </div>
                </div>
            )}

            {/* Vulnerability Index */}
            {status?.state === 'COMPLETED' && results && (
                <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                        <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wide">Vulnerability Index</h3>
                        <span className="text-xs text-slate-500">{results.vulnerabilities.length} findings</span>
                    </div>

                    <div className="divide-y divide-slate-100">
                        {results.vulnerabilities.length === 0 ? (
                            <div className="p-8 text-center text-slate-500">No vulnerabilities found. System secure.</div>
                        ) : (
                            results.vulnerabilities.map((vuln, idx) => {
                                const riskClass = getRiskClass(vuln.risk);
                                return (
                                    <details key={idx} className="group open:bg-slate-50/50 transition-colors">
                                        <summary className="flex items-center p-4 cursor-pointer list-none hover:bg-slate-50">
                                            <div className="w-6 h-6 mr-4 flex items-center justify-center text-slate-400 group-open:rotate-90 transition-transform">
                                                ➤
                                            </div>
                                            <div className={`w-24 text-xs font-bold uppercase text-center py-1 rounded border mr-4 ${riskClass}`}>
                                                {vuln.risk}
                                            </div>
                                            <div className="flex-1 font-medium text-slate-800 text-sm">{vuln.alert}</div>
                                            <div className="hidden md:block text-xs font-mono text-slate-400 truncate w-64 text-right">
                                                {vuln.url}
                                            </div>
                                        </summary>
                                        <div className="px-14 pb-6 pt-2 text-sm text-slate-600 space-y-4">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                <div>
                                                    <h4 className="font-bold text-slate-900 text-xs uppercase mb-2">Description</h4>
                                                    <p className="leading-relaxed bg-white p-3 rounded border border-slate-200">{vuln.description}</p>
                                                </div>
                                                <div>
                                                    <h4 className="font-bold text-slate-900 text-xs uppercase mb-2">Remediation</h4>
                                                    <p className="leading-relaxed bg-white p-3 rounded border border-slate-200">{vuln.solution}</p>
                                                </div>
                                            </div>
                                            <div>
                                                <h4 className="font-bold text-slate-900 text-xs uppercase mb-1">Affected Resource</h4>
                                                <code className="bg-slate-800 text-slate-100 px-2 py-1 rounded text-xs font-mono break-all block w-full">{vuln.url}</code>
                                            </div>
                                        </div>
                                    </details>
                                );
                            })
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ResultsView;
