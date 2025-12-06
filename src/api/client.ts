import { API_CONFIG } from '../utils/constants';

export class ApiError extends Error {
  constructor(message: string, public statusCode?: number, public data?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    let errorMessage = `Request failed: ${response.statusText}`;
    let errorData = null;

    try {
      errorData = await response.json();
      errorMessage = errorData.message || errorData.error || errorMessage;
    } catch {
      // If response body is not JSON, use status text
    }

    throw new ApiError(errorMessage, response.status, errorData);
  }

  return await response.json();
};

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.INGEST}`, {
      method: 'POST',
      body: formData,
    });

    return await handleResponse(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to upload file. Please check your connection and try again.');
  }
};

export const chatQuery = async (query: string) => {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHAT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    return await handleResponse(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to process query. Please check your connection and try again.');
  }
};

export const chatQueryStream = async (
  query: string,
  onQueries: (queries: string[]) => void,
  onChunks: (chunks: any[]) => void,
  onToken: (token: string) => void,
  onDone: (fullAnswer: string) => void,
  onError: (error: string) => void
) => {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHAT_STREAM}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new ApiError(`Stream request failed: ${response.statusText}`, response.status);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new ApiError('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE messages
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            switch (data.type) {
              case 'queries':
                onQueries(data.data);
                break;
              case 'chunks':
                onChunks(data.data);
                break;
              case 'token':
                onToken(data.data);
                break;
              case 'done':
                onDone(data.data);
                break;
              case 'error':
                onError(data.data);
                break;
            }
          } catch (e) {
            // Ignore JSON parse errors for incomplete data
          }
        }
      }
    }
  } catch (error) {
    if (error instanceof ApiError) {
      onError(error.message);
    } else {
      onError('Failed to stream response. Please check your connection.');
    }
  }
};

export const healthCheck = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
};
