"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/app/lib/auth";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: GridIcon },
  { href: "/cv/edit", label: "Mi CV", icon: DocumentIcon },
  { href: "/cv/preview", label: "Vista Previa", icon: EyeIcon },
  { href: "/chat", label: "Asistente IA", icon: ChatIcon },
  { href: "/cv/analysis", label: "Analisis", icon: ChartIcon },
  { href: "/cv/generate", label: "Generar CV", icon: DownloadIcon },
];

function GridIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
    </svg>
  );
}

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function ChartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

function DownloadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function LogOutIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed top-0 left-0 z-50 h-full bg-zinc-900 text-white
          transition-all duration-300 ease-in-out
          ${isOpen ? "w-60 translate-x-0" : "w-16 -translate-x-full lg:translate-x-0"}
        `}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center h-16 px-4 border-b border-zinc-800">
            <span className="text-xl font-bold text-white whitespace-nowrap overflow-hidden">
              {isOpen ? "CV Creator" : "CV"}
            </span>
          </div>

          <nav className="flex-1 py-4 space-y-1 px-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                    transition-colors duration-150
                    ${isActive
                      ? "bg-blue-600 text-white"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                    }
                  `}
                  title={!isOpen ? item.label : undefined}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  <span className={`whitespace-nowrap overflow-hidden ${isOpen ? "" : "hidden lg:hidden"}`}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-zinc-800 p-3">
            {user && (
              <div className={`mb-3 ${isOpen ? "" : "hidden lg:block"}`}>
                <p className="text-sm font-medium text-white truncate">{user.username}</p>
                <p className="text-xs text-zinc-400 truncate">{user.email}</p>
              </div>
            )}
            <button
              onClick={() => {
                logout();
                window.location.href = "/login";
              }}
              className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors duration-150"
              title="Cerrar sesion"
            >
              <LogOutIcon className="w-5 h-5 flex-shrink-0" />
              <span className={`whitespace-nowrap overflow-hidden ${isOpen ? "" : "hidden lg:hidden"}`}>
                Cerrar sesion
              </span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
