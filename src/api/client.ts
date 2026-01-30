/**
 * API Client for DeepRecall Backend
 * Handles file upload and chat streaming
 */

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Custom API Error class
 */
export class ApiError extends Error {
  status: number;
  
  constructor(message: string, status: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}


/**
 * Get or create a persistent session ID
 */
function getSessionId(): string {
  let sid = localStorage.getItem('deeprecall_session_id');
  if (!sid) {
    sid = crypto.randomUUID();
    localStorage.setItem('deeprecall_session_id', sid);
  }
  return sid;
}

/**
 * Upload a file to the ingestion endpoint
 * @param file - The file to upload
 * @returns The pipeline report and performance metrics
 */
export async function uploadFile(file: File): Promise<{
  status: string;
  filename: string;
  pipeline_report: {
    elements: any[];
    chunks: any[];
    total_elements: number;
    total_chunks: number;
    total_images: number;
    total_tables: number;
  };
  performance: {
    duration_seconds: number;
    throughput_mb_s: number;
  };
}> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/ingest`, {
    method: 'POST',
    headers: {
      'X-Session-ID': getSessionId(),
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(errorText || 'Upload failed', response.status);
  }

  return response.json();
}

/**
 * Stream chat response with query expansion and chunk retrieval
 * @param query - The user's query
 * @param onQueries - Callback when expanded queries are received
 * @param onChunks - Callback when retrieved chunks are received
 * @param onToken - Callback for each streamed token
 * @param onDone - Callback when streaming completes with final answer
 * @param onError - Callback for errors
 */
export async function chatQueryStream(
  query: string,
  onQueries: (queries: string[]) => void,
  onChunks: (chunks: any[]) => void,
  onToken: (token: string) => void,
  onDone: (fullAnswer: string) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': getSessionId(),
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      onError(errorText || 'Chat request failed');
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError('No response body');
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let fullAnswer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      // Process SSE events
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            onDone(fullAnswer);
            return;
          }

          try {
            const parsed = JSON.parse(data);
            
            // Handle different event types
            if (parsed.type === 'error') {
              onError(parsed.data || parsed.content || 'Stream Error');
              return; 
            } else if (parsed.type === 'queries' && parsed.queries) {
              onQueries(parsed.queries);
            } else if (parsed.type === 'chunks' && parsed.chunks) {
              onChunks(parsed.chunks);
            } else if (parsed.type === 'done') {
               // Do nothing, let the loop finish or handle explicitly
               // The generic [DONE] check at the start handles the stream end, 
               // but if we send a JSON 'done' event, we should stop accumulating.
               return;
            } else if (parsed.type === 'token' && parsed.content) {
              fullAnswer += parsed.content;
              onToken(parsed.content);
            } else if (parsed.content) {
              // Legacy format - direct content
              fullAnswer += parsed.content;
              onToken(parsed.content);
            }
          } catch {
            // Not JSON, treat as raw text token
            if (data.trim()) {
              fullAnswer += data;
              onToken(data);
            }
          }
        }
      }
    }

    // If we exit without [DONE], still call onDone
    onDone(fullAnswer);
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Unknown error');
  }
}
