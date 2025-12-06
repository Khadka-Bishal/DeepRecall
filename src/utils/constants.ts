// API Configuration
export const API_CONFIG = {
  BASE_URL: (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000',
  ENDPOINTS: {
    INGEST: '/ingest',
    CHAT: '/chat',
    CHAT_STREAM: '/chat/stream',
  },
  TIMEOUT: 30000,
} as const;

// Pipeline Configuration
export const PIPELINE_STEPS = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  PARTITIONING: 'partitioning',
  CHUNKING: 'chunking',
  SUMMARIZING: 'summarizing',
  VECTORIZING: 'vectorizing',
  COMPLETE: 'complete',
} as const;

export const PIPELINE_STEP_DELAYS = {
  CHUNKING: 800,
  SUMMARIZING: 800,
  VECTORIZING: 800,
} as const;

// UI Configuration
export const UI_CONFIG = {
  MAX_TEXTAREA_HEIGHT: 200,
  MIN_TEXTAREA_HEIGHT: 48,
  MAX_FILENAME_DISPLAY: 100,
} as const;

// Color Schemes
export const ELEMENT_COLORS = {
  Title: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/20',
  },
  Table: {
    bg: 'bg-orange-500/10',
    text: 'text-orange-400',
    border: 'border-orange-500/20',
  },
  Image: {
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    border: 'border-purple-500/20',
  },
  Default: {
    bg: 'bg-zinc-800',
    text: 'text-zinc-500',
    border: 'border-zinc-700',
  },
} as const;

export const STATUS_COLORS = {
  pending: {
    bg: 'bg-transparent',
    border: 'border-zinc-800',
    text: 'text-zinc-700',
  },
  active: {
    bg: 'bg-zinc-900',
    border: 'border-zinc-200',
    text: 'text-zinc-100',
    shadow: 'shadow-[0_0_10px_rgba(255,255,255,0.1)]',
  },
  complete: {
    bg: 'bg-zinc-900',
    border: 'border-zinc-700',
    text: 'text-zinc-400',
  },
} as const;

// File Configuration
export const FILE_CONFIG = {
  ACCEPTED_TYPES: '.pdf',
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
} as const;

// Vector Configuration
export const VECTOR_CONFIG = {
  DIMENSIONS: 1536,
  SIMILARITY_METRIC: 'Cosine Similarity',
} as const;

// Message Roles
export const MESSAGE_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
} as const;
