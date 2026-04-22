
import React, { useMemo } from 'react';
import { MemoryRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Jobs from './pages/Jobs';
import JobDetail from './pages/JobDetail';
import Candidates from './pages/Candidates';
import CandidateDetail from './pages/CandidateDetail';
import CreateProfile from './pages/CreateProfile';
import ProfilePage from './pages/ProfilePage';
import { ModalProvider, useModal } from './contexts/ModalContext';
import { AuthProvider } from './contexts/AuthContext';
import CvSelectorModal from './components/CvSelectorModal';
import RequirementSelectorModal from './components/RequirementSelectorModal';
import Chatbot from './components/Chatbot';
import { MOCK_CVS } from './utils/matching';
import { MOCK_REQUIREMENTS } from './utils/matchingCandidates';
import { UserCV, JobRequirement } from './types';

// Component to handle Global Modals logic inside the Router context
const GlobalModals: React.FC = () => {
  const { isCvModalOpen, closeCvModal, isReqModalOpen, closeReqModal } = useModal();
  const navigate = useNavigate();

  // Combine static mocks with dynamic localStorage requirements
  const allRequirements = useMemo(() => {
    try {
      const storedReqs = JSON.parse(localStorage.getItem('demo_requirements') || '[]');
      return [...storedReqs, ...MOCK_REQUIREMENTS];
    } catch (e) {
      return MOCK_REQUIREMENTS;
    }
  }, [isReqModalOpen]); // Re-read when modal opens

  // Combine static mock CVs with dynamic localStorage CVs
  const allCvs = useMemo(() => {
    try {
      const storedCvs = JSON.parse(localStorage.getItem('demo_cvs') || '[]');
      return [...storedCvs, ...MOCK_CVS];
    } catch (e) {
      return MOCK_CVS;
    }
  }, [isCvModalOpen]); // Re-read when modal opens

  const handleCvSelect = (cv: UserCV) => {
    closeCvModal();
    navigate(`/jobs?cv=${cv.id}`);
  };

  const handleCvSkip = () => {
    closeCvModal();
    navigate(`/jobs?manual=true`);
  };

  const handleReqSelect = (req: JobRequirement) => {
    closeReqModal();
    navigate(`/candidates?req=${req.id}`);
  };

  const handleReqSkip = () => {
    closeReqModal();
    // Navigate to manual mode with default sort 'newest'
    navigate('/candidates?manual=true&sort=newest');
  };

  return (
    <>
      <CvSelectorModal
        isOpen={isCvModalOpen}
        onClose={closeCvModal}
        onSelectCv={handleCvSelect}
        onSkip={handleCvSkip}
        cvs={allCvs}
      />
      <RequirementSelectorModal
        isOpen={isReqModalOpen}
        onClose={closeReqModal}
        onSelectReq={handleReqSelect}
        onSkip={handleReqSkip}
        requirements={allRequirements}
      />
    </>
  );
};

// Wrapper component to handle layout logic (hiding header/footer on auth pages)
const Layout: React.FC = () => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  return (
    <div className="flex flex-col min-h-screen bg-gray-50 font-sans relative">
      {/* Header is hidden on auth pages */}
      {!isAuthPage && <Header />}
      
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
          <Route path="/candidates" element={<Candidates />} />
          <Route path="/candidates/:id" element={<CandidateDetail />} />
          <Route path="/create-profile" element={<CreateProfile />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </main>

      {!isAuthPage && <Footer />}
      
      {/* Render Global Modals */}
      <GlobalModals />
      
      {/* Global AI Chatbot */}
      <Chatbot />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <ModalProvider>
        <Router>
          <Layout />
        </Router>
      </ModalProvider>
    </AuthProvider>
  );
};

export default App;
