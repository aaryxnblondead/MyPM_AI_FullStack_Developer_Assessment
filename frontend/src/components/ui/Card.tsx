import type { HTMLAttributes } from "react";

type Props = HTMLAttributes<HTMLDivElement>;

export function Card({ className = "", ...rest }: Props) {
  return (
    <div
      className={`rounded-card border border-border bg-surface ${className}`}
      {...rest}
    />
  );
}
