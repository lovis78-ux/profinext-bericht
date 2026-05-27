import { useState } from "react";
import {
  Download,
  Trash2,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  FileDown,
  Eye,
} from "lucide-react";
import { deleteReport, downloadOriginalUrl, downloadOptimizedUrl } from "../services/api";
import type { Report } from "../types";

interface Props {
  reports: Report[];
  onDeleted: (id: number) => void;
  onPreview: (report: Report) => void;
  previewId: number | null;
}

const STATUS_ICONS = {
  processing: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
  done: <CheckCircle2 className="w-4 h-4 text-green-500" />,
  error: <XCircle className="w-4 h-4 text-red-500" />,
};

const STATUS_LABELS = {
  processing: "Verarbeitung",
  done: "Fertig",
  error: "Fehler",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ArchiveTable({ reports, onDeleted, onPreview, previewId }: Props) {
  const [deleting, setDeleting] = useState<number | null>(null);

  const handleDelete = async (id: number) => {
    if (!window.confirm("Vorgang wirklich löschen?")) return;
    setDeleting(id);
    try {
      await deleteReport(id);
      onDeleted(id);
    } finally {
      setDeleting(null);
    }
  };

  if (reports.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-gray-400">
        <Clock className="w-10 h-10 mb-3" />
        <p className="text-sm">Noch keine Berichte vorhanden.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[#0C2561] text-white">
            <th className="text-left px-4 py-3 font-semibold">Dateiname</th>
            <th className="text-left px-4 py-3 font-semibold">Projekt</th>
            <th className="text-left px-4 py-3 font-semibold hidden md:table-cell">Adresse</th>
            <th className="text-left px-4 py-3 font-semibold hidden lg:table-cell">kWp</th>
            <th className="text-left px-4 py-3 font-semibold hidden lg:table-cell">Erstellt</th>
            <th className="text-center px-4 py-3 font-semibold">Status</th>
            <th className="text-center px-4 py-3 font-semibold">Aktionen</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {reports.map((r) => {
            const isActive = r.id === previewId;
            return (
              <tr
                key={r.id}
                className={`transition-colors ${
                  isActive
                    ? "bg-teal-50 border-l-4 border-l-[#009BA5]"
                    : "hover:bg-gray-50"
                }`}
              >
                <td className="px-4 py-3 max-w-[180px] truncate text-gray-700">
                  <span title={r.original_filename}>{r.original_filename}</span>
                </td>
                <td className="px-4 py-3 text-gray-700">
                  {r.project_name ?? <span className="text-gray-400">–</span>}
                </td>
                <td className="px-4 py-3 text-gray-600 hidden md:table-cell">
                  {r.address ?? <span className="text-gray-400">–</span>}
                </td>
                <td className="px-4 py-3 text-gray-600 hidden lg:table-cell">
                  {r.kwp ? `${r.kwp} kWp` : <span className="text-gray-400">–</span>}
                </td>
                <td className="px-4 py-3 text-gray-500 hidden lg:table-cell whitespace-nowrap">
                  {formatDate(r.created_at)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center gap-1.5">
                    {STATUS_ICONS[r.status]}
                    <span
                      className={`text-xs font-medium ${
                        r.status === "done"
                          ? "text-green-600"
                          : r.status === "error"
                          ? "text-red-600"
                          : "text-blue-600"
                      }`}
                    >
                      {STATUS_LABELS[r.status]}
                    </span>
                  </div>
                  {r.status === "error" && r.error_message && (
                    <p
                      className="text-xs text-red-400 text-center mt-0.5 truncate max-w-[120px]"
                      title={r.error_message}
                    >
                      {r.error_message}
                    </p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center gap-2">
                    {/* Vorschau (nur für fertige Berichte) */}
                    {r.status === "done" && (
                      <button
                        onClick={() => onPreview(r)}
                        title="Vorschau anzeigen"
                        className={`p-1.5 rounded-lg transition-colors ${
                          isActive
                            ? "bg-teal-100 text-[#009BA5]"
                            : "text-gray-400 hover:text-[#009BA5] hover:bg-teal-50"
                        }`}
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    )}

                    {/* Original herunterladen */}
                    <a
                      href={downloadOriginalUrl(r.id)}
                      download
                      title="Original herunterladen"
                      className="p-1.5 rounded-lg text-gray-500 hover:text-[#0C2561] hover:bg-gray-100 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                    </a>

                    {/* Optimierten Bericht herunterladen */}
                    {r.status === "done" && (
                      <a
                        href={downloadOptimizedUrl(r.id)}
                        download
                        title="Optimierten Bericht herunterladen"
                        className="p-1.5 rounded-lg text-[#009BA5] hover:text-[#0C2561] hover:bg-teal-50 transition-colors"
                      >
                        <FileDown className="w-4 h-4" />
                      </a>
                    )}

                    {/* Löschen */}
                    <button
                      onClick={() => handleDelete(r.id)}
                      disabled={deleting === r.id}
                      title="Löschen"
                      className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-40"
                    >
                      {deleting === r.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
