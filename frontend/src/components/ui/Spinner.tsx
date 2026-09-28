type Props = {
  label?: string;
};

export function Spinner({ label = "Loading" }: Props) {
  return (
    <span className="inline-flex items-center gap-3 text-sm text-body" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border border-border border-t-primary" />
      {label}
    </span>
  );
}
