interface Props {
  title: string;
  body?: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({ title, body, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <p className="font-medium text-slate-600">{title}</p>
      {body && <p className="max-w-xs text-sm text-slate-400">{body}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-1 rounded-md bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
