import { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import WorkoutPage from './pages/WorkoutPage';
import { setToken } from './lib/api';

type Page = 'dashboard' | 'chat' | 'workout';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');

  // Restore session on mount
  useEffect(() => {
    const token = localStorage.getItem('da_token');
    const uid = localStorage.getItem('da_user_id');
    if (token && uid) {
      setToken(token);
      setIsAuthenticated(true);
      setUserId(uid);
    }
  }, []);

  const handleLogin = (token: string, uid: string) => {
    localStorage.setItem('da_token', token);
    localStorage.setItem('da_user_id', uid);
    setToken(token);
    setIsAuthenticated(true);
    setUserId(uid);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('da_token');
    localStorage.removeItem('da_user_id');
    setToken('');
    setIsAuthenticated(false);
    setUserId(null);
    setCurrentPage('dashboard');
  };

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const commonProps = {
    userId: userId ?? '',
    onNavigate: (page: Page) => setCurrentPage(page),
  };

  switch (currentPage) {
    case 'chat':
      return <ChatPage {...commonProps} />;
    case 'workout':
      return <WorkoutPage {...commonProps} />;
    default:
      return <DashboardPage {...commonProps} onLogout={handleLogout} />;
  }
}
