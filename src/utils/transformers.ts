import { Chunk, PartitionElement, PipelineMetrics } from '../types';

export const transformElement = (apiElement: any): PartitionElement => {
  return {
    type: apiElement.type || 'Unknown',
    text: apiElement.text || apiElement.content || '',
    prob: apiElement.prob || 0.95,
    page: apiElement.page || 1,
  };
};

export const transformElements = (apiElements: any[]): PartitionElement[] => {
  return apiElements.map(transformElement);
};

export const transformChunk = (apiChunk: any, index: number): Chunk => {
  return {
    id: apiChunk.id || `chk_${index}`,
    type: apiChunk.images?.length > 0 ? 'mixed' : 'text',
    content: apiChunk.content || '',
    originalContent: apiChunk.originalContent || apiChunk.content || '',
    images: apiChunk.images || [],
    tables: apiChunk.tables || [],
    page: apiChunk.page || 1,
    score: apiChunk.score || 0,
    scores: apiChunk.scores || { bm25: 0, vector: 0 },
  };
};

export const transformChunks = (apiChunks: any[]): Chunk[] => {
  return apiChunks.map((chunk, index) => transformChunk(chunk, index));
};

export const transformPipelineReport = (report: any): PipelineMetrics => {
  return {
    elements: report.total_elements || 0,
    chunks: report.total_chunks || 0,
    images: report.total_images || 0,
    tables: report.total_tables || 0,
  };
};

export const normalizeImageUrl = (img: string | any): string => {
  if (typeof img !== 'string') return '';

  const isDataUrl = img.startsWith('data:image');
  if (isDataUrl) return img;

  return img.startsWith('http') ? img : `data:image/jpeg;base64,${img}`;
};

export const normalizeChunk = (chunk: Chunk): Chunk => {
  return {
    ...chunk,
    images: (chunk.images || []).map(normalizeImageUrl),
  };
};

export const extractRetrievedChunks = (chatResponse: any): Chunk[] => {
  return (
    chatResponse.retrievedChunks?.map((chunk: any) => ({
      id: chunk.id,
      type: chunk.images?.length > 0 ? 'mixed' : 'text',
      content: chunk.content,
      originalContent: chunk.content,
      images: chunk.images || [],
      tables: [],
      page: chunk.page || 1,
      score: chunk.score || 0,
      scores: chunk.scores || { bm25: 0, vector: 0 },
    })) || []
  );
};
