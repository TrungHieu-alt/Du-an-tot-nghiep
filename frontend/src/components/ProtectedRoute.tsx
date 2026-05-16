import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import type { Role } from "@/lib/api";
import DisabledPage from "@/pages/errors/DisabledPage";
import ForbiddenPage from "@/pages/errors/ForbiddenPage";

interface Props {
  children: React.ReactNode;
  /** If provided, only these roles can access the route */
  roles?: Role[];
}

export default function ProtectedRoute({ children, roles }: Props) {
  const { token, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-500">
        Đang tải...
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/auth" state={{ returnTo: location.pathname }} replace />;
  }

  if (user.status === "disabled") {
    return <DisabledPage />;
  }

  if (roles && !roles.includes(user.role)) {
    return <ForbiddenPage />;
  }

  return <>{children}</>;
}
