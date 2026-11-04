"use client";

import type { ReactNode } from "react";

import type { FullCV } from "@/app/lib/types";

/** Contrato común de los seis pasos del asistente. */
export interface StepProps {
  userId: string;
  cv: FullCV;
  /** Refresco silencioso tras una mutación (sin spinner, sin desmontar). */
  onChanged: () => void;
  /** Avanza al paso siguiente. */
  onAdvance: () => void;
}

/**
 * Primitivas compartidas del asistente de creación.
 *
 * Un solo juego de campos para los seis pasos: mismo look, mismas reglas de
 * foco y el mismo manejo de errores, para que el formulario no se vea ni se
 * comporte distinto según el paso.
 */

const INPUT_BASE =
  "w-full rounded-lg border border-[#334155] bg-[#0F172A] px-3.5 py-2.5 text-sm text-[#F8FAFC] placeholder-[#64748B] transition-colors duration-150 focus:border-[#6366F1] focus:outline-none focus:ring-2 focus:ring-[#6366F1]/20 disabled:opacity-60";

const labelClass = "mb-1 block text-sm font-medium text-[#F1F5F9]";

interface CommonFieldProps {
  label: string;
  error?: string;
  hint?: string;
  required?: boolean;
}

function Label({
  label,
  hint,
  required,
}: {
  label: string;
  hint?: string;
  required?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <label className={labelClass}>
        {label}
        {required && <span className="ml-1 text-[#6366F1]">*</span>}
      </label>
      {hint && <span className="text-xs text-[#64748B]">{hint}</span>}
    </div>
  );
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs text-[#EF4444]">{message}</p>;
}

export function TextField({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  error,
  hint,
  required,
  autoFocus,
  disabled,
}: CommonFieldProps & {
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "email" | "tel" | "url";
  placeholder?: string;
  autoFocus?: boolean;
  disabled?: boolean;
}) {
  return (
    <div>
      <Label label={label} hint={hint} required={required} />
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        autoFocus={autoFocus}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        className={INPUT_BASE}
      />
      <FieldError message={error} />
    </div>
  );
}

export function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
  rows = 4,
  error,
  hint,
  required,
  disabled,
}: CommonFieldProps & {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
}) {
  return (
    <div>
      <Label label={label} hint={hint} required={required} />
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        required={required}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        className={`${INPUT_BASE} resize-y`}
      />
      <FieldError message={error} />
    </div>
  );
}

export function DateField({
  label,
  value,
  onChange,
  error,
  hint,
  disabled,
}: CommonFieldProps & {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <div>
      <Label label={label} hint={hint} />
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        className={`${INPUT_BASE} [color-scheme:dark]`}
      />
      <FieldError message={error} />
    </div>
  );
}

export function SelectField({
  label,
  value,
  onChange,
  options,
  error,
  hint,
}: CommonFieldProps & {
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <div>
      <Label label={label} hint={hint} />
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={INPUT_BASE}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      <FieldError message={error} />
    </div>
  );
}

/** Indicador de guardado: idle → saving → saved, sin desmontar el formulario. */
export function SaveState({ status }: { status: "idle" | "saving" | "saved" | "error" }) {
  if (status === "idle") return null;
  const styles = {
    saving: "text-[#94A3B8]",
    saved: "text-[#10B981]",
    error: "text-[#EF4444]",
  } as const;
  const text = {
    saving: "Guardando…",
    saved: "Guardado ✓",
    error: "No se pudo guardar",
  } as const;
  return (
    <span className={`text-xs font-medium ${styles[status]}`}>
      {status === "saving" ? "Guardando…" : text[status]}
    </span>
  );
}

/** Fila de un item guardado, con sus acciones. */
export function ItemCard({
  title,
  subtitle,
  meta,
  description,
  onEdit,
  onDelete,
  children,
}: {
  title: string;
  subtitle?: string;
  meta?: string;
  description?: string;
  onEdit?: () => void;
  onDelete?: () => void;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-[#334155] bg-[#0F172A] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="font-medium text-[#F8FAFC]">{title}</p>
          {subtitle && <p className="text-sm text-[#94A3B8]">{subtitle}</p>}
          {meta && <p className="mt-0.5 text-xs text-[#64748B]">{meta}</p>}
          {description && (
            <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-[#94A3B8]">
              {description}
            </p>
          )}
          {children}
        </div>
        <div className="flex shrink-0 gap-2">
          {onEdit && (
            <button
              type="button"
              onClick={onEdit}
              className="rounded px-2 py-1 text-xs font-medium text-[#6366F1] transition-colors hover:bg-[#6366F1]/10"
            >
              Editar
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="rounded px-2 py-1 text-xs font-medium text-[#EF4444] transition-colors hover:bg-[#EF4444]/10"
            >
              Borrar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/** Error general del paso (fallo de red, por ejemplo). */
export function StepError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <div className="rounded-lg border border-[#EF4444]/20 bg-[#EF4444]/10 px-4 py-2.5 text-sm text-[#EF4444]">
      {message}
    </div>
  );
}

/** Lista de chips: skills, programas e idiomas. */
export function ChipList({
  items,
  onDelete,
  deleteLabel,
}: {
  items: { id: string; label: string; meta?: string }[];
  onDelete: (id: string) => void;
  deleteLabel?: (label: string) => string;
}) {
  if (items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item.id}
          className="inline-flex items-center gap-2 rounded-full border border-[#334155] bg-[#0F172A] px-3 py-1.5 text-sm"
        >
          <span className="text-[#F8FAFC]">{item.label}</span>
          {item.meta && <span className="text-xs text-[#64748B]">{item.meta}</span>}
          <button
            type="button"
            onClick={() => onDelete(item.id)}
            aria-label={deleteLabel ? deleteLabel(item.label) : "Quitar"}
            className="-mr-1 text-[#64748B] transition-colors hover:text-[#EF4444]"
          >
            ×
          </button>
        </span>
      ))}
    </div>
  );
}

/** Navegación del paso: atrás, continuar o saltar (lo opcional). */export function StepActions({
  onBack,
  onNext,
  nextLabel = "Continuar",
  onSkip,
  skipLabel = "Todavía no tengo esto",
  nextDisabled,
  nextBusy,
}: {
  onBack?: () => void;
  onNext: () => void;
  nextLabel?: string;
  onSkip?: () => void;
  skipLabel?: string;
  nextDisabled?: boolean;
  nextBusy?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            className="rounded-lg border border-[#334155] bg-[#0F172A] px-4 py-2.5 text-sm font-medium text-[#F1F5F9] transition-colors hover:border-[#6366F1]/30 hover:bg-[#1E293B]"
          >
            ← Atrás
          </button>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {onSkip && (
          <button
            type="button"
            onClick={onSkip}
            className="text-sm text-[#94A3B8] underline-offset-2 transition-colors hover:text-[#CBD5E1] hover:underline"
          >
            {skipLabel}
          </button>
        )}
        <button
          type="button"
          onClick={onNext}
          disabled={nextDisabled || nextBusy}
          className="rounded-lg bg-[#6366F1] px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:bg-[#6366F1]/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {nextBusy ? "Guardando…" : nextLabel}
        </button>
      </div>
    </div>
  );
}
