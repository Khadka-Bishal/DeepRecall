import {
  Activity,
  UploadCloud,
  FileText,
  Layers,
  Cpu,
  Database,
  Command,
  Maximize2,
  Workflow,
} from 'lucide-react';
import { PipelineStepIndicator, ElementViewer, ChunkViewer } from './PipelineComponents';
import { ChunkCard } from './ChunkCard';
import { pluralize, PIPELINE_STEPS, VECTOR_CONFIG, mapStepStatus } from '../utils';
import type { PartitionElement, Chunk } from '../types';

interface PipelineMetrics {
  elements: number;
  chunks: number;
  images: number;
  tables: number;
}

interface InspectorPanelProps {
  /** Currently active tab */
  activeTab: 'pipeline' | 'retrieval';
  /** Callback to change active tab */
  setActiveTab: (tab: 'pipeline' | 'retrieval') => void;
  /** Current pipeline processing status */
  pipelineStatus: string;
  /** Currently expanded pipeline step */
  expandedStep: string | null;
  /** Callback to change expanded step */
  setExpandedStep: (step: string | null) => void;
  /** Uploaded file name */
  uploadedFile: string | null;
  /** Pipeline processing metrics */
  metrics: PipelineMetrics;
  /** Extracted document elements */
  realElements: PartitionElement[];
  /** Processed chunks */
  realChunks: Chunk[];
  /** Expanded queries from multi-query retrieval */
  expandedQueries: string[];
  /** Latest retrieved chunks from messages */
  latestRetrievedChunks: Chunk[] | undefined;
  /** Has valid retrieval results */
  hasRetrievalResults: boolean;
  /** Callback when inspecting element */
  onInspectElement: (el: PartitionElement) => void;
  /** Callback when inspecting chunk */
  onInspectChunk: (chunk: Chunk) => void;
  /** Callback when expanding to full view */
  onExpandView: (view: { type: 'elements' | 'chunks'; items: any[] }) => void;
}

/**
 * Right sidebar panel showing pipeline/retrieval info.
 * Extracted from App.tsx for better modularity.
 */
export function InspectorPanel({
  activeTab,
  setActiveTab,
  pipelineStatus,
  expandedStep,
  setExpandedStep,
  uploadedFile,
  metrics,
  realElements,
  realChunks,
  expandedQueries,
  latestRetrievedChunks,
  hasRetrievalResults,
  onInspectElement,
  onInspectChunk,
  onExpandView,
}: InspectorPanelProps) {
  const isComplete = pipelineStatus === PIPELINE_STEPS.COMPLETE;
  const isIdle = pipelineStatus === PIPELINE_STEPS.IDLE;

  return (
    <div className="w-[400px] border-l border-zinc-800 bg-[#09090b] flex flex-col shadow-xl z-20">
      {/* Tab header */}
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

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-0">
        {activeTab === 'pipeline' && (
          <PipelineTab
            pipelineStatus={pipelineStatus}
            isComplete={isComplete}
            isIdle={isIdle}
            expandedStep={expandedStep}
            setExpandedStep={setExpandedStep}
            uploadedFile={uploadedFile}
            metrics={metrics}
            realElements={realElements}
            realChunks={realChunks}
            onInspectElement={onInspectElement}
            onInspectChunk={onInspectChunk}
            onExpandView={onExpandView}
          />
        )}

        {activeTab === 'retrieval' && (
          <RetrievalTab
            hasRetrievalResults={hasRetrievalResults}
            expandedQueries={expandedQueries}
            latestRetrievedChunks={latestRetrievedChunks}
            onInspectChunk={onInspectChunk}
            onExpandView={onExpandView}
          />
        )}
      </div>
    </div>
  );
}

