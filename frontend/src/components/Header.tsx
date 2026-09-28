"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "New Analysis" },
  { href: "/resumes", label: "Resumes" },
  { href: "/history", label: "History" },
];

export function Header() {
  const pathname = usePathname();
  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4">
        <Link href="/" className="font-display text-lg font-semibold text-title">
          MyPM Fit Check
        </Link>
        <nav aria-label="Main" className="flex gap-2">
          {links.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                aria-current={active ? "page" : undefined}
                className={`rounded-pill px-4 py-2 font-display text-sm font-medium ${
                  active ? "bg-primary text-surface" : "text-title hover:border-primary border border-transparent"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
