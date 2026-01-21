import { Link, useLocation } from 'react-router-dom';
import { FolderKanban, Settings, Inbox, LayoutDashboard } from 'lucide-react';
import clsx from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const navLinks = [
    { to: '/', label: 'Projects', icon: LayoutDashboard },
    { to: '/intake', label: 'Intake Inbox', icon: Inbox },
  ];

  return (
    <div className="min-h-screen">
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2 text-xl font-bold text-indigo-600">
                <FolderKanban className="w-6 h-6" />
                Auto PM
              </Link>
              <div className="flex items-center gap-1">
                {navLinks.map(({ to, label, icon: Icon }) => (
                  <Link
                    key={to}
                    to={to}
                    className={clsx(
                      'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition',
                      location.pathname === to || (to !== '/' && location.pathname.startsWith(to))
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to="/admin"
                className={clsx(
                  'flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition',
                  location.pathname === '/admin'
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                )}
              >
                <Settings className="w-4 h-4" />
                Admin
              </Link>
              <Link
                to="/projects/new"
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
              >
                New Project
              </Link>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
