
import React, { useState } from "react";
import { X } from "lucide-react";
import { Chunk, PartitionElement } from "../types";

export const DetailModal = ({
  isOpen,
  onClose,
  title,
  content,
  type = "text",
  metaData,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  content: string | Chunk | PartitionElement;
  type?: "text" | "json" | "image" | "chunk" | "element";
  metaData?: any;
}) => {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState<"preview" | "raw">("preview");

  const renderContent = () => {
    if (type === "chunk") {
      const chunk = content as Chunk;
      return activeTab === "preview" ? (
        <div className="space-y-4">
          <div className="text-sm text-zinc-300 font-mono leading-relaxed whitespace-pre-wrap">
            {chunk.originalContent || chunk.content}
          </div>
          {chunk.images && chunk.images.length > 0 && (
            <div className="mt-4">
              <div className="text-xs text-zinc-500 font-mono mb-2 uppercase">
                Extracted Image
              </div>
              <div className="bg-zinc-950 border border-zinc-800 rounded p-2 flex justify-center">
                <img
                  src={chunk.images[0]}
                  className="max-w-full max-h-[400px] rounded"
                  alt="Extracted"
                />
              </div>
            </div>
          )}
        </div>
      ) : (
        <pre className="text-xs text-zinc-400 font-mono bg-zinc-950 p-4 rounded overflow-auto">
          {JSON.stringify(chunk, null, 2)}
        </pre>
      );
    }

    if (type === "element") {
      const el = content as PartitionElement;
      return activeTab === "preview" ? (
        <div className="text-sm text-zinc-300 font-mono whitespace-pre-wrap">
          {el.text}
        </div>
      ) : (
        <pre className="text-xs text-zinc-400 font-mono bg-zinc-950 p-4 rounded overflow-auto">
          {JSON.stringify(el, null, 2)}
        </pre>
      );
    }

    return (
      <div className="text-sm text-zinc-300">{JSON.stringify(content)}</div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-[#09090b] w-full max-w-4xl h-[80vh] border border-zinc-800 rounded-lg shadow-2xl flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-zinc-200">{title}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab("preview")}
                className={`text-[10px] px-2 py-1 rounded font-mono transition-colors ${
                  activeTab === "preview"
                    ? "bg-zinc-800 text-zinc-200"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                PREVIEW
              </button>
              <button
                onClick={() => setActiveTab("raw")}
                className={`text-[10px] px-2 py-1 rounded font-mono transition-colors ${
                  activeTab === "raw"
                    ? "bg-zinc-800 text-zinc-200"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                RAW_JSON
              </button>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-zinc-800 rounded text-zinc-500 hover:text-zinc-300"
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-6 bg-[#0c0c0e]">
          {renderContent()}
        </div>

        <div className="px-4 py-2 border-t border-zinc-800 bg-zinc-900/30 flex gap-4 text-[10px] font-mono text-zinc-500">
          {metaData &&
            Object.entries(metaData).map(([key, value]) => (
              <div key={key}>
                <span className="uppercase opacity-50 mr-1">{key}:</span>
                <span className="text-zinc-400">{String(value)}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};
