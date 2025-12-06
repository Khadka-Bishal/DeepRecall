import React from 'react';
import { Minimize2, ExternalLink } from 'lucide-react';
import { Chunk, PartitionElement } from '../types';

export const StepDetailView = ({
  isOpen,
  onClose,
  title,
  data,
  onInspectChunk,
  onInspectElement,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  data: { type: 'elements'; items: PartitionElement[] } | { type: 'chunks'; items: Chunk[] };
  onInspectChunk?: (chunk: Chunk) => void;
  onInspectElement?: (element: PartitionElement) => void;
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 bg-[#09090b] animate-fade-in flex flex-col">
      <div className="h-14 border-b border-zinc-800 flex items-center justify-between px-6 bg-[#09090b]">
        <div className="flex items-center gap-4">
          <div className="text-lg font-medium text-zinc-200">{title}</div>
          <div className="text-xs font-mono text-zinc-500 bg-zinc-900 px-2 py-1 rounded border border-zinc-800">
            {data.items.length} ITEMS FOUND
          </div>
        </div>
        <button
          onClick={onClose}
          className="flex items-center gap-2 text-zinc-400 hover:text-zinc-200 text-xs font-medium bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-md hover:bg-zinc-800 transition-colors"
        >
          <Minimize2 size={14} />
          <span>Collapse View</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 bg-grid">
        <div className="max-w-7xl mx-auto">
          {data.type === 'chunks' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(data.items as Chunk[]).map((chunk) => (
                <div
                  key={chunk.id}
                  onClick={() => onInspectChunk?.(chunk)}
                  className="bg-zinc-950 border border-zinc-800 rounded-md overflow-hidden flex flex-col h-[400px] hover:border-zinc-600 transition-colors group cursor-pointer"
                >
                  <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-900/30 flex items-center justify-between">
                    <span className="text-xs font-mono text-zinc-400">{chunk.id}</span>
                    <span className="text-[10px] font-mono text-zinc-600">pg.{chunk.page}</span>
                  </div>
                  <div className="flex-1 p-4 overflow-y-auto">
                    <div className="text-xs text-zinc-300 font-mono leading-relaxed whitespace-pre-wrap">
                      {chunk.originalContent || chunk.content}
                    </div>
                    {chunk.images && chunk.images.length > 0 && (
                      <div className="mt-4 border-t border-zinc-800 pt-4">
                        <div className="text-[10px] text-zinc-500 uppercase mb-2">
                          Figure Extracted
                        </div>
                        <img
                          src={chunk.images[0]}
                          className="w-full rounded border border-zinc-800 opacity-80 group-hover:opacity-100 transition-opacity"
                          alt="Chunk content"
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {(data.items as PartitionElement[]).map((el, i) => (
                <div
                  key={i}
                  onClick={() => onInspectElement?.(el)}
                  className="bg-zinc-950 border border-zinc-800 rounded p-3 hover:border-zinc-700 transition-colors cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                        el.type === 'Title'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          : el.type === 'Table'
                          ? 'bg-orange-500/10 text-orange-400 border-orange-500/20'
                          : el.type === 'Image'
                          ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                          : 'bg-zinc-800 text-zinc-500 border-zinc-700'
                      }`}
                    >
                      {el.type}
                    </span>
                    <span className="text-[10px] text-zinc-600 font-mono">
                      {(el.prob * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-xs text-zinc-400 font-mono leading-relaxed whitespace-pre-wrap">
                    {el.text}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
