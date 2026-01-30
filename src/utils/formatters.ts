export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
};

export const formatScore = (score: number | string | undefined, decimals: number = 2): string => {
  if (score === undefined || score === null) return '0.00';
  const num = typeof score === 'string' ? parseFloat(score) : score;
  if (isNaN(num)) return '0.00';
  return num.toFixed(decimals);
};

export const formatPercentage = (value: number, decimals: number = 0): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export const pluralize = (count: number, singular: string, plural?: string): string => {
  if (count === 1) return `${count} ${singular}`;
  return `${count} ${plural || singular + 's'}`;
};

export const formatElementType = (type: string, maxLength: number = 6): string => {
  return type.slice(0, maxLength);
};

export const formatChunkId = (id: string): string => {
  // Extract filename part if possible, otherwise truncate hash
  const parts = id.split('_');
  if (parts.length > 1) {
    // Attempt to show a cleaner identifier (e.g. "Doc_A1B2...")
    const last = parts[parts.length - 1];
    return `Ref_${last.substring(0, 8)}`;
  }
  return `Ref_${id.substring(0, 8)}`;
};
