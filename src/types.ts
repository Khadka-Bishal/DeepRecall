export type PipelineStep =
  | 'idle'
  | 'uploading'
  | 'partitioning'
  | 'chunking'
  | 'summarizing'
  | 'vectorizing'
  | 'complete';

export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  retrievedChunks?: Chunk[];
};

export type Chunk = {
  id: string;
  type: 'text' | 'mixed';
  content: string;
  originalContent?: string;
  images?: string[];
  tables?: string[];
  page: number;
  score: number;
  scores?: {
    bm25: number;
    vector: number;
    cross_encoder?: number;
  };
};

export type PartitionElement = {
  type: string;
  text: string;
  prob: number;
  page: number;
  image?: string | null;
};

export type PipelineMetrics = {
  elements: number;
  chunks: number;
  images: number;
  tables: number;
};
