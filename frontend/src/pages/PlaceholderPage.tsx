interface Props {
  title: string;
  description?: string;
}

export default function PlaceholderPage({ title, description }: Props) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center">
      <h1 className="text-lg font-semibold text-slate-700">{title}</h1>
      <p className="max-w-sm text-sm text-slate-400">
        {description ?? "Tính năng này sẽ được triển khai trong Slice 15."}
      </p>
    </div>
  );
}
