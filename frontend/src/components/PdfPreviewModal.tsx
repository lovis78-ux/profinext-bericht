import { useEffect, useState } from "react";
import { X, FileDown } from "lucide-react";
import { downloadOptimizedUrl, viewOptimizedUrl } from "../services/api";
import type { Report } from "../types";

interface Props {
  report: Report;
  onClose: () => void;
}

export default function PdfPreviewModal({ report, onClose }: Props) {
  const [loading, setLoading] = useState(true);

  const previewUrl = viewOptimizedUrl(report.id);
  const downloadUrl = downloadOptimizedUrl(report.id);

  // Escape-Taste schließt das Modal
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  // Body-Scroll sperren während Modal offen
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-2xl flex flex-col w-full max-w-5xl h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 flex-shrink-0">
          <div className="min-w-0 flex-1 pr-4">
            <p className="text-xs text-[#009BA5] uppercase tracking-wider font-semibold mb-0.5">
              Vorschau · Optimierter Bericht
            </p>
            <h3 className="text-sm font-bold text-[#0C2561] truncate">
              {report.project_name ?? report.original_filename}
            </h3>
            {report.address && (
              <p className="text-xs text-gray-500 truncate mt-0.5">
                {report.address}
                {report.kwp ? ` · ${report.kwp} kWp` : ""}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <a
              href={downloadUrl}
              download
              title="Optimierten Bericht herunterladen"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#009BA5] hover:bg-[#007d87] text-white text-xs font-semibold rounded-lg transition-colors"
            >
              <FileDown className="w-3.5 h-3.5" />
              Herunterladen
            </a>
            <button
              onClick={onClose}
              title="Schließen (Esc)"
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* PDF-Viewer */}
        <div className="flex-1 relative bg-gray-200 rounded-b-2xl overflow-hidden">
          {loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 z-10">
              <div className="w-8 h-8 border-[3px] border-gray-300 border-t-[#009BA5] rounded-full animate-spin mb-3" />
              <p className="text-sm text-gray-400">PDF wird geladen…</p>
            </div>
          )}
          <iframe
            src={previewUrl}
            className="w-full h-full border-0 rounded-b-2xl"
            onLoad={() => setLoading(false)}
            title={`Vorschau: ${report.original_filename}`}
          />
        </div>
      </div>
    </div>
  );
}
