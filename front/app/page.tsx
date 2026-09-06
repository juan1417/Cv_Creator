"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/lib/auth";

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    router.replace(user ? "/dashboard" : "/login");
  }, [user, isLoading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50">
      <div className="text-zinc-500 text-sm">Cargando...</div>
    </div>
  );
}
