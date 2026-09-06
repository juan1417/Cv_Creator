"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/lib/auth";
import { getFullCV } from "@/app/lib/api";
import type { FullCV } from "@/app/lib/types";

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
        <div className="text-neutral-500">Cargando vista previa...</div>
      </div>
    );
  }

  if (!cv) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <p className="text-neutral-500">No se pudo cargar el CV.</p>
        <button
          onClick={() => router.push("/cv/edit")}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
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

  const contactParts: string[] = [];
  if (data.address) contactParts.push(data.address);
  if (data.linkedin) contactParts.push(data.linkedin);
  if (data.phone) {
    contactParts.push(data.phone.startsWith("+") ? data.phone : `+${data.phone}`);
  }
  if (data.email) contactParts.push(data.email);

  return (
    <div className="max-w-[800px] mx-auto">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-6 no-print">
        <button
          onClick={() => router.push("/cv/edit")}
          className="text-sm text-neutral-500 hover:text-neutral-700 flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Volver a Editar
        </button>
        <button
          onClick={() => window.print()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          Imprimir / Guardar PDF
        </button>
      </div>

      {/* CV Document — Harvard Template Style */}
      <div className="bg-white shadow-xl rounded-lg overflow-hidden print:shadow-none print:rounded-none">
        <div className="px-10 py-8" style={{ fontFamily: "'STIX Two Text', 'Georgia', serif" }}>

          {/* ── NAME ──────────────────────────────────────────── */}
          <h1
            className="text-center font-bold tracking-wide"
            style={{ fontSize: "28px", color: "#1A1A2E" }}
          >
            {data.name || "Tu Nombre"}
          </h1>

          {/* ── CONTACT ───────────────────────────────────────── */}
          <p
            className="text-center mt-2"
            style={{ fontSize: "11px", color: "#444" }}
          >
            {contactParts.join(" \u2022 ")}
          </p>

          {/* ── ABOUT ─────────────────────────────────────────── */}
          {data.about && (
            <p className="mt-6" style={{ fontSize: "11px", color: "#333", lineHeight: "1.6" }}>
              {data.about}
            </p>
          )}

          {/* ── EXPERIENCIA PROFESIONAL ───────────────────────── */}
          {experiences.length > 0 && (
            <>
              <h2
                className="text-center mt-8 mb-4 font-bold uppercase tracking-widest"
                style={{ fontSize: "13px", color: "#1A1A2E", letterSpacing: "2px" }}
              >
                Experiencia Profesional
              </h2>
              {experiences.map((exp, i) => (
                <div key={i} className="mb-4">
                  <div className="flex justify-between items-baseline">
                    <div>
                      <span className="font-bold" style={{ fontSize: "11px", color: "#1A1A2E" }}>
                        {exp.company}
                      </span>
                      {exp.title && (
                        <span className="ml-2" style={{ fontSize: "11px", color: "#1A1A2E" }}>
                          {exp.title}
                        </span>
                      )}
                    </div>
                    <span style={{ fontSize: "10px", color: "#666" }}>
                      {exp.start_date && new Date(exp.start_date).getFullYear()}
                      {exp.start_date && (exp.end_date ? ` - ${new Date(exp.end_date).getFullYear()}` : " - Presente")}
                    </span>
                  </div>
                  {exp.description && (
                    <p className="mt-1" style={{ fontSize: "11px", color: "#333", lineHeight: "1.6" }}>
                      {exp.description}
                    </p>
                  )}
                </div>
              ))}
            </>
          )}

          {/* ── EDUCACIÓN ─────────────────────────────────────── */}
          {education.length > 0 && (
            <>
              <h2
                className="text-center mt-8 mb-4 font-bold uppercase tracking-widest"
                style={{ fontSize: "13px", color: "#1A1A2E", letterSpacing: "2px" }}
              >
                Educación
              </h2>
              {education.map((edu, i) => (
                <div key={i} className="mb-3">
                  <div className="flex justify-between items-baseline">
                    <div>
                      <span className="font-bold" style={{ fontSize: "11px", color: "#1A1A2E" }}>
                        {edu.institution}
                      </span>
                      {edu.degree && (
                        <span className="ml-2" style={{ fontSize: "11px", color: "#1A1A2E" }}>
                          {edu.degree}
                        </span>
                      )}
                    </div>
                    <span style={{ fontSize: "10px", color: "#666" }}>
                      {edu.start_date && new Date(edu.start_date).getFullYear()}
                      {edu.start_date && (edu.end_date ? ` - ${new Date(edu.end_date).getFullYear()}` : " - Presente")}
                    </span>
                  </div>
                  {edu.description && (
                    <p className="mt-1" style={{ fontSize: "11px", color: "#333", lineHeight: "1.6" }}>
                      {edu.description}
                    </p>
                  )}
                </div>
              ))}
            </>
          )}

          {/* ── SKILLS ADICIONALES ────────────────────────────── */}
          {skills.length > 0 && (
            <>
              <h2
                className="text-center mt-8 mb-4 font-bold uppercase tracking-widest"
                style={{ fontSize: "13px", color: "#1A1A2E", letterSpacing: "2px" }}
              >
                Skills Adicionales
              </h2>
              <div style={{ fontSize: "11px", color: "#333", lineHeight: "1.8" }}>
                {skills.map((s, i) => (
                  <div key={i}>
                    {"\u2022"} {s.name}
                    {s.level ? ` (${s.level})` : ""}
                  </div>
                ))}
              </div>
            </>
          )}

          {/* ── TECNOLOGÍAS ───────────────────────────────────── */}
          {skills.length > 0 && (
            <>
              <h2
                className="text-center mt-8 mb-4 font-bold uppercase tracking-widest"
                style={{ fontSize: "13px", color: "#1A1A2E", letterSpacing: "2px" }}
              >
                Tecnologías
              </h2>
              <p style={{ fontSize: "11px", color: "#333" }}>
                {skills.map((s) => s.name).join(", ")}
              </p>
            </>
          )}

          {/* ── EMPTY STATE ───────────────────────────────────── */}
          {!data.name && experiences.length === 0 && skills.length === 0 && education.length === 0 && (
            <div className="text-center py-12 text-neutral-400" style={{ fontFamily: "sans-serif" }}>
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
        </div>
      </div>

      {/* Print styles */}
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=STIX+Two+Text:wght@400;700&display=swap');
        @media print {
          body {
            background: white !important;
          }
          nav, header, footer, .no-print {
            display: none !important;
          }
          .print\\:shadow-none {
            box-shadow: none !important;
          }
          .print\\:rounded-none {
            border-radius: 0 !important;
          }
        }
      `}</style>
    </div>
  );
}
