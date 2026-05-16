import { useState, type FormEvent } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError, type Role } from "@/lib/api";
import { cn } from "@/lib/cn";

type Mode = "login" | "register";

const ERROR_MESSAGES: Record<string, string> = {
  invalid_credentials: "Email hoặc mật khẩu không đúng.",
  invalid_token: "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
  expired_token: "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
  duplicate_email: "Email đã được đăng ký. Vui lòng đăng nhập.",
  disabled_user: "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.",
};

function roleHome(role: Role): string {
  if (role === "candidate") return "/jobs";
  if (role === "recruiter") return "/talent";
  return "/admin";
}

export default function AuthPage() {
  const { login, register, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const returnTo = (location.state as { returnTo?: string } | null)?.returnTo;

  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("candidate");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Already logged in — redirect
  if (user) {
    const dest = returnTo ?? roleHome(user.role);
    navigate(dest, { replace: true });
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setSubmitting(true);

    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, role);
      }
      // After auth context updates, redirect — useEffect below handles this
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 422 && err.body.fields) {
          setFieldErrors(err.body.fields);
        } else {
          setError(ERROR_MESSAGES[err.body.code] ?? err.body.message);
        }
      } else {
        setError("Không thể kết nối. Kiểm tra mạng và thử lại.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  // Redirect after successful auth (user state updated by context)
  // We use a render-time check: if user is set after submit, navigate
  // This is handled by the early return above on next render.

  return (
    <div className="flex min-h-screen">
      {/* Left: form */}
      <div className="flex w-full flex-col justify-center px-8 py-12 sm:px-12 md:w-1/2 lg:w-2/5">
        <div className="mx-auto w-full max-w-sm">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-900">JobConnect</h1>
            <p className="mt-1 text-sm text-slate-500">
              {mode === "login" ? "Đăng nhập vào tài khoản của bạn" : "Tạo tài khoản mới"}
            </p>
          </div>

          {/* Mode switch */}
          <div className="mb-6 flex rounded-lg border border-slate-200 p-1">
            <button
              type="button"
              onClick={() => { setMode("login"); setError(null); setFieldErrors({}); }}
              className={cn(
                "flex-1 rounded-md py-1.5 text-sm font-medium transition-colors",
                mode === "login"
                  ? "bg-slate-900 text-white"
                  : "text-slate-500 hover:text-slate-700",
              )}
            >
              Đăng nhập
            </button>
            <button
              type="button"
              onClick={() => { setMode("register"); setError(null); setFieldErrors({}); }}
              className={cn(
                "flex-1 rounded-md py-1.5 text-sm font-medium transition-colors",
                mode === "register"
                  ? "bg-slate-900 text-white"
                  : "text-slate-500 hover:text-slate-700",
              )}
            >
              Đăng ký
            </button>
          </div>

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {/* Email */}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="email@example.com"
                className={cn(
                  "w-full rounded-md border px-3 py-2 text-sm outline-none transition-colors",
                  "placeholder:text-slate-400 focus:border-slate-500 focus:ring-1 focus:ring-slate-500",
                  fieldErrors["body.email"] ? "border-red-400" : "border-slate-300",
                )}
              />
              {fieldErrors["body.email"] && (
                <p className="mt-1 text-xs text-red-500">{fieldErrors["body.email"]}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Mật khẩu</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder={mode === "register" ? "Tối thiểu 8 ký tự" : ""}
                className={cn(
                  "w-full rounded-md border px-3 py-2 text-sm outline-none transition-colors",
                  "placeholder:text-slate-400 focus:border-slate-500 focus:ring-1 focus:ring-slate-500",
                  fieldErrors["body.password"] ? "border-red-400" : "border-slate-300",
                )}
              />
              {fieldErrors["body.password"] && (
                <p className="mt-1 text-xs text-red-500">{fieldErrors["body.password"]}</p>
              )}
            </div>

            {/* Role — register only */}
            {mode === "register" && (
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Vai trò</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as Role)}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
                >
                  <option value="candidate">Ứng viên</option>
                  <option value="recruiter">Nhà tuyển dụng</option>
                </select>
              </div>
            )}

            {/* Global error */}
            {error && (
              <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className={cn(
                "w-full rounded-md bg-slate-900 py-2.5 text-sm font-medium text-white transition-colors",
                submitting ? "cursor-not-allowed opacity-60" : "hover:bg-slate-700",
              )}
            >
              {submitting
                ? "Đang xử lý..."
                : mode === "login"
                  ? "Đăng nhập"
                  : "Tạo tài khoản"}
            </button>
          </form>
        </div>
      </div>

      {/* Right: decorative panel (desktop only) */}
      <div className="hidden bg-slate-900 md:flex md:w-1/2 lg:w-3/5 flex-col items-center justify-center px-12">
        <div className="max-w-md text-center text-white">
          <h2 className="mb-4 text-3xl font-bold">Kết nối tài năng với cơ hội</h2>
          <p className="text-slate-400">
            Nền tảng tuyển dụng thông minh với matching AI hai chiều cho ứng viên và nhà tuyển dụng.
          </p>
        </div>
      </div>
    </div>
  );
}
