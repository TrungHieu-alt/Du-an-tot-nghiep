import { cn } from "@/lib/cn";

interface Props {
  label: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}
export default function FormField({ label, error, children, className }: Props) {
  return (
    <div className={cn("space-y-1", className)}>
      <label className="block text-sm font-medium text-slate-700">{label}</label>
      {children}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}

export function inputCls(error?: string) {
  return cn(
    "w-full rounded-md border px-3 py-2 text-sm outline-none transition-colors",
    "placeholder:text-slate-400 focus:border-slate-500 focus:ring-1 focus:ring-slate-500",
    error ? "border-red-400" : "border-slate-300",
  );
}
