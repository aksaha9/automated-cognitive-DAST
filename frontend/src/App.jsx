import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import NewScanForm from './components/NewScanForm';
import ResultsView from './components/ResultsView';

const NavLink = ({ to, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link
      to={to}
      className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive
          ? 'bg-slate-800 text-white'
          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
        }`}
    >
      {children}
    </Link>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-100 font-sans text-slate-900">
        <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
          <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex h-14 items-center justify-between">
              <div className="flex items-center gap-8">
                <Link to="/" className="flex flex-shrink-0 items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded bg-indigo-500 text-white font-bold text-lg">C</div>
                  <span className="font-semibold text-lg text-white tracking-tight">Cognitive DAST</span>
                </Link>
                <div className="hidden sm:flex sm:space-x-1">
                  <NavLink to="/">Dashboard</NavLink>
                  <NavLink to="/new">New Scan</NavLink>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="hidden md:block text-right">
                  <div className="text-xs font-medium text-white">Admin User</div>
                  <div className="text-[10px] text-slate-400">SecOps Team</div>
                </div>
                <div className="h-8 w-8 rounded bg-slate-700 border border-slate-600"></div>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new" element={<NewScanForm />} />
            <Route path="/scan/:id" element={<ResultsView />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
