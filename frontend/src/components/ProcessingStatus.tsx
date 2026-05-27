import { useEffect, useState } from "react";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { getReportStatus } from "../services/api";
import type { ReportStatus } from "../types";

interface Props {
  reportId: number;
  onDone: () => void;
}

export default function ProcessingStatus({ reportId, onDone }: Props) {
  const [status, setStatus] = useState<ReportStatus>("processing");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const res = await getReportStatus(reportId);
        if (cancelled) return;
        setStatus(res.status);
        if (res.status === "processing") {
          setTimeout(poll, 2500);
        } else {
          if (res.status === "error") setErrorMsg(res.error_message);
          onDone();
        }
      } catch {
        if (!cancelled) setTimeout(poll, 3000);
      }
    };

    poll();
    return () => {
      cancelled = true;
    };
  }, [reportId, onDone]);

  if (status === "processing") {
    return (
      <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl">
        <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
        <div>
          <p className="text-sm font-semibold text-blue-800">
            Bericht wird optimiert…
          </p>
          <p className="text-xs text-blue-600 mt-0.5">
            Bitte warten, dies kann einige Sekunden dauern.
          </p>
        </div>
      </div>
    );
  }

  if (status === "done") {
    return (
      <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-xl">
        <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
        <p className="text-sm font-semibold text-green-800">
          Optimierung abgeschlossen – Bericht steht zum Download bereit.
        </p>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
      <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
      <div>
        <p className="text-sm font-semibold text-red-800">
          Verarbeitung fehlgeschlagen.
        </p>
        {errorMsg && (
          <p className="text-xs text-red-600 mt-0.5 font-mono">{errorMsg}</p>
        )}
      </div>
    </div>
  );
}
