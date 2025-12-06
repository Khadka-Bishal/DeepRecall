import React from 'react';
import { FileText, ImageIcon, Table, BarChart3, Maximize2 } from 'lucide-react';
import { Chunk } from '../types';
import { formatScore, formatChunkId, getChunkTypeColor, normalizeImageUrl } from '../utils';

export const ChunkCard: React.FC<{
  chunk: Chunk;
  onInspect: (chunk: Chunk) => void;
  mini?: boolean;
}> = ({ chunk, onInspect, mini = false }) => {
  if (mini) {
    return (
      <button
        onClick={() => onInspect(chunk)}
        className="flex items-center gap-1.5 px-2 py-1 rounded bg-zinc-900 border border-zinc-800 hover:border-zinc-600 transition-colors text-[10px] text-zinc-500 hover:text-zinc-300 font-mono group/btn"
      >
        <FileText size={10} />
        <span>{formatChunkId(chunk.id)}</span>
        <span className="text-emerald-600">RRF {formatScore(chunk.score, 3)}</span>
        <Maximize2
          size={8}
          className="opacity-0 group-hover/btn:opacity-100 ml-1 transition-opacity"
        />
      </button>
    );
  }

  return (
    <div className="group relative bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 overflow-hidden rounded-sm">
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-zinc-800 bg-zinc-900/50 cursor-pointer"
        onClick={() => onInspect(chunk)}
      >
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${getChunkTypeColor(chunk.type)}`}></div>
          <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-wider group-hover:text-zinc-200">
            {chunk.id}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {chunk.images && chunk.images.length > 0 && (
            <div className="flex items-center gap-1 bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/20">
              <ImageIcon size={9} className="text-purple-400" />
              <span className="text-[9px] text-purple-400 font-mono uppercase">Img</span>
            </div>
          )}
          {chunk.tables && chunk.tables.length > 0 && (
            <div className="flex items-center gap-1 bg-orange-500/10 px-1.5 py-0.5 rounded border border-orange-500/20">
              <Table size={9} className="text-orange-400" />
              <span className="text-[9px] text-orange-400 font-mono uppercase">Tbl</span>
            </div>
          )}

          <div className="h-3 w-px bg-zinc-800 mx-1"></div>

          <span className="text-[10px] text-zinc-500 font-mono">pg.{chunk.page}</span>
          <div className="flex items-center gap-1 bg-zinc-950 border border-zinc-800 rounded px-1.5 py-0.5">
            <BarChart3 size={10} className="text-emerald-500" />
            <span className="text-[10px] font-mono text-emerald-500">
              RRF {formatScore(chunk.score, 3)}
            </span>
          </div>

          <Maximize2 size={10} className="text-zinc-600 opacity-0 group-hover:opacity-100 ml-1" />
        </div>
      </div>

      {chunk.scores && (
        <div className="px-3 py-1.5 bg-zinc-950/30 border-b border-zinc-800/50 flex gap-4">
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] text-zinc-600 uppercase font-mono w-8">BM25</span>
            <div className="h-1 w-12 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500"
                style={{ width: `${chunk.scores.bm25 * 100}%` }}
              ></div>
            </div>
            <span className="text-[9px] text-zinc-500 font-mono">
              {formatScore(chunk.scores.bm25)}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] text-zinc-600 uppercase font-mono w-8">Vector</span>
            <div className="h-1 w-12 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500"
                style={{ width: `${chunk.scores.vector * 100}%` }}
              ></div>
            </div>
            <span className="text-[9px] text-zinc-500 font-mono">
              {formatScore(chunk.scores.vector)}
            </span>
          </div>
        </div>
      )}

      <div className="p-3 cursor-pointer" onClick={() => onInspect(chunk)}>
        <p className="text-xs text-zinc-300 leading-relaxed font-light whitespace-pre-wrap line-clamp-6">
          {chunk.content}
        </p>

        {chunk.images && chunk.images.length > 0 && (
          <div className="mt-3 pt-3 border-t border-zinc-800/50">
            <div className="flex items-center gap-2 text-[10px] text-zinc-500 mb-2 uppercase tracking-wider font-semibold">
              <ImageIcon className="w-3 h-3" />
              <span>Extracted_Figure_01</span>
            </div>
            <div className="relative w-full h-32 bg-zinc-950 border border-zinc-800 rounded-sm flex items-center justify-center overflow-hidden group/img">
              <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
              <img
                src={normalizeImageUrl(chunk.images[0])}
                alt="Extracted"
                className="h-full object-contain opacity-90 grayscale group-hover/img:grayscale-0 transition-all duration-500"
              />
              <div className="absolute bottom-1 right-1 px-1 py-0.5 bg-black/60 text-[8px] text-white rounded font-mono">
                BASE64_DECODED
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
