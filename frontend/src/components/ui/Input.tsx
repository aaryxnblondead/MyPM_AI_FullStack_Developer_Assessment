import type { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className = "", ...rest }: Props) {
  return (
    <input
      className={`block w-full h-input rounded-input border border-border bg-surface px-field-x text-base text-body placeholder:text-muted transition-all duration-500 focus:border-primary focus:outline-none ${className}`}
      {...rest}
    />
  );
}
