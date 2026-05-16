import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";

export default function DisabledPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/auth", { replace: true });
  }

  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-xl font-semibold text-slate-800">Tài khoản đã bị khóa</h1>
      <p className="max-w-sm text-sm text-slate-500">
        Bạn không thể thực hiện thao tác này. Vui lòng liên hệ quản trị viên nếu cần hỗ trợ.
      </p>
      <button
        onClick={handleLogout}
        className="rounded-md bg-slate-800 px-4 py-2 text-sm text-white hover:bg-slate-700"
      >
        Đăng xuất
      </button>
    </div>
  );
}
