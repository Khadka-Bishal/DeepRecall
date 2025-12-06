import { useEffect, useMemo, useState } from 'react';
import { Message, PipelineStep, PipelineMetrics, PartitionElement, Chunk } from '../types';
import { uploadFile, chatQueryStream, ApiError } from '../api/client';
import {
  PIPELINE_STEPS,
  transformElements,
  transformChunks,
  transformPipelineReport,
} from '../utils';
import { createUserMessage, createAssistantMessage, createErrorMessage } from '../services';

export const useRAG = () => {
  // Pipeline State
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStep>(
    PIPELINE_STEPS.IDLE as PipelineStep
  );
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<PipelineMetrics>({
    elements: 0,
    chunks: 0,
    images: 0,
    tables: 0,
  });
  const [realElements, setRealElements] = useState<PartitionElement[]>([]);
  const [realChunks, setRealChunks] = useState<Chunk[]>([]);

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [expandedQueries, setExpandedQueries] = useState<string[]>([]);

  // Minimal WebSocket listener for live pipeline stages
  const wsUrl = useMemo(() => {
    try {
      const base = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000';
      const asWs = base.replace(/^http/, 'ws');
      return `${asWs}/ws`;
    } catch {
      return 'ws://localhost:8000/ws';
    }
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {};
      ws.onerror = (err) => {};
      ws.onclose = () => {};
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);

          if (msg?.type === 'pipeline' && typeof msg?.stage === 'string') {
            const stage = msg.stage.toLowerCase();
            if (
              stage === 'uploading' ||
              stage === 'partitioning' ||
              stage === 'chunking' ||
              stage === 'summarizing' ||
              stage === 'vectorizing' ||
              stage === 'complete'
            ) {
              setPipelineStatus(stage as PipelineStep);
            }

            // Update counts from WebSocket broadcasts (live updates before HTTP response)
            if (msg.status === 'complete' && typeof msg.count === 'number') {
              if (stage === 'partitioning') {
                setMetrics((prev) => ({ ...prev, elements: msg.count }));
              } else if (stage === 'chunking') {
                setMetrics((prev) => ({ ...prev, chunks: msg.count }));
              }
            }

            // Capture image/table counts from COMPLETE message for summary
            if (stage === 'complete' && msg.status === 'complete') {
              if (typeof msg.images === 'number') {
                setMetrics((prev) => ({ ...prev, images: msg.images }));
              }
              if (typeof msg.tables === 'number') {
                setMetrics((prev) => ({ ...prev, tables: msg.tables }));
              }
            }
          }
        } catch (e) {}
      };
    } catch (err) {}
    return () => {
      try {
        ws?.close();
      } catch {
        // noop
      }
    };
  }, [wsUrl]);

  const handleUpload = async (file: File) => {
    setUploadedFile(file.name);
    setPipelineStatus(PIPELINE_STEPS.UPLOADING as PipelineStep);

    try {
      // Upload file - WebSocket will update pipeline status in real-time
      const result = await uploadFile(file);

      // Process report data
      if (result && typeof result === 'object' && 'pipeline_report' in result) {
        const report = (result as any).pipeline_report;

        // Transform metrics
        setMetrics(transformPipelineReport(report));

        // Transform elements
        if (report.elements) {
          setRealElements(transformElements(report.elements));
        }

        // Transform chunks
        if (report.chunks) {
          setRealChunks(transformChunks(report.chunks));
        }
      }

      // No manual status updates - WebSocket handles all pipeline stages
    } catch (error) {
      const errorMessage =
        error instanceof ApiError
          ? error.message
          : 'Failed to upload file. Ensure backend is running.';

      alert(errorMessage);
      setPipelineStatus(PIPELINE_STEPS.IDLE as PipelineStep);
      setUploadedFile(null);
    }
  };

  const sendMessage = async (text: string) => {
    const newUserMsg = createUserMessage(text);
    setMessages((prev) => [...prev, newUserMsg]);
    setIsTyping(true);
    setExpandedQueries([]); // Clear previous queries

    // Create a placeholder message that we'll update with streaming content
    const streamingMsgId = `streaming-${Date.now()}`;
    let streamedContent = '';
    let retrievedChunks: any[] = [];

    // Add empty assistant message that we'll update
    const placeholderMsg = createAssistantMessage('', []);
    placeholderMsg.id = streamingMsgId;
    setMessages((prev) => [...prev, placeholderMsg]);

    try {
      await chatQueryStream(
        text,
        // onQueries - received expanded queries
        (queries) => {
          setExpandedQueries(queries);
        },
        // onChunks - received retrieved chunks
        (chunks) => {
          retrievedChunks = chunks
            .map((chunk: any) => ({
              id: chunk.id,
              content: chunk.content,
              images: chunk.images || [],
              score: chunk.score,
              scores: chunk.scores,
              page: chunk.page,
            }))
            .sort((a: any, b: any) => b.score - a.score);
          // Update message with chunks (content still empty)
          setMessages((prev) =>
            prev.map((msg) => (msg.id === streamingMsgId ? { ...msg, retrievedChunks } : msg))
          );
        },
        // onToken - stream each token
        (token) => {
          // Hide "processing" indicator once streaming starts
          setIsTyping(false);
          streamedContent += token;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMsgId ? { ...msg, content: streamedContent } : msg
            )
          );
        },
        // onDone - streaming complete
        (fullAnswer) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMsgId ? { ...msg, content: fullAnswer, retrievedChunks } : msg
            )
          );
          setIsTyping(false);
        },
        // onError
        (error) => {
          setMessages((prev) => prev.filter((msg) => msg.id !== streamingMsgId));
          const errorMsg = createErrorMessage(error);
          setMessages((prev) => [...prev, errorMsg]);
          setIsTyping(false);
        }
      );
    } catch (error) {
      const errorMessage =
        error instanceof ApiError
          ? error.message
          : 'Error: Failed to connect to DeepRecall backend.';

      // Remove placeholder and add error
      setMessages((prev) => prev.filter((msg) => msg.id !== streamingMsgId));
      const errorMsg = createErrorMessage(errorMessage);
      setMessages((prev) => [...prev, errorMsg]);
      setIsTyping(false);
    }
  };

  const resetState = () => {
    setMessages([]);
    setUploadedFile(null);
    setPipelineStatus(PIPELINE_STEPS.IDLE as PipelineStep);
    setMetrics({ elements: 0, chunks: 0, images: 0, tables: 0 });
    setRealElements([]);
    setRealChunks([]);
    setExpandedQueries([]);
  };

  return {
    pipelineStatus,
    uploadedFile,
    metrics,
    realElements,
    realChunks,
    messages,
    isTyping,
    expandedQueries,
    handleUpload,
    sendMessage,
    resetState,
  };
};
