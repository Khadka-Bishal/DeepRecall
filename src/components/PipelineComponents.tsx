import React from 'react';
import { CheckCircle2, ChevronDown, Loader2, Maximize2, Image as ImageIcon } from 'lucide-react';
import { PartitionElement, Chunk } from '../types';
import { getElementColorClasses, formatElementType, formatPercentage, pluralize } from '../utils';

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
    <div className="max-h-40 overflow-y-auto p-1 space-y-1">
      {elements.map((el, i) => (
        <div
          key={i}
          onClick={() => onInspect(el)}
          className="flex gap-2 p-1.5 hover:bg-zinc-900/50 rounded group cursor-pointer transition-colors"
        >
          <div className="flex-shrink-0 w-16">
            <span
              className={`text-[9px] font-mono px-1 py-0.5 rounded border ${getElementColorClasses(
                el.type
              )}`}
            >
              {formatElementType(el.type)}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[10px] text-zinc-400 font-mono group-hover:text-zinc-200 line-clamp-2">
              {el.text}
            </div>
            <div className="flex items-center justify-between mt-0.5">
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-zinc-600">pg.{el.page}</span>
                <span className="text-[9px] text-zinc-600">conf: {formatPercentage(el.prob)}</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
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
    <div className="max-h-60 overflow-y-auto p-2 space-y-2">
      {chunks.map((chk, i) => (
        <div
          key={i}
          onClick={() => onInspect(chk)}
          className="bg-zinc-900/30 border border-zinc-800/50 hover:border-zinc-700 rounded p-2 cursor-pointer transition-colors group"
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] text-zinc-500 font-mono group-hover:text-zinc-300">
              ID: {chk.id}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[9px] text-zinc-600 font-mono">
                {pluralize(chk.content.length, 'char')}
              </span>
            </div>
          </div>
          <div className="text-[10px] text-zinc-400 leading-tight font-mono opacity-80 group-hover:text-zinc-300 whitespace-pre-wrap line-clamp-3">
            {chk.content}
          </div>
          {chk.images && chk.images.length > 0 && (
            <div className="mt-2 space-y-1">
              <div className="flex items-center gap-1 text-[9px] text-purple-400">
                <ImageIcon size={9} />
                <span>
                  {chk.images.length} extracted image{chk.images.length > 1 ? 's' : ''}
                </span>
              </div>
              <div className="flex gap-1 flex-wrap">
                {chk.images.map((img, idx) => (
                  <img
                    key={idx}
                    src={img.startsWith('data:') ? img : `data:image/jpeg;base64,${img}`}
                    alt={`Chunk ${chk.id} image ${idx + 1}`}
                    className="h-16 w-auto rounded border border-zinc-700 object-cover"
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  </div>
);
