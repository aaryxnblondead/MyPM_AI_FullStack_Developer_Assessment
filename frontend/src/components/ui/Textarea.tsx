import type { TextareaHTMLAttributes } from "react";

type Props = TextareaHTMLAttributes<HTMLTextAreaElement>;

export function Textarea({ className = "", ...rest }: Props) {
  return (
    <textarea
      className={`block w-full min-h-area rounded-area border border-border bg-surface px-field-x py-4 text-base text-body placeholder:text-muted transition-all duration-500 focus:border-primary focus:outline-none ${className}`}
      {...rest}
    />
  );
}
