import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/cn";
import {
  Briefcase,
  Users,
  FolderOpen,
  Bell,
  Settings,
  LogOut,
  LayoutDashboard,
  ClipboardList,
} from "lucide-react";

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

function candidateNav(): NavItem[] {
  return [
    { to: "/jobs", label: "Thị trường việc làm", icon: <Briefcase size={16} /> },
    { to: "/records", label: "Hồ sơ của tôi", icon: <FolderOpen size={16} /> },
    { to: "/activity", label: "Hoạt động", icon: <ClipboardList size={16} /> },
    { to: "/settings", label: "Cài đặt", icon: <Settings size={16} /> },
  ];
}

function recruiterNav(): NavItem[] {
  return [
    { to: "/talent", label: "Thị trường ứng viên", icon: <Users size={16} /> },
    { to: "/records", label: "Tin tuyển dụng", icon: <FolderOpen size={16} /> },
    { to: "/recruiter/applications", label: "Quản lý ứng tuyển", icon: <ClipboardList size={16} /> },
    { to: "/settings", label: "Cài đặt", icon: <Settings size={16} /> },
  ];
}

function adminNav(): NavItem[] {
  return [
    { to: "/admin", label: "Giám sát hệ thống", icon: <LayoutDashboard size={16} /> },
    { to: "/settings", label: "Cài đặt", icon: <Settings size={16} /> },
  ];
}

export default function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItems =
    user?.role === "candidate"
      ? candidateNav()
      : user?.role === "recruiter"
        ? recruiterNav()
        : adminNav();

  const roleLabel =
    user?.role === "candidate"
      ? "Ứng viên"
      : user?.role === "recruiter"
        ? "Nhà tuyển dụng"
        : "Quản trị viên";

  async function handleLogout() {
    await logout();
    navigate("/auth", { replace: true });
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-slate-200 bg-white">
        {/* Brand */}
        <div className="flex h-14 items-center border-b border-slate-200 px-4">
          <span className="font-semibold tracking-tight text-slate-800">JobConnect</span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto p-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-slate-100 font-medium text-slate-900"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                )
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div className="border-t border-slate-200 p-3">
          <div className="mb-1 flex items-center gap-2">
            <Bell size={14} className="text-slate-400" />
            <NavLink
              to="/notifications"
              className="text-xs text-slate-500 hover:text-slate-700"
            >
              Thông báo
            </NavLink>
          </div>
          <div className="mb-2 truncate text-xs text-slate-500">
            <span className="font-medium text-slate-700">{user?.email}</span>
            <br />
            <span className="text-slate-400">{roleLabel}</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-xs text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-800"
          >
            <LogOut size={13} />
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
