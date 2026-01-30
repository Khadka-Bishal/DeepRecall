import { Minimize2 } from 'lucide-react';
import { Chunk, PartitionElement } from '../types';
import { UnifiedItemCard } from './PipelineComponents';
import { 
  formatElementType, 
  getElementColorClasses, 
  formatPercentage, 
  formatChunkId, 
  pluralize 
} from '../utils';

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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.type === 'chunks' ? (
              (data.items as Chunk[]).map((chunk) => (
                <UnifiedItemCard
                  key={chunk.id}
                  title={formatChunkId(chunk.id)}
                  subtitle={
                    <span className="text-[10px] text-zinc-600 font-mono">
                      pg.{chunk.page} • {pluralize((chunk.originalContent || chunk.content).length, 'char')}
                    </span>
                  }
                  content={chunk.originalContent || chunk.content}
                  images={chunk.images}
                  onClick={() => onInspectChunk?.(chunk)}
                  className="h-64"
                />
              ))
          ) : (
              (data.items as PartitionElement[]).map((el, i) => (
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
                  onClick={() => onInspectElement?.(el)}
                  className="h-64"
                />
              ))
          )}
          </div>
        </div>
      </div>
    </div>
  );
};
