import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import profinextLogo from "./assets/ProfiNEXT_Logo_RGB.jpg";
import UploadSection from "./components/UploadSection";
import ArchiveTable from "./components/ArchiveTable";
import ProcessingStatus from "./components/ProcessingStatus";
import { listReports } from "./services/api";
import type { Report, UploadResponse } from "./types";

export default function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeJobs, setActiveJobs] = useState<number[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchReports = useCallback(async () => {
    try {
      const data = await listReports();
      setReports(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  // Auto-refresh list while processing jobs are active
  useEffect(() => {
    if (activeJobs.length > 0) {
      pollRef.current = setInterval(fetchReports, 3000);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [activeJobs, fetchReports]);

  const handleUploaded = useCallback(
    (res: UploadResponse) => {
      setActiveJobs((prev) => [...prev, res.id]);
      fetchReports();
    },
    [fetchReports]
  );

  const handleJobDone = useCallback(
    (id: number) => {
      setActiveJobs((prev) => prev.filter((j) => j !== id));
      fetchReports();
    },
    [fetchReports]
  );

  const handleDeleted = useCallback((id: number) => {
    setReports((prev) => prev.filter((r) => r.id !== id));
    setActiveJobs((prev) => prev.filter((j) => j !== id));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#0C2561] text-white shadow-lg">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              Projektbericht Optimizer
            </h1>
            <p className="text-sm text-blue-200 mt-0.5">
              PROFINEXT Montagesysteme
            </p>
          </div>
          <div className="h-1 w-20 rounded-full bg-[#F5A31F]" />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10 space-y-10">
        {/* Logo oben links im Arbeitsbereich */}
        <div className="flex justify-start">
          <img
            src={profinextLogo}
            alt="PROFINEXT Logo"
            className="h-14 object-contain"
            style={{ mixBlendMode: "multiply" }}
          />
        </div>
        {/* Upload */}
        <section>
          <h2 className="text-lg font-semibold text-[#0C2561] mb-4">
            Neuen Bericht hochladen
          </h2>
          <UploadSection onUploaded={handleUploaded} />
        </section>

        {/* Active processing banners */}
        {activeJobs.length > 0 && (
          <section className="space-y-3">
            {activeJobs.map((id) => (
              <ProcessingStatus
                key={id}
                reportId={id}
                onDone={() => handleJobDone(id)}
              />
            ))}
          </section>
        )}

        {/* Archive */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[#0C2561]">
              Archiv ({reports.length})
            </h2>
            <button
              onClick={fetchReports}
              className="flex items-center gap-2 text-sm text-gray-500 hover:text-[#009BA5] transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Aktualisieren
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-16">
              <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
            </div>
          ) : (
            <ArchiveTable reports={reports} onDeleted={handleDeleted} />
          )}
        </section>
      </main>
    </div>
  );
}
