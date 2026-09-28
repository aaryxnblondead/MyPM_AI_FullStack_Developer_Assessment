import type { HTMLAttributes } from "react";

type Props = HTMLAttributes<HTMLDivElement>;

export function Container({ className = "", ...rest }: Props) {
  return (
    <div className={`mx-auto w-full max-w-6xl px-4 ${className}`} {...rest} />
  );
}
