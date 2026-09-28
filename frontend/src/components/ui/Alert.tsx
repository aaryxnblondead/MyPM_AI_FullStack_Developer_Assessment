import type { HTMLAttributes } from "react";

type Props = HTMLAttributes<HTMLDivElement> & {
  tone?: "info" | "error";
};

export function Alert({ tone = "info", className = "", ...rest }: Props) {
  const toneClass =
    tone === "error"
      ? "border-border bg-surface text-body"
      : "border-border bg-tint text-title";
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`rounded-card border px-6 py-4 text-sm ${toneClass} ${className}`}
      {...rest}
    />
  );
}
