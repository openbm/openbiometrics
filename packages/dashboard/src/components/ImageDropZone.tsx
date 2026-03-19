import { useCallback, useRef, useState } from 'react';

interface Props {
  onImage: (file: File, preview: string) => void;
  label?: string;
  preview?: string | null;
}

export function ImageDropZone({ onImage, label = 'Drop image here or click to upload', preview }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      const url = URL.createObjectURL(file);
      onImage(file, url);
    },
    [onImage]
  );

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      className={`relative cursor-pointer rounded-xl border-2 border-dashed transition-all
        ${dragOver
          ? 'border-indigo-500 bg-indigo-500/10'
          : 'border-gray-700 hover:border-gray-500 bg-gray-900/50'}
        ${preview ? 'p-2' : 'p-12'}
      `}
    >
      {preview ? (
        <img src={preview} alt="Uploaded" className="w-full rounded-lg object-contain max-h-80" />
      ) : (
        <div className="flex flex-col items-center gap-3 text-gray-500">
          <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M12 16v-8m0 0l-3 3m3-3l3 3M3 16.5V18a2.5 2.5 0 002.5 2.5h13A2.5 2.5 0 0021 18v-1.5M3 16.5l4.94-4.94a1.5 1.5 0 012.12 0l3.88 3.88m0 0l1.94-1.94a1.5 1.5 0 012.12 0L21 16.5"
            />
          </svg>
          <span className="text-sm">{label}</span>
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
    </div>
  );
}
