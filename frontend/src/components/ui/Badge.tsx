import { cn } from "@/lib/cn";

const variants: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  active: "bg-green-100 text-green-700",
  archived: "bg-slate-200 text-slate-500",
  published: "bg-blue-100 text-blue-700",
  closed: "bg-red-100 text-red-600",
  submitted: "bg-sky-100 text-sky-700",
  shortlisted: "bg-yellow-100 text-yellow-700",
  rejected: "bg-red-100 text-red-600",
  hired: "bg-green-100 text-green-700",
  withdrawn: "bg-slate-100 text-slate-500",
  pending: "bg-orange-100 text-orange-700",
  accepted: "bg-green-100 text-green-700",
  unread: "bg-blue-100 text-blue-700",
  read: "bg-slate-100 text-slate-500",
  active_user: "bg-green-100 text-green-700",
  disabled_user: "bg-red-100 text-red-600",
  default: "bg-slate-100 text-slate-600",
};

export default function Badge({ value, label }: { value: string; label?: string }) {
  const cls = variants[value] ?? variants.default;
  return (
    <span className={cn("inline-flex items-center rounded px-2 py-0.5 text-xs font-medium", cls)}>
      {label ?? value}
    </span>
  );
}
