"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";

import { useAuth } from "@/app/lib/auth";
import { apiErrorMessage, getFullCV, updateCV } from "@/app/lib/api";
import type { FullCV } from "@/app/lib/types";

import {
  AchievementManager,
  EducationManager,
  ExperienceManager,
  LanguagePicker,
  PersonalFields,
  ProgramPicker,
  SkillPicker,
} from "@/app/components/cv-forms";

// ─── Helpers ────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#6366F1] border-t-transparent" />
    </div>
  );
}

function useDebounce(fn: () => void, ms: number) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latest = useRef(fn);

  // El timer siempre ejecuta la versión más nueva de `fn`: si cerrara sobre la
  // función de la tecla que lo programó, se guardaría el valor anterior a la
  // última tecla tipeada.
  useEffect(() => {
    latest.current = fn;
  });

  // Al desmontar, lo que quedó pendiente se envía en vez de descartarse:
  // salir antes de los `ms` milisegundos no pierde la última edición.
  useEffect(() => {
    return () => {
      if (timer.current) {
        clearTimeout(timer.current);
        timer.current = null;
        latest.current();
      }
    };
  }, []);

  return useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      timer.current = null;
      latest.current();
    }, ms);
  }, [ms]);
}

type SaveStatus = "idle" | "saving" | "saved";

function SaveIndicator({ status }: { status: SaveStatus }) {
  if (status === "idle") return null;
  return (
    <span className="ml-3 text-xs font-medium">
      {status === "saving" && (
        <span className="text-[#94A3B8]">Guardando...</span>
      )}
      {status === "saved" && (
        <span className="text-[#10B981]">Guardado</span>
      )}
    </span>
  );
}

// ─── CV Editor Page ──────────────────────────────────────────────────────────

