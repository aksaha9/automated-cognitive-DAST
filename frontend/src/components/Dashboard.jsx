import { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

const MetricCard = ({ title, value, subtext, trend }) => (
    <div className="bg-white p-4 rounded border border-slate-200 shadow-sm">
        <div className="flex justify-between items-start mb-2">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</h3>
            {trend && <span className={`text-xs font-bold ${trend > 0 ? 'text-emerald-600' : 'text-slate-400'}`}>{trend > 0 ? '+' : ''}{trend}%</span>}
        </div>
        <div className="text-2xl font-bold text-slate-900">{value}</div>
        {subtext && <div className="text-xs text-slate-400 mt-1">{subtext}</div>}
    </div>
);

const Dashboard = () => {
    const [scans, setScans] = useState([]);

    useEffect(() => {
        const fetchScans = async () => {
            try {
                const response = await axios.get(`${import.meta.env.VITE_API_URL || ''}/api/scans`);
                setScans(response.data);
            } catch (error) {
                console.error("Failed to fetch scans", error);
            }
        };

        fetchScans();
        const interval = setInterval(fetchScans, 5000);
        return () => clearInterval(interval);
    }, []);

    const getStatusBadge = (state) => {
        const styles = {
            COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
            RUNNING: 'bg-blue-50 text-blue-700 border-blue-200',
            FAILED: 'bg-rose-50 text-rose-700 border-rose-200',
            PENDING: 'bg-slate-50 text-slate-600 border-slate-200',
        };
        const style = styles[state] || styles.PENDING;
        return (
            <span className={`px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide rounded border ${style}`}>
                {state}
            </span>
        );
    };

    const stats = {
        total: scans.length,
        active: scans.filter(s => s.state === 'RUNNING').length,
        completed: scans.filter(s => s.state === 'COMPLETED').length,
        failed: scans.filter(s => s.state === 'FAILED').length
    };

    return (
        <div className="space-y-6">
            {/* Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard title="Total Scans" value={stats.total} subtext="All time" trend={12} />
                <MetricCard title="Active Scans" value={stats.active} subtext="Currently running" />
                <MetricCard title="Vulnerabilities" value="-" subtext="Detected issues" />
                <MetricCard title="Security Score" value="A+" subtext="Overall posture" />
            </div>

            <div className="flex justify-between items-end">
                <h2 className="text-lg font-bold text-slate-800">Recent Activity</h2>
                <Link to="/new" className="bg-indigo-600 text-white text-xs font-bold uppercase px-4 py-2 rounded hover:bg-indigo-700 transition">
                    New Scan
                </Link>
            </div>

            <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200">
                        <thead className="bg-slate-50">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider w-24">ID</th>
                                <th className="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Target</th>
                                <th className="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider w-32">Status</th>
                                <th className="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider w-40">Progress</th>
                                <th className="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider w-48">Date</th>
                                <th className="px-4 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider w-20"></th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-slate-200">
                            {scans.map((scan) => (
                                <tr key={scan.id} className="hover:bg-slate-50 transition-colors group">
                                    <td className="px-4 py-2 whitespace-nowrap text-xs font-mono text-slate-500">
                                        {scan.id.slice(0, 8)}
                                    </td>
                                    <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-slate-900">
                                        <div className="flex items-center gap-2">
                                            {scan.target_url}
                                            <a href={scan.target_url} target="_blank" rel="noreferrer" className="text-slate-300 hover:text-indigo-500">
                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                                            </a>
                                        </div>
                                    </td>
                                    <td className="px-4 py-2 whitespace-nowrap">
                                        {getStatusBadge(scan.state)}
                                    </td>
                                    <td className="px-4 py-2 whitespace-nowrap text-xs text-slate-500">
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-slate-100 rounded-full h-1.5 min-w-[60px]">
                                                <div className={`h-1.5 rounded-full ${scan.state === 'FAILED' ? 'bg-rose-500' : 'bg-indigo-600'}`} style={{ width: `${scan.progress}%` }}></div>
                                            </div>
                                            <span className="font-mono w-8 text-right">{scan.progress}%</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-2 whitespace-nowrap text-xs text-slate-500">
                                        {new Date(scan.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-4 py-2 whitespace-nowrap text-right text-xs font-medium">
                                        <Link to={`/scan/${scan.id}`} className="text-indigo-600 hover:text-indigo-900 opacity-0 group-hover:opacity-100 transition-opacity">
                                            Details &rarr;
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                            {scans.length === 0 && (
                                <tr>
                                    <td colSpan="6" className="px-6 py-8 text-center text-sm text-slate-500">
                                        No scans found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
