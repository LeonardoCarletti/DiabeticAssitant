import { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import { setToken, getToken } from './lib/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('da_token');
    const uid = localStorage.getItem('da_user_id');
    if (token) {
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
  };

  const handleLogout = () => {
    localStorage.removeItem('da_token');
    localStorage.removeItem('da_user_id');
    setIsAuthenticated(false);
    setUserId(null);
  };

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return <DashboardPage userId={userId || ''} onLogout={handleLogout} />;
}