export default function CVEditPage() {
  const { user } = useAuth();
  const [cv, setCv] = useState<FullCV | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [dirty, setDirty] = useState(false);

  // Personal info form
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [about, setAbout] = useState("");
  const [porfolio, setPorfolio] = useState("");
  const [linkedin, setLinkedin] = useState("");

  // Track if form is initialized
  const initialized = useRef(false);

  const personalSetters = {
    name: setName,
    email: setEmail,
    phone: setPhone,
    address: setAddress,
    about: setAbout,
    porfolio: setPorfolio,
    linkedin: setLinkedin,
  } as const;

  const fetchCV = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getFullCV(user.id);
      setCv(data);
      setName(data.cv.name);
      setEmail(data.cv.email);
      setPhone(data.cv.phone);
      setAddress(data.cv.address);
      setAbout(data.cv.about);
      setPorfolio(data.cv.porfolio);
      setLinkedin(data.cv.linkedin ?? "");
      initialized.current = true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar el CV");
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Refresco tras guardar: actualiza la lista sin mostrar el spinner y sin
  // pisar los campos que el usuario pueda estar escribiendo en este momento.
  const refreshCV = useCallback(async () => {
    if (!user) return;
    try {
      const data = await getFullCV(user.id);
      setCv(data);
      setError(null);
    } catch (e) {
      // El estado local sigue siendo válido: se avisa sin desmontar la página.
      setError(e instanceof Error ? e.message : "No se pudo actualizar el CV");
    }
  }, [user]);

  useEffect(() => {
    fetchCV();
  }, [fetchCV]);

  // ── Auto-save personal info ──────────────────────────────────────────

  const doSavePersonal = useCallback(async () => {
    if (!user || !initialized.current || !dirty) return;
    setSaveStatus("saving");
    try {
      const updated = await updateCV(user.id, {
        name,
        email,
        phone,
        address,
        about,
        porfolio,
        linkedin,
      });
      setCv((prev) => (prev ? { ...prev, cv: updated } : prev));
      setDirty(false);
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch (e) {
      setSaveStatus("idle");
      setError(apiErrorMessage(e, "No se pudieron guardar tus datos"));
    }
  }, [user, dirty, name, email, phone, address, about, porfolio, linkedin]);

  const autoSavePersonal = useDebounce(doSavePersonal, 1000);


  const handleChange = <T extends React.Dispatch<React.SetStateAction<string>>>(
    setter: T,
    value: string,
  ) => {
    setDirty(true);
    setter(value);
    autoSavePersonal();
  };

  if (loading) return <Spinner />;

  if (error && !cv) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p className="text-[#EF4444]">{error}</p>
        <button
          onClick={fetchCV}
          className="rounded-lg bg-[#6366F1] px-4 py-2 text-sm font-medium text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:bg-[#6366F1]/90"
        >
          Reintentar
        </button>
      </div>
    );
  }


  if (!cv) return null;
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <h1 className="text-[28px] font-bold text-[#F8FAFC]">
            Editar CV
          </h1>
          <SaveIndicator status={saveStatus} />
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/cv/create"
            className="inline-flex items-center gap-2 rounded-lg border border-[#334155] bg-[#1E293B] px-4 py-2 text-sm font-medium text-[#F1F5F9] transition-all duration-200 hover:border-[#6366F1]/30 hover:bg-[#0F172A]"
          >
            Crear con el asistente
          </Link>
          <a
            href="/cv/preview"
            target="_blank"
            className="inline-flex items-center gap-2 rounded-lg border border-[#334155] bg-[#1E293B] px-4 py-2 text-sm font-medium text-[#F1F5F9] transition-all duration-200 hover:border-[#6366F1]/30 hover:bg-[#0F172A]"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            Vista Previa
          </a>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-[#EF4444]/20 bg-[#EF4444]/10 p-4 text-sm text-[#EF4444] backdrop-blur-sm">
          {error}
          <button onClick={() => setError(null)} className="ml-2 font-medium underline">
            Cerrar
          </button>
        </div>
      )}

      {/* ── Personal Info ─────────────────────────────────────────────── */}
      <section className="rounded-2xl border border-[#334155] bg-[#1E293B] p-6 shadow-xl backdrop-blur-sm">
        <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
          <h2 className="text-lg font-semibold text-[#F1F5F9]">
            Información Personal
          </h2>
          <span className="text-xs text-[#64748B]">Se guarda solo mientras escribís</span>
        </div>
        <PersonalFields
          value={{ name, email, phone, address, about, porfolio, linkedin }}
          onChange={(key, value) => handleChange(personalSetters[key], value)}
          onBlur={() => {
            if (dirty) void doSavePersonal();
          }}
        />
      </section>

      {/* ── Secciones (módulos compartidos con el asistente) ────────────── */}
      <ExperienceManager cv={cv} userId={user!.id} onChanged={refreshCV} onError={setError} title="Experiencia" subtitle="Puestos, proyectos o freelance" />
      <SkillPicker cv={cv} userId={user!.id} onChanged={refreshCV} onError={setError} type="tech" title="Tecnologías" subtitle="Lenguajes, frameworks y herramientas técnicas" />
      <SkillPicker cv={cv} userId={user!.id} onChanged={refreshCV} onError={setError} type="soft" title="Skills Adicionales" subtitle="Habilidades blandas y competencias" />
      <EducationManager cv={cv} userId={user!.id} onChanged={refreshCV} onError={setError} title="Formación" subtitle="Carreras, tecnicaturas y certificaciones" />
      <AchievementManager cv={cv} userId={user!.id} onChanged={refreshCV} onError={setError} title="Logros Destacados" subtitle="Premios, publicaciones y proyectos propios" />
      <ProgramPicker cv={cv} userId={user!.id} onChanged={refreshCV} onError={setError} title="Programas" subtitle="Herramientas, cursos y certificaciones" />
      <LanguagePicker cv={cv} userId={user!.id} onChanged={refreshCV} onError={setError} title="Idiomas" subtitle="Nivel con estándar europeo si lo tenés" />
    </div>
  );
}
