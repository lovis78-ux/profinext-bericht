import { useRef, useState, useCallback } from "react";
import { UploadCloud, FileText, Loader2 } from "lucide-react";
import { previewUpload, confirmUpload } from "../services/api";
import ConfirmDialog from "./ConfirmDialog";
import type { PreviewData, UploadResponse } from "../types";

interface Props {
  onUploaded: (res: UploadResponse) => void;
}

export default function UploadSection({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);   // while fetching preview
  const [confirming, setConfirming] = useState(false); // while running pipeline
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Step 1: upload file and show confirmation dialog ──────────────────
  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Nur PDF-Dateien erlaubt.");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const data = await previewUpload(file);
      setPreview(data);
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload fehlgeschlagen.";
      setError(msg);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }, []);

  // ── Step 2a: user confirmed (possibly edited) data ────────────────────
  const handleConfirm = useCallback(
    async (confirmed: PreviewData) => {
      setPreview(null);
      setConfirming(true);
      try {
        const res = await confirmUpload(confirmed);
        onUploaded(res);
      } catch (e: unknown) {
        const msg =
          (e as { response?: { data?: { detail?: string } } })?.response?.data
            ?.detail ?? "Verarbeitung konnte nicht gestartet werden.";
        setError(msg);
      } finally {
        setConfirming(false);
      }
    },
    [onUploaded]
  );

  // ── Step 2b: user cancelled dialog ───────────────────────────────────
  const handleCancel = useCallback(() => {
    setPreview(null);
  }, []);

  // ── Drag & drop / click handlers ──────────────────────────────────────
  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const busy = uploading || confirming;

  return (
    <>
      {/* Confirmation dialog (rendered in portal-style overlay) */}
      {preview && (
        <ConfirmDialog
          preview={preview}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}

      <div className="w-full max-w-2xl mx-auto">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => !busy && inputRef.current?.click()}
          className={`
            relative flex flex-col items-center justify-center gap-4
            border-2 border-dashed rounded-2xl p-12 cursor-pointer
            transition-all duration-200 select-none
            ${dragging ? "border-[#009BA5] bg-teal-50" : "border-gray-300 bg-gray-50 hover:border-[#009BA5] hover:bg-teal-50"}
            ${busy ? "pointer-events-none opacity-70" : ""}
          `}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={onInputChange}
          />

          {uploading ? (
            <>
              <Loader2 className="w-12 h-12 text-[#009BA5] animate-spin" />
              <p className="text-lg font-medium text-gray-600">
                Datei wird gelesen…
              </p>
            </>
          ) : confirming ? (
            <>
              <Loader2 className="w-12 h-12 text-[#009BA5] animate-spin" />
              <p className="text-lg font-medium text-gray-600">
                Verarbeitung wird gestartet…
              </p>
            </>
          ) : (
            <>
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-[#009BA5]/10">
                {dragging ? (
                  <FileText className="w-8 h-8 text-[#009BA5]" />
                ) : (
                  <UploadCloud className="w-8 h-8 text-[#009BA5]" />
                )}
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-gray-800">
                  {dragging
                    ? "PDF loslassen"
                    : "PDF-Bericht hier ablegen oder klicken"}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Nur .pdf-Dateien • Profinal-Format
                </p>
              </div>
            </>
          )}
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-600 text-center">{error}</p>
        )}
      </div>
    </>
  );
}
