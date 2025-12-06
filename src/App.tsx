import { useState, useRef, useEffect } from 'react';
import {
  Plus,
  UploadCloud,
  Sparkles,
  ArrowUp,
  FileText,
  Activity,
  Command,
  Cpu,
  Layers,
  Database,
  Maximize2,
} from 'lucide-react';
import { DeepRecallLogo } from './components/DeepRecallLogo';
import { DetailModal } from './components/DetailModal';
import { StepDetailView } from './components/StepDetailView';
import { PipelineStepIndicator, ElementViewer, ChunkViewer } from './components/PipelineComponents';
import { ChunkCard } from './components/ChunkCard';
import { useRAG } from './hooks/useRAG';
import { Chunk, PartitionElement } from './types';
import {
  formatTime,
  pluralize,
  normalizeChunk,
  getRoleColor,
  getRoleTextColor,
  isValidQuery,
  PIPELINE_STEPS,
  UI_CONFIG,
  VECTOR_CONFIG,
  mapStepStatus,
} from './utils';
import { buttonPrimary } from './utils/styles';
import { selectFile } from './services';

const App = () => {
  const {
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
  } = useRAG();

  const [activeTab, setActiveTab] = useState<'pipeline' | 'retrieval'>('pipeline');
  const [inputValue, setInputValue] = useState('');
  const [expandedStep, setExpandedStep] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalData, setModalData] = useState<{
    title: string;
    content: any;
    type: 'chunk' | 'element';
    metaData: any;
  } | null>(null);
  const [fullViewStep, setFullViewStep] = useState<
    { type: 'elements'; items: PartitionElement[] } | { type: 'chunks'; items: Chunk[] } | null
  >(null);

  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  useEffect(() => {
    const el = document.activeElement as HTMLElement | null;
    if (el && typeof el.blur === 'function') {
      el.blur();
    }
  }, []);

  // Keep all steps collapsed - user can expand manually
  useEffect(() => {
    if (pipelineStatus === PIPELINE_STEPS.COMPLETE) {
      setExpandedStep(null);
    }
  }, [pipelineStatus]);

  // Handlers
  const onUploadClick = () => {
    selectFile((file) => {
      handleUpload(file);
      setActiveTab('pipeline');
    });
  };

  const onSend = () => {
    if (!isValidQuery(inputValue)) return;
    sendMessage(inputValue);
    setInputValue('');
    setActiveTab('retrieval');
  };

  const openElementDetail = (el: PartitionElement) => {
    setModalData({
      title: `Element Inspection [${el.type}]`,
      content: el,
      type: 'element',
      metaData: { page: el.page, probability: el.prob },
    });
    setModalOpen(true);
  };

  const openChunkDetail = (chunk: Chunk) => {
    const normalizedChunk = normalizeChunk(chunk);
    setModalData({
      title: `Chunk Inspector [${chunk.id}]`,
      content: normalizedChunk,
      type: 'chunk',
      metaData: {
        page: chunk.page,
        score: chunk.score,
        hasImages: normalizedChunk.images?.length || 0,
        length: chunk.content.length,
      },
    });
    setModalOpen(true);
  };

  return (
    <div className="flex h-screen bg-[#09090b] text-zinc-300 font-sans overflow-hidden selection:bg-zinc-800 selection:text-zinc-100">
      {modalData && (
        <DetailModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={modalData.title}
          content={modalData.content}
          type={modalData.type}
          metaData={modalData.metaData}
        />
      )}

      {fullViewStep && (
        <StepDetailView
          isOpen={true}
          onClose={() => setFullViewStep(null)}
          title={
            fullViewStep.type === 'elements'
              ? 'Document Partitioning Analysis'
              : 'Semantic Chunking & Extraction'
          }
          data={fullViewStep}
          onInspectChunk={openChunkDetail}
          onInspectElement={openElementDetail}
        />
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative bg-[#09090b]">
        {/* Header */}
        <div className="h-14 border-b border-zinc-800 flex items-center justify-between px-6 bg-[#09090b] z-10">
          <div className="flex items-center gap-2.5 text-zinc-100 mr-4">
            <DeepRecallLogo />
          </div>
          <button
            tabIndex={-1}
            onClick={resetState}
            className="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-md border border-zinc-800 text-xs font-medium group focus:outline-none focus:ring-0"
          >
            <Plus size={14} className="text-zinc-500 group-hover:text-zinc-300" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Messages */}
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-0 scroll-smooth">
          <div className="max-w-4xl mx-auto py-8 px-6">
            {messages.length === 0 ? (
              <div className="mt-20 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-zinc-900/50 rounded-2xl flex items-center justify-center mb-6 border border-zinc-800 shadow-2xl shadow-emerald-900/10">
                  <DeepRecallLogo />
                </div>
                <h2 className="text-xl font-medium text-zinc-200 mb-2">DeepRecall</h2>
                <p className="text-zinc-500 text-sm max-w-sm leading-relaxed mb-8">
                  Upload a document to begin hybrid retrieval analysis. System handles text, tables,
                  and vector embeddings.
                </p>

                {!uploadedFile && (
                  <button
                    tabIndex={-1}
                    onClick={onUploadClick}
                    className="group flex items-center gap-3 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 px-5 py-3 rounded-md focus:outline-none focus:ring-0"
                  >
                    <UploadCloud size={16} className="text-zinc-400 group-hover:text-zinc-200" />
                    <span className="text-sm text-zinc-400 group-hover:text-zinc-200">
                      Upload PDF
                    </span>
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-8">
                {messages.map((msg) => (
                  <div key={msg.id} className="group">
                    <div className="flex items-baseline justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs font-semibold uppercase tracking-wider ${getRoleColor(
                            msg.role
                          )}`}
                        >
                          {msg.role === 'assistant' ? 'DeepRecall' : 'User'}
                        </span>
                        <span className="text-[10px] text-zinc-700 font-mono">
                          {formatTime(msg.timestamp)}
                        </span>
                      </div>
                    </div>
                    <div className={`text-sm leading-7 ${getRoleTextColor(msg.role)}`}>
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>

                    {msg.role === 'assistant' &&
                      msg.retrievedChunks &&
                      msg.retrievedChunks.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {msg.retrievedChunks.map((chunk, i) => (
                            <ChunkCard
                              key={i}
                              chunk={chunk}
                              onInspect={openChunkDetail}
                              mini={true}
                            />
                          ))}
                        </div>
                      )}
                  </div>
                ))}

                {isTyping && (
                  <div className="flex items-center gap-2 text-zinc-500">
                    <Sparkles size={14} />
                    <span className="text-xs font-mono">processing_query...</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="p-6 pt-0 bg-[#09090b] z-20">
          <div className="max-w-4xl mx-auto">
            <div className="relative bg-zinc-900/50 border border-zinc-800 rounded-lg shadow-sm">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    onSend();
                  }
                }}
                placeholder="Ask query..."
                autoFocus={false}
                className="w-full bg-transparent border-none text-zinc-200 placeholder-zinc-600 p-3 min-h-[48px] max-h-[200px] resize-none focus:ring-0 text-sm outline-none font-sans"
              />
              <div className="flex items-center justify-between px-2 pb-2">
                <div className="flex items-center gap-1">
                  {uploadedFile && (
                    <div className="flex items-center gap-2 px-2 py-1 bg-zinc-800 rounded border border-zinc-700">
                      <FileText size={12} className="text-zinc-400" />
                      <span
                        className="text-[10px] text-zinc-300 font-mono truncate"
                        style={{
                          maxWidth: `${UI_CONFIG.MAX_FILENAME_DISPLAY}px`,
                        }}
                      >
                        {uploadedFile}
                      </span>
                    </div>
                  )}
                </div>
                <button
                  onClick={onSend}
                  disabled={!inputValue.trim() || pipelineStatus !== PIPELINE_STEPS.COMPLETE}
                  className={`focus:outline-none focus:ring-0 ${buttonPrimary(
                    !inputValue.trim() || pipelineStatus !== PIPELINE_STEPS.COMPLETE
                  )}`}
                >
                  <ArrowUp size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel (Inspector) */}
      <div className="w-[400px] border-l border-zinc-800 bg-[#09090b] flex flex-col shadow-xl z-20">
        <div className="flex border-b border-zinc-800">
          <button
            tabIndex={-1}
            onClick={() => setActiveTab('pipeline')}
            className={`flex-1 py-3 text-[10px] uppercase tracking-wider font-semibold border-b focus:outline-none focus:ring-0 ${
              activeTab === 'pipeline'
                ? 'text-zinc-200 border-zinc-200'
                : 'text-zinc-600 border-transparent hover:text-zinc-400'
            }`}
          >
            Ingestion
          </button>
          <button
            tabIndex={-1}
            onClick={() => setActiveTab('retrieval')}
            className={`flex-1 py-3 text-[10px] uppercase tracking-wider font-semibold border-b focus:outline-none focus:ring-0 ${
              activeTab === 'retrieval'
                ? 'text-zinc-200 border-zinc-200'
                : 'text-zinc-600 border-transparent hover:text-zinc-400'
            }`}
          >
            Retrieval
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-0">
          {activeTab === 'pipeline' && (
            <div className="p-5">
              <div className="mb-6 flex items-center justify-between">
                <span className="text-[10px] font-mono text-zinc-500 uppercase">Status</span>
                <div className="flex items-center gap-1.5">
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${
                      pipelineStatus === PIPELINE_STEPS.IDLE
                        ? 'bg-zinc-700'
                        : 'bg-emerald-500 animate-pulse'
                    }`}
                  ></div>
                  <span className="text-[10px] font-mono text-zinc-300">
                    {pipelineStatus.toUpperCase()}
                  </span>
                </div>
              </div>

              {pipelineStatus === PIPELINE_STEPS.IDLE ? (
                <div className="text-center py-20 border border-dashed border-zinc-800 rounded-sm bg-zinc-900/20">
                  <Activity className="w-8 h-8 mx-auto mb-2 text-zinc-700" />
                  <p className="text-xs text-zinc-600 font-mono">Waiting for input...</p>
                </div>
              ) : (
                <div className="pl-2 pt-2">
                  <PipelineStepIndicator
                    label="Uploading File"
                    icon={UploadCloud}
                    status={mapStepStatus(pipelineStatus, 'uploading')}
                    details={
                      mapStepStatus(pipelineStatus, 'uploading') === 'complete'
                        ? '1 file'
                        : undefined
                    }
                    isExpanded={expandedStep === 'uploading'}
                    onToggle={
                      pipelineStatus === PIPELINE_STEPS.COMPLETE
                        ? () => setExpandedStep(expandedStep === 'uploading' ? null : 'uploading')
                        : undefined
                    }
                  >
                    <div className="bg-zinc-950 p-2 rounded border border-zinc-800 text-[9px] font-mono text-zinc-500">
                      <div className="truncate">{uploadedFile || 'No file selected'}</div>
                    </div>
                  </PipelineStepIndicator>

                  <PipelineStepIndicator
                    label="Partitioning File"
                    icon={FileText}
                    status={mapStepStatus(pipelineStatus, 'partitioning')}
                    details={
                      metrics.elements > 0 ? pluralize(metrics.elements, 'element') : undefined
                    }
                    isExpanded={expandedStep === 'partitioning'}
                    onToggle={
                      pipelineStatus === PIPELINE_STEPS.COMPLETE
                        ? () =>
                            setExpandedStep(expandedStep === 'partitioning' ? null : 'partitioning')
                        : undefined
                    }
                    onExpand={
                      pipelineStatus === PIPELINE_STEPS.COMPLETE
                        ? () => setFullViewStep({ type: 'elements', items: realElements })
                        : undefined
                    }
                  >
                    <ElementViewer elements={realElements} onInspect={openElementDetail} />
                  </PipelineStepIndicator>

                  <PipelineStepIndicator
                    label="Chunking"
                    icon={Layers}
                    status={mapStepStatus(pipelineStatus, 'chunking')}
                    details={metrics.chunks > 0 ? pluralize(metrics.chunks, 'chunk') : undefined}
                    isExpanded={expandedStep === 'chunking'}
                    onToggle={
                      pipelineStatus === PIPELINE_STEPS.COMPLETE
                        ? () => setExpandedStep(expandedStep === 'chunking' ? null : 'chunking')
                        : undefined
                    }
                    onExpand={
                      pipelineStatus === PIPELINE_STEPS.COMPLETE
                        ? () => setFullViewStep({ type: 'chunks', items: realChunks })
                        : undefined
                    }
                  >
                    <ChunkViewer chunks={realChunks} onInspect={openChunkDetail} />
                  </PipelineStepIndicator>

                  <PipelineStepIndicator
                    label="Enriching"
                    icon={Cpu}
                    status={mapStepStatus(pipelineStatus, 'summarizing')}
                    isExpanded={expandedStep === 'summarizing'}
                    onToggle={
                      pipelineStatus === PIPELINE_STEPS.COMPLETE
                        ? () =>
                            setExpandedStep(expandedStep === 'summarizing' ? null : 'summarizing')
                        : undefined
                    }
                  >
                    <div className="bg-zinc-950 p-2 rounded border border-zinc-800 text-[9px] font-mono text-zinc-500 space-y-1">
                      <div>Generating searchable descriptions</div>
                      <div>Enhancing retrieval accuracy</div>
                      <div>Creating semantic metadata</div>
                    </div>
                  </PipelineStepIndicator>

                  <PipelineStepIndicator
                    label="Vectorizing"
                    icon={Database}
                    status={mapStepStatus(pipelineStatus, 'vectorizing')}
                    isExpanded={expandedStep === 'vectorizing'}
                    onToggle={
                      pipelineStatus === PIPELINE_STEPS.COMPLETE
                        ? () =>
                            setExpandedStep(expandedStep === 'vectorizing' ? null : 'vectorizing')
                        : undefined
                    }
                  >
                    <div className="bg-zinc-950 p-2 rounded border border-zinc-800 text-[9px] font-mono text-zinc-500 space-y-1">
                      <div>Dimensions: {VECTOR_CONFIG.DIMENSIONS}</div>
                      <div>Metric: {VECTOR_CONFIG.SIMILARITY_METRIC}</div>
                    </div>
                  </PipelineStepIndicator>

                  {/* Summary section - only visible after pipeline completes */}
                  {pipelineStatus === PIPELINE_STEPS.COMPLETE && (
                    <div className="mt-4 bg-zinc-950/50 border border-zinc-800 rounded-sm p-3">
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center justify-between py-1">
                          <span className="text-zinc-400 font-medium">Elements</span>
                          <span className="text-zinc-500">{metrics.elements || '—'}</span>
                        </div>
                        <div className="flex items-center justify-between py-1">
                          <span className="text-zinc-400 font-medium">Chunks</span>
                          <span className="text-zinc-500">{metrics.chunks || '—'}</span>
                        </div>
                        {metrics.images > 0 && (
                          <div className="flex items-center justify-between py-1">
                            <span className="text-zinc-400 font-medium">Images</span>
                            <span className="text-zinc-500">{metrics.images}</span>
                          </div>
                        )}
                        {metrics.tables > 0 && (
                          <div className="flex items-center justify-between py-1">
                            <span className="text-zinc-400 font-medium">Tables</span>
                            <span className="text-zinc-500">{metrics.tables}</span>
                          </div>
                        )}
                        <div className="flex items-center justify-between py-1">
                          <span className="text-zinc-400 font-medium">Hybrid Mode</span>
                          <span className="text-zinc-500">BM25+Vector</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'retrieval' && (
            <div className="p-4 space-y-3">
              {(() => {
                const lastMsg = messages.at(-1);
                return (
                  lastMsg &&
                  lastMsg.role === 'assistant' &&
                  lastMsg.retrievedChunks &&
                  lastMsg.retrievedChunks.length > 0
                );
              })() ? (
                <>
                  {expandedQueries.length > 0 &&
                    messages.at(-1)?.retrievedChunks &&
                    messages.at(-1)!.retrievedChunks!.length > 0 && (
                      <div className="bg-zinc-950 rounded border border-zinc-800 overflow-hidden">
                        <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-900/50 flex items-center justify-between">
                          <span className="text-[9px] font-mono text-zinc-500 uppercase">
                            Multi Search Queries
                          </span>
                          <span className="text-[9px] font-mono text-zinc-600">
                            {expandedQueries.length} queries
                          </span>
                        </div>
                        <div className="p-2 space-y-1">
                          {expandedQueries.map((q, i) => (
                            <div
                              key={i}
                              className="text-[10px] font-mono px-2 py-1.5 rounded bg-zinc-900/30 text-zinc-400 border border-zinc-800/50"
                            >
                              "{q}"
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  <div className="bg-zinc-900/50 px-2 py-1.5 border-b border-zinc-800 flex items-center justify-between">
                    <span className="text-[9px] font-mono text-zinc-500 uppercase">
                      Retrieved Chunks (Hybrid RRF Ranked)
                    </span>
                    <button
                      onClick={() =>
                        setFullViewStep({
                          type: 'chunks',
                          items: messages.at(-1)!.retrievedChunks!,
                        })
                      }
                      className="flex items-center gap-1 text-[9px] font-mono text-zinc-500 hover:text-zinc-300"
                    >
                      <span>{messages.at(-1)?.retrievedChunks?.length} items</span>
                      <Maximize2 size={10} />
                    </button>
                  </div>
                  {messages.at(-1)?.retrievedChunks?.map((chunk) => (
                    <ChunkCard key={chunk.id} chunk={chunk} onInspect={openChunkDetail} />
                  ))}
                </>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center py-20 opacity-30">
                  <Command className="w-8 h-8 mx-auto mb-2" />
                  <p className="text-xs text-zinc-400 font-mono">Awaiting query execution</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
