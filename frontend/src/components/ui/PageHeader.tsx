interface Props {
  title: string;
  action?: React.ReactNode;
}
export default function PageHeader({ title, action }: Props) {
  return (
    <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <h1 className="text-base font-semibold text-slate-800">{title}</h1>
      {action && <div>{action}</div>}
    </div>
  );
}
