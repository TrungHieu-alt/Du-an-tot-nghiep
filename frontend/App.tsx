import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';

import Header from './components/Header';
import Footer from './components/Footer';
import { ErrorToastProvider } from './contexts/ErrorToastContext';
import V2CvDetail from './pages/V2CvDetail';
import V2JobDetail from './pages/V2JobDetail';
import V2Matching from './pages/V2Matching';
import V2Search from './pages/V2Search';

export const AppRoutes: React.FC = () => (
  <div className="flex min-h-screen flex-col bg-gray-50 font-sans">
    <Header />
    <main className="flex-grow">
      <Routes>
        <Route path="/" element={<Navigate to="/v2/search" replace />} />
        <Route path="/v2/search" element={<V2Search />} />
        <Route path="/v2/jobs/:id" element={<V2JobDetail />} />
        <Route path="/v2/cvs/:id" element={<V2CvDetail />} />
        <Route path="/v2/matching" element={<V2Matching />} />
        <Route path="*" element={<Navigate to="/v2/search" replace />} />
      </Routes>
    </main>
    <Footer />
  </div>
);

const App: React.FC = () => (
  <ErrorToastProvider>
    <Router>
      <AppRoutes />
    </Router>
  </ErrorToastProvider>
);

export default App;
