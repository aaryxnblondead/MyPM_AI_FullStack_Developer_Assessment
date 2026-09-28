import type { HTMLAttributes } from "react";

type Props = HTMLAttributes<HTMLSpanElement>;

export function Badge({ className = "", ...rest }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-pill bg-tint px-4 py-1 font-display text-sm font-medium text-primary ${className}`}
      {...rest}
    />
  );
}
