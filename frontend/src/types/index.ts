export interface ReviewFlag {
  rule_id: string;
  severity: string;
  issue: string;
  contract_value: string | null;
  required_value: string | null;
  explanation: string;
}

export interface ReviewResponse {
  status: string;
  summary: string;
  flags: ReviewFlag[];
}

export interface ContractDetails {
  contract_id?: string;
  contract_name: string;
  contract_amount: number | null;
  tax_rate: number | null;
  effective_date: string | null;
  completion_date: string | null;
  file_url: string | null;
  start_date?: string | null;
  end_date?: string | null;
  created_at?: string;
}

export interface InvoiceDetails {
  invoice_id: string;
  contract_name: string;
  invoice_amount: number;
  invoice_tax: number;
  due_date: string;
  status: string;
  paid_date: string | null;
}

export interface InvoiceValidation {
  invoice_id: string;
  contract_id: string;
  is_valid: boolean;
  amount_valid: boolean;
  tax_valid: boolean;
  contract_amount: number;
  invoice_amount: number;
  expected_tax: number;
  invoice_tax: number;
  status: string;
  issues: string[];
}

export interface ChatResponse {
  document_type?: 'contract' | 'invoice';
  action?: 'review_contract' | 'save_contract' | 'validate_invoice' | 'save_invoice' | 'text_to_sql' | string;
  message?: string;
  contract?: ContractDetails;
  review?: ReviewResponse;
  invoice?: InvoiceDetails;
  validation?: InvoiceValidation;
  save_result?: Record<string, any>;
  contract_id?: string;
  generated_sql?: string;
  results?: any[];
  pending_action?: 'confirm_save_contract' | 'confirm_save_invoice' | string | null;
  already_saved?: boolean;
}
