import type { LabelHTMLAttributes } from "react";

type Props = LabelHTMLAttributes<HTMLLabelElement>;

export function Label({ className = "", ...rest }: Props) {
  return (
    <label
      className={`block font-display text-sm font-semibold text-title ${className}`}
      {...rest}
    />
  );
}
