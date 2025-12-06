import { validateFileUpload } from '../utils/validators';

export const selectFile = (onFileSelected: (file: File) => void): void => {
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.pdf';

  fileInput.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) {
      const validation = validateFileUpload(file);
      if (!validation.valid) {
        alert(validation.error);
        return;
      }
      onFileSelected(file);
    }
  };

  fileInput.click();
};

export const getFileExtension = (filename: string): string => {
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2);
};

export const getFileNameWithoutExtension = (filename: string): string => {
  return filename.replace(/\.[^/.]+$/, '');
};
