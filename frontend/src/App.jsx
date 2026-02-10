import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { Database, Upload, GitCompare, Award, LayoutDashboard } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import UploadPage from './pages/UploadPage';
import MatchReview from './pages/MatchReview';
import GoldenRecords from './pages/GoldenRecords';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/upload', icon: Upload, label: 'Upload Data' },
  { path: '/matches', icon: GitCompare, label: 'Review Matches' },
  { path: '/golden-records', icon: Award, label: 'Golden Records' },
];

export default function App() {
  const location = useLocation();

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1><span>U</span>nify</h1>
          <p>Master Data Management</p>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(({ path, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              end={path === '/'}
            >
              <Icon />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/matches" element={<MatchReview />} />
          <Route path="/golden-records" element={<GoldenRecords />} />
        </Routes>
      </main>
    </div>
  );
}