// Sub-components
function PipelineTab({
  pipelineStatus,
  isComplete,
  isIdle,
  expandedStep,
  setExpandedStep,
  uploadedFile,
  metrics,
  realElements,
  realChunks,
  onInspectElement,
  onInspectChunk,
  onExpandView,
}: {
  pipelineStatus: string;
  isComplete: boolean;
  isIdle: boolean;
  expandedStep: string | null;
  setExpandedStep: (step: string | null) => void;
  uploadedFile: string | null;
  metrics: PipelineMetrics;
  realElements: PartitionElement[];
  realChunks: Chunk[];
  onInspectElement: (el: PartitionElement) => void;
  onInspectChunk: (chunk: Chunk) => void;
  onExpandView: (view: { type: 'elements' | 'chunks'; items: any[] }) => void;
}) {
  const toggleStep = (step: string) => {
    if (!isComplete) return;
    setExpandedStep(expandedStep === step ? null : step);
  };

  return (
    <div className="p-5">
      {/* Status header */}
      <div className="mb-6 flex items-center justify-between">
        <span className="text-[10px] font-mono text-zinc-500 uppercase">Status</span>
        <div className="flex items-center gap-1.5">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              isIdle ? 'bg-zinc-700' : 'bg-emerald-500 animate-pulse'
            }`}
          />
          <span className="text-[10px] font-mono text-zinc-300">
            {pipelineStatus.toUpperCase()}
          </span>
        </div>
      </div>

      {isIdle ? (
        <div className="text-center py-20 border border-dashed border-zinc-800 rounded-sm bg-zinc-900/20">
          <Activity className="w-8 h-8 mx-auto mb-2 text-zinc-700" />
          <p className="text-xs text-zinc-600 font-mono">Waiting for input...</p>
        </div>
      ) : (
        <div className="pl-2 pt-2">
          {/* Pipeline steps */}
          <PipelineStepIndicator
            label="Uploading File"
            icon={UploadCloud}
            status={mapStepStatus(pipelineStatus, 'uploading')}
            details={mapStepStatus(pipelineStatus, 'uploading') === 'complete' ? '1 file' : undefined}
            isExpanded={expandedStep === 'uploading'}
            onToggle={isComplete ? () => toggleStep('uploading') : undefined}
          >
            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 text-[9px] font-mono text-zinc-500">
              <div className="truncate">{uploadedFile || 'No file selected'}</div>
            </div>
          </PipelineStepIndicator>

          <PipelineStepIndicator
            label="AWS S3 Cloud Storage"
            icon={Database}
            status={mapStepStatus(pipelineStatus, 'securing')}
            details={
              mapStepStatus(pipelineStatus, 'securing') === 'active'
                ? 'Bucket: DeepRecall-Input'
                : mapStepStatus(pipelineStatus, 'securing') === 'complete'
                ? 'Secured in Bucket'
                : undefined
            }
          >
            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 text-[9px] font-mono text-zinc-500">
              File handoff to AWS S3 bucket for cloud processing.
            </div>
          </PipelineStepIndicator>

          <PipelineStepIndicator
            label="AWS Orchestration"
            icon={Workflow}
            status={mapStepStatus(pipelineStatus, 'orchestrating')}
            details={
              mapStepStatus(pipelineStatus, 'orchestrating') === 'active'
                ? 'Triggering ADE Lambda...'
                : mapStepStatus(pipelineStatus, 'orchestrating') === 'complete'
                ? 'Handover Successful'
                : undefined
            }
          >
            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 text-[9px] font-mono text-zinc-500">
              Managed by AWS EventBridge & Lambda
            </div>
          </PipelineStepIndicator>

          <PipelineStepIndicator
            label="Partitioning File"
            icon={FileText}
            status={mapStepStatus(pipelineStatus, 'partitioning')}
            details={metrics.elements > 0 ? pluralize(metrics.elements, 'element') : undefined}
            isExpanded={expandedStep === 'partitioning'}
            onToggle={isComplete ? () => toggleStep('partitioning') : undefined}
            onExpand={isComplete ? () => onExpandView({ type: 'elements', items: realElements }) : undefined}
          >
            <ElementViewer elements={realElements} onInspect={onInspectElement} />
          </PipelineStepIndicator>

          <PipelineStepIndicator
            label="Chunking"
            icon={Layers}
            status={mapStepStatus(pipelineStatus, 'chunking')}
            details={metrics.chunks > 0 ? pluralize(metrics.chunks, 'chunk') : undefined}
            isExpanded={expandedStep === 'chunking'}
            onToggle={isComplete ? () => toggleStep('chunking') : undefined}
            onExpand={isComplete ? () => onExpandView({ type: 'chunks', items: realChunks }) : undefined}
          >
            <ChunkViewer chunks={realChunks} onInspect={onInspectChunk} />
          </PipelineStepIndicator>

          <PipelineStepIndicator
            label="Enriching"
            icon={Cpu}
            status={mapStepStatus(pipelineStatus, 'summarizing')}
            isExpanded={expandedStep === 'summarizing'}
            onToggle={isComplete ? () => toggleStep('summarizing') : undefined}
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
            onToggle={isComplete ? () => toggleStep('vectorizing') : undefined}
          >
            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 text-[9px] font-mono text-zinc-500 space-y-1">
              <div>Dimensions: {VECTOR_CONFIG.DIMENSIONS}</div>
              <div>Metric: {VECTOR_CONFIG.SIMILARITY_METRIC}</div>
            </div>
          </PipelineStepIndicator>

          {/* Summary section */}
          {isComplete && (
            <div className="mt-4 bg-zinc-950/50 border border-zinc-800 rounded-sm p-3">
              <div className="space-y-2 text-xs">
                <SummaryRow label="Elements" value={metrics.elements || '—'} />
                <SummaryRow label="Chunks" value={metrics.chunks || '—'} />
                {metrics.images > 0 && <SummaryRow label="Images" value={metrics.images} />}
                {metrics.tables > 0 && <SummaryRow label="Tables" value={metrics.tables} />}
                <SummaryRow label="Hybrid Mode" value="BM25+Vector" />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-zinc-400 font-medium">{label}</span>
      <span className="text-zinc-500">{value}</span>
    </div>
  );
}

function RetrievalTab({
  hasRetrievalResults,
  expandedQueries,
  latestRetrievedChunks,
  onInspectChunk,
  onExpandView,
}: {
  hasRetrievalResults: boolean;
  expandedQueries: string[];
  latestRetrievedChunks: Chunk[] | undefined;
  onInspectChunk: (chunk: Chunk) => void;
  onExpandView: (view: { type: 'chunks'; items: Chunk[] }) => void;
}) {
  if (!hasRetrievalResults) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center py-20 opacity-30">
        <Command className="w-8 h-8 mx-auto mb-2" />
        <p className="text-xs text-zinc-400 font-mono">Awaiting query execution</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      {/* Expanded queries */}
      {expandedQueries.length > 0 && latestRetrievedChunks && latestRetrievedChunks.length > 0 && (
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

      {/* Chunks header */}
      <div className="bg-zinc-900/50 px-2 py-1.5 border-b border-zinc-800 flex items-center justify-between">
        <span className="text-[9px] font-mono text-zinc-500 uppercase">
          Retrieved Chunks (Hybrid RRF Ranked)
        </span>
        <button
          onClick={() => onExpandView({ type: 'chunks', items: latestRetrievedChunks! })}
          className="flex items-center gap-1 text-[9px] font-mono text-zinc-500 hover:text-zinc-300"
        >
          <span>{latestRetrievedChunks?.length} items</span>
          <Maximize2 size={10} />
        </button>
      </div>

      {/* Chunk cards */}
      {latestRetrievedChunks?.map((chunk) => (
        <ChunkCard key={chunk.id} chunk={chunk} onInspect={onInspectChunk} />
      ))}
    </div>
  );
}
