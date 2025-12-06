import { FILE_CONFIG } from './constants';

export const isValidFileType = (file: File): boolean => {
  return file.type === 'application/pdf' || file.name.endsWith('.pdf');
};

export const isValidFileSize = (file: File): boolean => {
  return file.size <= FILE_CONFIG.MAX_FILE_SIZE;
};

export const validateFileUpload = (file: File): { valid: boolean; error?: string } => {
  if (!isValidFileType(file)) {
    return { valid: false, error: 'Only PDF files are accepted.' };
  }

  if (!isValidFileSize(file)) {
    return {
      valid: false,
      error: `File size must be less than ${FILE_CONFIG.MAX_FILE_SIZE / (1024 * 1024)}MB.`,
    };
  }

  return { valid: true };
};

export const isValidQuery = (query: string): boolean => {
  return query.trim().length > 0;
};

export const sanitizeInput = (input: string): string => {
  return input.trim();
};
