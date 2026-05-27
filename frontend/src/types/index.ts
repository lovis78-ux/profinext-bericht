export type ReportStatus = "processing" | "done" | "error";

export interface PreviewData {
  file_id: string;
  original_filename: string;
  project_name: string;
  date: string;
  plz: string;
  city: string;
  street: string;
  kwp: string;
}

export interface Report {
  id: number;
  original_filename: string;
  project_name: string | null;
  address: string | null;
  kwp: string | null;
  report_date: string | null;
  status: ReportStatus;
  error_message: string | null;
  created_at: string;
}

export interface UploadResponse {
  id: number;
  status: ReportStatus;
}

export interface StatusResponse {
  id: number;
  status: ReportStatus;
  error_message: string | null;
}
