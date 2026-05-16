import { useNavigate } from "react-router-dom";

export default function ForbiddenPage() {
  const navigate = useNavigate();
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-xl font-semibold text-slate-800">Bạn không có quyền truy cập</h1>
      <p className="max-w-sm text-sm text-slate-500">
        Tài khoản hiện tại không có quyền xem hoặc thao tác với nội dung này.
      </p>
      <button
        onClick={() => navigate(-1)}
        className="rounded-md bg-slate-100 px-4 py-2 text-sm text-slate-700 hover:bg-slate-200"
      >
        Quay lại
      </button>
    </div>
  );
}
