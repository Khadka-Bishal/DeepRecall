import React, { useMemo } from 'react';
import {
  CheckCircle2,
  ChevronDown,
  Loader2,
  Maximize2,
  Image as ImageIcon,
  FileQuestion,
  Layers as LayersIcon,
} from 'lucide-react';
import { EmptyState } from './EmptyState';
import { PartitionElement, Chunk } from '../types';
import { getElementColorClasses, formatElementType, formatPercentage, pluralize, formatChunkId, decodeHtml } from '../utils';



export const UnifiedItemCard = ({
  title,
  subtitle,
  badges,
  content,
  images,
  onClick,
  className = "h-40"
}: {
  title: string;
  subtitle?: React.ReactNode;
  badges?: React.ReactNode;
  content: string;
  images?: string[];
  onClick: () => void;
  className?: string;
}) => {
  // Memoize decoded content to prevent flicker/re-calc
  const decodedContent = useMemo(() => decodeHtml(content), [content]);

  return (
    <div
      onClick={onClick}
      className="bg-zinc-900/30 border border-zinc-800/50 hover:border-zinc-700 rounded p-2 cursor-pointer transition-colors group flex flex-col gap-2"
    >
      {/* Header */}
      <div className="flex items-center justify-between h-5 shrink-0">
        <span className="text-[10px] text-zinc-500 font-mono group-hover:text-zinc-300 truncate max-w-[50%]">
          {title}
        </span>
        <div className="flex items-center gap-2">
            {subtitle}
            {badges}
        </div>
      </div>

      {/* Content - Fixed Height & Scrollable */}
      {/* font-sans to differentiate from code/raw tags. whitespace-normal to wrap text. */}
      <div 
        className={`${className} w-full bg-zinc-950/50 rounded border border-zinc-900/50 p-2 overflow-y-auto text-[11px] text-zinc-300 font-sans leading-relaxed whitespace-normal [&>table]:w-full [&>table]:border-collapse [&>table]:my-1 [&>table_td]:border [&>table_td]:border-zinc-700 [&>table_td]:px-1.5 [&>table_td]:py-0.5 [&>table_th]:bg-zinc-800 [&>table_th]:p-1 [&>table_th]:text-left`}
        dangerouslySetInnerHTML={{ __html: decodedContent }}
      />

      {/* Footer / Images */}
      {images && images.length > 0 && (
        <div className="mt-auto pt-2 space-y-1 border-t border-zinc-800/30">
          <div className="flex items-center gap-1 text-[9px] text-purple-400">
            <ImageIcon size={9} />
            <span>
              {images.length} extracted image{images.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex gap-1 flex-wrap">
            {images.map((img, idx) => (
              <img
                key={idx}
                src={img.startsWith('data:') ? img : `data:image/jpeg;base64,${img}`}
                alt={`Image ${idx + 1}`}
                className="h-12 w-auto rounded border border-zinc-700 object-cover"
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export const PipelineStepIndicator = ({
  label,
  status,
  icon: Icon,
  details,
  children,
  isExpanded = false,
  onToggle,
  onExpand,
}: {
  label: string;
  status: 'pending' | 'active' | 'complete';
  icon: any;
  details?: string;
  children?: React.ReactNode;
  isExpanded?: boolean;
  onToggle?: () => void;
  onExpand?: () => void;
}) => {
  return (
    <div className={`relative flex items-start gap-3 transition-all duration-300 group`}>
      <div
        className={`absolute left-[15px] top-8 bottom-[-8px] w-px bg-zinc-800 group-last:hidden`}
      />

      <div
        className={`mt-0.5 relative z-10 w-8 h-8 rounded border flex items-center justify-center transition-all ${
          status === 'active'
            ? 'bg-zinc-900 border-zinc-200 text-zinc-100 shadow-[0_0_10px_rgba(255,255,255,0.1)]'
            : status === 'complete'
            ? 'bg-zinc-900 border-zinc-700 text-zinc-400'
            : 'bg-transparent border-zinc-800 text-zinc-700'
        }`}
      >
        {status === 'active' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : status === 'complete' ? (
          <CheckCircle2 className="w-3.5 h-3.5" />
        ) : (
          <Icon className="w-3.5 h-3.5" />
        )}
      </div>
      <div className="flex-1 pb-6 min-w-0">
        <div
          onClick={() => status !== 'pending' && onToggle?.()}
          className={`flex items-center justify-between cursor-pointer select-none ${
            status === 'pending' || !onToggle ? 'pointer-events-none' : ''
          }`}
        >
          <div
            className={`text-xs font-medium ${
              status === 'active'
                ? 'text-zinc-100'
                : status === 'complete'
                ? 'text-zinc-400'
                : 'text-zinc-600'
            }`}
          >
            {label}
          </div>
          <div className="flex items-center gap-2">
            {status !== 'pending' && details && (
              <span className="text-[10px] text-zinc-500 font-mono hidden sm:inline">
                {details}
              </span>
            )}
            {status !== 'pending' && onToggle && (
              <>
                {onExpand && (
                  <div
                    onClick={(e) => {
                      e.stopPropagation();
                      onExpand();
                    }}
                    className="p-1 hover:bg-zinc-800 rounded text-zinc-500 hover:text-zinc-300 transition-colors"
                    title="Maximize View"
                  >
                    <Maximize2 size={12} />
                  </div>
                )}
                <ChevronDown
                  size={12}
                  className={`text-zinc-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                />
              </>
            )}
          </div>
        </div>

        {isExpanded && children && (
          <div className="mt-3 overflow-hidden animate-fade-in">{children}</div>
        )}
      </div>
    </div>
  );
};

export const ElementViewer = ({
  elements,
  onInspect,
}: {
  elements: PartitionElement[];
  onInspect: (el: PartitionElement) => void;
}) => (
  <div className="bg-zinc-950 rounded border border-zinc-800 overflow-hidden">
    {elements.length === 0 ? (
      <EmptyState 
        icon={FileQuestion} 
        title="No Elements" 
        description="Partitioning didn't return any elements." 
      />
    ) : (
      <div className="max-h-60 overflow-y-auto p-2 space-y-2">
        {elements.map((el, i) => (
          <UnifiedItemCard
            key={i}
            title={formatElementType(el.type)}
            subtitle={<span className="text-[9px] text-zinc-600 font-mono">pg.{el.page}</span>}
            badges={
               <span className={`text-[9px] font-mono px-1 py-0.5 rounded border ${getElementColorClasses(el.type)}`}>
                  {formatPercentage(el.prob)}
               </span>
            }
            content={el.text}
            onClick={() => onInspect(el)}
          />
        ))}
      </div>
    )}
  </div>
);

export const ChunkViewer = ({
  chunks,
  onInspect,
}: {
  chunks: Chunk[];
  onInspect: (chunk: Chunk) => void;
}) => (
  <div className="bg-zinc-950 rounded border border-zinc-800 overflow-hidden">
    {chunks.length === 0 ? (
      <EmptyState 
        icon={LayersIcon} 
        title="No Chunks" 
        description="Document hasn't been chunked yet." 
      />
    ) : (
      <div className="max-h-60 overflow-y-auto p-2 space-y-2">
        {chunks.map((chk, i) => (
          <UnifiedItemCard
            key={i}
            title={formatChunkId(chk.id)}
            subtitle={
                <span className="text-[9px] text-zinc-600 font-mono">
                  {pluralize(chk.content.length, 'char')}
                </span>
            }
            content={chk.content}
            images={chk.images}
            onClick={() => onInspect(chk)}
          />
        ))}
      </div>
    )}
  </div>
);
