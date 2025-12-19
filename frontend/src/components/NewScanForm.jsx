import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const NewScanForm = () => {
    const [url, setUrl] = useState('');
    const [scanType, setScanType] = useState('API');
    const [reportFormat, setReportFormat] = useState('JSON');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/scan`, {
                target_url: url,
                scan_type: scanType,
                report_format: reportFormat
            });
            navigate(`/scan/${response.data.id}`);
        } catch (error) {
            console.error("Scan failed to start", error);
            alert("Failed to start scan");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-xl mx-auto mt-12 mb-12">
            <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Start New Security Scan</h2>
                <p className="text-slate-500 mt-2">Enter the target details below to begin the automated analysis.</p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">Target URL</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="text-slate-400 text-sm">https://</span>
                            </div>
                            <input
                                type="text"
                                required
                                className="input-field pl-16 font-mono text-sm"
                                placeholder="api.example.com"
                                value={url.replace(/^https?:\/\//, '')}
                                onChange={(e) => setUrl(e.target.value)}
                            />
                        </div>
                        <p className="text-xs text-slate-400 mt-1">Refrain from scanning targets you do not own.</p>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">Scan Type</label>
                        <div className="grid grid-cols-2 gap-4">
                            <button
                                type="button"
                                onClick={() => setScanType('API')}
                                className={`px-4 py-3 rounded-lg border text-sm font-medium transition-all text-left ${scanType === 'API' ? 'border-indigo-600 bg-indigo-50 text-indigo-700 ring-1 ring-indigo-600' : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'}`}
                            >
                                <div className="font-bold mb-1">API Scan</div>
                                <div className="text-xs opacity-80 font-normal">For REST/GraphQL endpoints</div>
                            </button>
                            <button
                                type="button"
                                onClick={() => setScanType('WEB')}
                                className={`px-4 py-3 rounded-lg border text-sm font-medium transition-all text-left ${scanType === 'WEB' ? 'border-indigo-600 bg-indigo-50 text-indigo-700 ring-1 ring-indigo-600' : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'}`}
                            >
                                <div className="font-bold mb-1">Web App Scan</div>
                                <div className="text-xs opacity-80 font-normal">For SPAs and Multi-page apps</div>
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">Report Format</label>
                        <select
                            value={reportFormat}
                            onChange={(e) => setReportFormat(e.target.value)}
                            className="input-field appearance-none bg-slate-50 text-slate-900"
                        >
                            <option value="JSON">JSON (Standard)</option>
                            <option value="SARIF">SARIF (GitHub Security)</option>
                            <option value="OCSF">OCSF (Open Schema)</option>
                        </select>
                    </div>

                    <div className="pt-2">
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full btn-primary py-3 text-base shadow-indigo-500/20 shadow-lg disabled:shadow-none bg-slate-900 hover:bg-slate-800 text-white"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="animate-spin h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Initializing Scan...
                                </span>
                            ) : 'Launch Scan'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default NewScanForm;
