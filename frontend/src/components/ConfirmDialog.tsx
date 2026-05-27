import { useState } from "react";
import { CheckCircle2, X } from "lucide-react";
import type { PreviewData } from "../types";

interface Props {
  preview: PreviewData;
  onConfirm: (data: PreviewData) => void;
  onCancel: () => void;
}

interface Field {
  key: keyof PreviewData;
  label: string;
  placeholder: string;
}

const FIELDS: Field[] = [
  { key: "project_name", label: "Projektname",      placeholder: "z. B. Neubau Assamstadt" },
  { key: "date",         label: "Datum",             placeholder: "z. B. 20.05.2026" },
  { key: "street",       label: "Straße / Hausnr.",  placeholder: "z. B. Musterstraße 12" },
  { key: "plz",          label: "PLZ",               placeholder: "z. B. 97959" },
  { key: "city",         label: "Ort",               placeholder: "z. B. Assamstadt" },
  { key: "kwp",          label: "Anlagenleistung",   placeholder: "z. B. 157,50 kWp" },
];

export default function ConfirmDialog({ preview, onConfirm, onCancel }: Props) {
  const [form, setForm] = useState<PreviewData>({ ...preview });

  const handleChange = (key: keyof PreviewData, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    /* Backdrop */
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      {/* Dialog */}
      <div className="relative w-full max-w-lg mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="bg-[#0C2561] px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-white font-semibold text-base">
              Projektdaten prüfen
            </h2>
            <p className="text-blue-200 text-xs mt-0.5">
              Automatisch erkannte Daten – bitte prüfen und ggf. korrigieren
            </p>
          </div>
          <button
            onClick={onCancel}
            className="text-blue-200 hover:text-white transition-colors"
            aria-label="Abbrechen"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Amber accent bar */}
        <div className="h-1 bg-[#F5A31F]" />

        {/* Form */}
        <div className="px-6 py-5 space-y-4">
          {FIELDS.map(({ key, label, placeholder }) => (
            <div key={key}>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                {label}
              </label>
              <input
                type="text"
                value={(form[key] as string) ?? ""}
                placeholder={placeholder}
                onChange={(e) => handleChange(key, e.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2
                           text-sm text-gray-800 placeholder-gray-300
                           focus:outline-none focus:ring-2 focus:ring-[#009BA5] focus:border-transparent
                           transition"
              />
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="px-6 pb-5 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600
                       border border-gray-200 hover:bg-gray-100 transition"
          >
            Abbrechen
          </button>
          <button
            onClick={() => onConfirm(form)}
            className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold
                       bg-[#009BA5] text-white hover:bg-[#007f88] transition shadow-sm"
          >
            <CheckCircle2 className="w-4 h-4" />
            Bestätigen &amp; Verarbeiten
          </button>
        </div>
      </div>
    </div>
  );
}
