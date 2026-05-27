import axios from "axios";
import type { Report, UploadResponse, StatusResponse, PreviewData } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "";

const api = axios.create({ baseURL: BASE });

/** Step 1: upload PDF and get extracted data back for review. */
export async function previewUpload(file: File): Promise<PreviewData> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<PreviewData>("/api/upload/preview", form);
  return data;
}

/** Step 2: send confirmed (possibly edited) data to start processing. */
export async function confirmUpload(preview: PreviewData): Promise<UploadResponse> {
  const { data } = await api.post<UploadResponse>("/api/upload/confirm", preview);
  return data;
}

/** Legacy single-step upload (no confirmation dialog). */
export async function uploadReport(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<UploadResponse>("/api/upload", form);
  return data;
}

export async function listReports(): Promise<Report[]> {
  const { data } = await api.get<Report[]>("/api/reports");
  return data;
}

export async function getReportStatus(id: number): Promise<StatusResponse> {
  const { data } = await api.get<StatusResponse>(`/api/reports/${id}/status`);
  return data;
}

export async function deleteReport(id: number): Promise<void> {
  await api.delete(`/api/reports/${id}`);
}

export function downloadOriginalUrl(id: number): string {
  return `${BASE}/api/reports/${id}/download/original`;
}

export function downloadOptimizedUrl(id: number): string {
  return `${BASE}/api/reports/${id}/download/optimized`;
}
