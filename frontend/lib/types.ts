export interface FieldMetadata {
  type: string;
  label: string;
  required: boolean;
  description?: string;
  placeholder?: string;
  options?: string[];
}

export interface TemplateMetadata {
  name: string;
  filename: string;
  fields: Record<string, FieldMetadata>;
}

export interface DocumentResponse {
  document_id: string;
  filename: string;
  download_url: string;
  created_at: string;
}

export interface ApiError {
  error: string;
  detail?: string;
  missing_fields?: string[];
}

export interface AuthUser {
  id: number;
  email: string;
}

export interface AuthResponse {
  message: string;
  user: AuthUser;
}
