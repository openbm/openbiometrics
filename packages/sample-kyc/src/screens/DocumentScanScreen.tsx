import { useState, useRef, useCallback } from 'react';
import { scanDocument } from '../api.ts';
import type { KycData } from '../App.tsx';

interface Props {
  data: KycData;
  onUpdate: (partial: Partial<KycData>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function DocumentScanScreen({ data, onUpdate, onNext, onBack }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [showOcr, setShowOcr] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setPreview(URL.createObjectURL(file));
      setLoading(true);
      try {
        const result = await scanDocument(file);
        onUpdate({ documentImage: file, documentScan: result });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Scan failed');
      } finally {
        setLoading(false);
      }
    },
    [onUpdate],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const scan = data.documentScan;
  const mrz = scan?.mrz;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-slate-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <StepHeader step={1} title="Scan Your ID Document" />

        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-6">
          {/* Drop zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              dragOver
                ? 'border-indigo-400 bg-indigo-50'
                : 'border-slate-300 hover:border-indigo-300 hover:bg-slate-50'
            }`}
          >
            {preview ? (
              <img
                src={preview}
                alt="Document preview"
                className="mx-auto max-h-56 rounded-lg object-contain"
              />
            ) : (
              <>
                <div className="text-4xl mb-3 text-slate-400">&#x1F4C4;</div>
                <p className="font-medium text-slate-700">Drop your ID document here</p>
                <p className="text-sm text-slate-400 mt-1">or click to browse (JPEG, PNG)</p>
              </>
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

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center gap-2 mt-6 text-indigo-600">
              <Spinner />
              <span className="text-sm font-medium">Scanning document...</span>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Results */}
          {scan && !loading && (
            <div className="mt-6 space-y-4">
              {/* Status badges */}
              <div className="flex flex-wrap gap-2">
                <Badge ok={scan.detected} label={scan.detected ? 'Document Detected' : 'No Document'} />
                <Badge ok={scan.has_face} label={scan.has_face ? 'Face Found' : 'No Face'} />
                {mrz && (
                  <Badge
                    ok={mrz.check_digits_valid}
                    label={mrz.check_digits_valid ? 'MRZ Valid' : 'MRZ Invalid'}
                  />
                )}
                {mrz && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700">
                    {mrz.mrz_type === 'TD3' ? 'Passport' : 'ID Card'}
                  </span>
                )}
              </div>

              {/* MRZ Data */}
              {mrz && (
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">Parsed Document Data</h3>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                    <Field label="Full Name" value={`${mrz.given_names} ${mrz.surname}`} />
                    <Field label="Document No." value={mrz.document_number} />
                    <Field label="Date of Birth" value={formatMrzDate(mrz.date_of_birth)} />
                    <Field label="Expiry Date" value={formatMrzDate(mrz.expiry_date)} />
                    <Field label="Nationality" value={mrz.nationality} />
                    <Field label="Sex" value={mrz.sex === 'M' ? 'Male' : mrz.sex === 'F' ? 'Female' : mrz.sex} />
                    <Field label="Issuing Country" value={mrz.issuing_country} />
                  </div>
                </div>
              )}

              {/* OCR collapsible */}
              {scan.ocr && (
                <div>
                  <button
                    onClick={() => setShowOcr(!showOcr)}
                    className="text-sm text-indigo-600 hover:text-indigo-700 font-medium cursor-pointer"
                  >
                    {showOcr ? 'Hide' : 'Show'} OCR Text (confidence: {(scan.ocr.confidence * 100).toFixed(0)}%)
                  </button>
                  {showOcr && (
                    <pre className="mt-2 p-3 bg-slate-900 text-slate-200 rounded-lg text-xs overflow-auto max-h-48 whitespace-pre-wrap">
                      {scan.ocr.full_text}
                    </pre>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between mt-6">
            <button
              onClick={onBack}
              className="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
            >
              Back
            </button>
            <button
              onClick={onNext}
              disabled={!scan || !scan.detected}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors text-sm cursor-pointer"
            >
              Continue to Selfie
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StepHeader({ step, title }: { step: number; title: string }) {
  return (
    <div className="mb-4 flex items-center gap-3">
      <div className="flex gap-1">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`w-8 h-1 rounded-full ${s <= step ? 'bg-indigo-600' : 'bg-slate-200'}`}
          />
        ))}
      </div>
      <span className="text-xs text-slate-500 font-medium">Step {step}/3</span>
      <h1 className="text-lg font-bold text-slate-800 ml-auto">{title}</h1>
    </div>
  );
}

function Badge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
        ok ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
      }`}
    >
      {ok ? '\u2713' : '\u2717'} {label}
    </span>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-slate-500 text-xs">{label}</span>
      <p className="font-medium text-slate-800">{value}</p>
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

function formatMrzDate(d: string): string {
  if (d.length !== 6) return d;
  const yy = d.slice(0, 2);
  const mm = d.slice(2, 4);
  const dd = d.slice(4, 6);
  const year = parseInt(yy) > 50 ? `19${yy}` : `20${yy}`;
  return `${dd}/${mm}/${year}`;
}
