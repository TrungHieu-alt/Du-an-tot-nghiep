import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppShell from "@/components/AppShell";
import AuthPage from "@/pages/AuthPage";
import NotFoundPage from "@/pages/errors/NotFoundPage";
import type { Role } from "@/lib/api";

// Profile setup
import CandidateProfileSetupPage from "@/pages/candidate/ProfileSetupPage";
import RecruiterProfileSetupPage from "@/pages/recruiter/ProfileSetupPage";

// Candidate pages
import JobMarketPage from "@/pages/candidate/JobMarketPage";
import MyActivityPage from "@/pages/candidate/MyActivityPage";
import ResumeDetailPage from "@/pages/candidate/ResumeDetailPage";
import ResumeCreatePage from "@/pages/candidate/ResumeCreatePage";

// Recruiter pages
import TalentMarketPage from "@/pages/recruiter/TalentMarketPage";
import RecruiterApplicationsPage from "@/pages/recruiter/RecruiterApplicationsPage";
import JobDetailPage from "@/pages/recruiter/JobDetailPage";
import JobCreatePage from "@/pages/recruiter/JobCreatePage";

// Shared pages
import RecordsPage from "@/pages/RecordsPage";
import NotificationsPage from "@/pages/NotificationsPage";
import AccountSettingsPage from "@/pages/AccountSettingsPage";
import UploadPage from "@/pages/UploadPage";

// Admin
import AdminPage from "@/pages/admin/AdminPage";

function RoleHome() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/auth" replace />;
  const dest: Record<Role, string> = {
    candidate: "/jobs",
    recruiter: "/talent",
    admin: "/admin",
  };
  return <Navigate to={dest[user.role]} replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/auth" element={<AuthPage />} />

          {/* Profile setup — protected but outside shell */}
          <Route path="/profile/candidate/setup" element={
            <ProtectedRoute roles={["candidate"]}>
              <CandidateProfileSetupPage />
            </ProtectedRoute>
          } />
          <Route path="/profile/recruiter/setup" element={
            <ProtectedRoute roles={["recruiter"]}>
              <RecruiterProfileSetupPage />
            </ProtectedRoute>
          } />

          {/* Root redirect */}
          <Route path="/" element={<RoleHome />} />

          {/* Protected shell */}
          <Route
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            {/* Candidate */}
            <Route path="/jobs" element={
              <ProtectedRoute roles={["candidate"]}>
                <JobMarketPage />
              </ProtectedRoute>
            } />
            <Route path="/activity" element={
              <ProtectedRoute roles={["candidate"]}>
                <MyActivityPage />
              </ProtectedRoute>
            } />

            {/* Recruiter */}
            <Route path="/talent" element={
              <ProtectedRoute roles={["recruiter"]}>
                <TalentMarketPage />
              </ProtectedRoute>
            } />
            <Route path="/recruiter/applications" element={
              <ProtectedRoute roles={["recruiter"]}>
                <RecruiterApplicationsPage />
              </ProtectedRoute>
            } />

            {/* Records — candidate: resumes, recruiter: jobs */}
            <Route path="/records" element={
              <ProtectedRoute roles={["candidate", "recruiter"]}>
                <RecordsPage />
              </ProtectedRoute>
            } />
            <Route path="/records/resumes/new" element={
              <ProtectedRoute roles={["candidate"]}>
                <ResumeCreatePage />
              </ProtectedRoute>
            } />
            <Route path="/records/resumes/:resumeId" element={
              <ProtectedRoute roles={["candidate"]}>
                <ResumeDetailPage />
              </ProtectedRoute>
            } />
            <Route path="/records/jobs/new" element={
              <ProtectedRoute roles={["recruiter"]}>
                <JobCreatePage />
              </ProtectedRoute>
            } />
            <Route path="/records/jobs/:jobId" element={
              <ProtectedRoute roles={["recruiter"]}>
                <JobDetailPage />
              </ProtectedRoute>
            } />

            {/* Documents upload */}
            <Route path="/documents/upload" element={
              <ProtectedRoute roles={["candidate", "recruiter"]}>
                <UploadPage />
              </ProtectedRoute>
            } />

            {/* Shared */}
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/settings" element={<AccountSettingsPage />} />

            {/* Admin */}
            <Route path="/admin" element={
              <ProtectedRoute roles={["admin"]}>
                <AdminPage />
              </ProtectedRoute>
            } />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
