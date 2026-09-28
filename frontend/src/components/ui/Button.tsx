import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "dark" | "ghost";
type Size = "sm" | "base";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
};

const base =
  "inline-flex items-center justify-center rounded-pill font-display font-medium transition-all duration-500 disabled:cursor-not-allowed disabled:opacity-60";

const sizeClasses: Record<Size, string> = {
  sm: "px-3 py-1.5 text-sm",
  base: "px-btn-x py-btn-y text-base",
};

const variants: Record<Variant, string> = {
  primary: "bg-primary text-surface hover:bg-secondary",
  dark: "bg-title text-surface hover:bg-secondary",
  ghost: "bg-surface text-title border border-border hover:border-primary",
};

export function Button({ variant = "primary", size = "base", fullWidth = false, className = "", ...rest }: Props) {
  const width = fullWidth ? " w-full" : "";
  return <button className={`${base} ${sizeClasses[size]} ${variants[variant]}${width} ${className}`} {...rest} />;
}
