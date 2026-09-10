"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/lib/auth";
import { getFullCV } from "@/app/lib/api";
import type { FullCV } from "@/app/lib/types";

const FONT = "'Arial', 'Helvetica Neue', Helvetica, sans-serif";
const COLOR = "#404040";
const SIZE = {
  name: "26px",
  contact: "11px",
  body: "11.5px",
  heading: "12px",
  section: "13px",
  date: "11px",
};

export default function CVPreviewPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [cv, setCV] = useState<FullCV | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    getFullCV(user.id)
      .then(setCV)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-zinc-400">Cargando vista previa...</div>
      </div>
    );
  }

  if (!cv) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <p className="text-zinc-400">No se pudo cargar el CV.</p>
        <button
          onClick={() => router.push("/cv/edit")}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 hover:bg-indigo-500 transition-all"
        >
          Ir a Editar CV
        </button>
      </div>
    );
  }

  const data = cv.cv;
  const experiences = cv.experiences || [];
  const education = cv.education || [];
  const skills = cv.skills || [];
  const achievements = cv.achievements || [];
  const programs = cv.programs || [];
  const languages = cv.languages || [];

  const hasData =
    data.name ||
    data.about ||
    experiences.length ||
    education.length ||
    skills.length ||
    achievements.length ||
    programs.length ||
    languages.length;

  const contactParts = [
    data.address,
    data.linkedin,
    data.porfolio,
    data.phone,
    data.email,
  ].filter(Boolean);

  return (
    <div className="max-w-[800px] mx-auto">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-6 no-print">
        <button
          onClick={() => router.push("/cv/edit")}
          className="text-sm text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Volver a Editar
        </button>
        <button
          onClick={() => window.print()}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 hover:bg-indigo-500 transition-all"
        >
          Imprimir / Guardar PDF
        </button>
      </div>

      {/* CV Document */}
      <div className="bg-white shadow-xl rounded-lg overflow-hidden print:shadow-none print:rounded-none">
        <div className="px-10 py-8">
          {!hasData && (
            <div className="text-center py-16 text-neutral-400">
              <p className="text-lg">Tu CV está vacío</p>
              <p className="text-sm mt-2">
                Ve a{" "}
                <button
                  onClick={() => router.push("/cv/edit")}
                  className="text-blue-600 hover:underline"
                >
                  Editar CV
                </button>{" "}
                o usá el chat para crearlo desde cero.
              </p>
            </div>
          )}

          {data.name && (
            <h1
              className="font-bold text-center mb-1"
              style={{ fontSize: SIZE.name, color: COLOR, fontFamily: FONT }}
            >
              {data.name}
            </h1>
          )}

          {contactParts.length > 0 && (
            <p
              className="text-center mb-8"
              style={{ fontSize: SIZE.contact, color: COLOR, fontFamily: FONT, letterSpacing: "0.02em" }}
            >
              {contactParts.join(" ● ")}
            </p>
          )}

          {data.about && (
            <Section title="PERFIL PROFESIONAL">
              <p style={{ fontSize: SIZE.body, color: COLOR, lineHeight: "1.6", fontFamily: FONT }}>
                {data.about}
              </p>
            </Section>
          )}

          {education.length > 0 && (
            <Section title="EDUCACIÓN">
              {education.map((edu, i) => (
                <div key={i} className="mb-3">
                  <div className="flex justify-between items-baseline">
                    <span className="font-bold" style={{ fontSize: SIZE.heading, color: COLOR, fontFamily: FONT }}>
                      {edu.degree}
                    </span>
                    <span style={{ fontSize: SIZE.date, color: COLOR, fontFamily: FONT, whiteSpace: "nowrap", marginLeft: "12px" }}>
                      {formatDateRange(edu.start_date, edu.end_date)}
                    </span>
                  </div>
                  {edu.institution && (
                    <p className="italic" style={{ fontSize: SIZE.body, color: COLOR, fontFamily: FONT }}>
                      {edu.institution}
                    </p>
                  )}
                  {edu.description && (
                    <p className="mt-1" style={{ fontSize: SIZE.body, color: COLOR, lineHeight: "1.6", fontFamily: FONT }}>
                      {edu.description}
                    </p>
                  )}
                </div>
              ))}
            </Section>
          )}

          {experiences.length > 0 && (
            <Section title="EXPERIENCIA PROFESIONAL">
              {experiences.map((exp, i) => (
                <div key={i} className="mb-3">
                  <div className="flex justify-between items-baseline">
                    <span className="font-bold" style={{ fontSize: SIZE.heading, color: COLOR, fontFamily: FONT }}>
                      {exp.company}
                      {exp.title && <span className="italic font-normal"> — {exp.title}</span>}
                    </span>
                    <span style={{ fontSize: SIZE.date, color: COLOR, fontFamily: FONT, whiteSpace: "nowrap", marginLeft: "12px" }}>
                      {formatDateRange(exp.start_date, exp.end_date)}
                    </span>
                  </div>
                  {exp.description && (
                    <div className="mt-1">
                      {exp.description.split("\n").map((line, j) => (
                        <p key={j} style={{ fontSize: SIZE.body, color: COLOR, lineHeight: "1.6", fontFamily: FONT, paddingLeft: "16px", position: "relative" as const }}>
                          <span style={{ position: "absolute", left: 0 }}>•</span>
                          {line}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </Section>
          )}

          {skills.length > 0 && (
            <Section title="HABILIDADES">
              <p style={{ fontSize: SIZE.body, color: COLOR, lineHeight: "1.6", fontFamily: FONT }}>
                {skills.map((s) => s.name).join(" | ")}
              </p>
            </Section>
          )}

          {achievements.length > 0 && (
            <Section title="LOGROS DESTACADOS">
              {achievements.map((ach, i) => (
                <div key={i} className="mb-2">
                  <p style={{ fontSize: SIZE.body, color: COLOR, fontFamily: FONT }}>
                    <span className="font-bold">{ach.title}</span>
                    {ach.description && ` — ${ach.description}`}
                  </p>
                </div>
              ))}
            </Section>
          )}

          {programs.length > 0 && (
            <Section title="TECNOLOGÍAS">
              <p style={{ fontSize: SIZE.body, color: COLOR, lineHeight: "1.6", fontFamily: FONT }}>
                {programs.map((p) => p.name).join(" | ")}
              </p>
            </Section>
          )}

          {languages.length > 0 && (
            <Section title="IDIOMAS">
              <p style={{ fontSize: SIZE.body, color: COLOR, lineHeight: "1.6", fontFamily: FONT }}>
                {languages.map((l) => `${l.name} (${l.level})`).join(" | ")}
              </p>
            </Section>
          )}
        </div>
      </div>

      <style jsx global>{`
        @media print {
          body { background: white !important; }
          nav, header, footer, .no-print { display: none !important; }
          .print\\:shadow-none { box-shadow: none !important; }
          .print\\:rounded-none { border-radius: 0 !important; }
        }
      `}</style>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <h2
        className="font-bold uppercase tracking-wide pb-1 mb-3"
        style={{ fontSize: SIZE.section, color: COLOR, borderBottom: `1.5px solid ${COLOR}`, fontFamily: FONT }}
      >
        {title}
      </h2>
      {children}
    </div>
  );
}

function formatDateRange(start?: string | null, end?: string | null): string {
  if (!start) return "";
  const s = new Date(start);
  const startStr = s.toLocaleDateString("es-AR", { month: "short", year: "numeric" });
  if (!end) return `${startStr} - Presente`;
  const e = new Date(end);
  const endStr = e.toLocaleDateString("es-AR", { month: "short", year: "numeric" });
  return `${startStr} - ${endStr}`;
}
