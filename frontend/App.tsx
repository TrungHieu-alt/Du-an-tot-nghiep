import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes, useLocation } from 'react-router-dom';

import Header from './components/Header';
import Footer from './components/Footer';
import { AuthProvider } from './contexts/AuthContext';
import { ErrorToastProvider } from './contexts/ErrorToastContext';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import V2CvDetail from './pages/V2CvDetail';
import V2JobDetail from './pages/V2JobDetail';
import V2Matching from './pages/V2Matching';
import V2Search from './pages/V2Search';

export const AppRoutes: React.FC = () => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 font-sans">
      {!isAuthPage && <Header />}
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/v2/search" element={<V2Search />} />
          <Route path="/v2/jobs/:id" element={<V2JobDetail />} />
          <Route path="/v2/cvs/:id" element={<V2CvDetail />} />
          <Route path="/v2/matching" element={<V2Matching />} />
          <Route path="*" element={<Navigate to="/v2/search" replace />} />
        </Routes>
      </main>
      {!isAuthPage && <Footer />}
    </div>
  );
};

const App: React.FC = () => (
  <ErrorToastProvider>
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  </ErrorToastProvider>
);

export default App;
