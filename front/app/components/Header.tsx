"use client";

import { useAuth } from "@/app/lib/auth";

interface HeaderProps {
  title: string;
  onMenuToggle?: () => void;
}

export default function Header({ title, onMenuToggle }: HeaderProps) {
  const { user } = useAuth();

  const initials = user
    ? user.username
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "??";

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-zinc-200/80 bg-white/80 backdrop-blur-md flex items-center justify-between px-6 shrink-0 dark:border-zinc-800 dark:bg-zinc-900/80">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 rounded-lg text-zinc-500 hover:bg-zinc-100 transition-colors dark:hover:bg-zinc-800"
          aria-label="Toggle menu"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <h1 className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-white">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm font-semibold shadow-sm ring-2 ring-white/60 dark:ring-zinc-900/60">
          {initials}
        </div>
      </div>
    </header>
  );
}
