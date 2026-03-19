import { useState, useEffect, useRef } from 'react';
import { verifyDocument } from '../api.ts';
import type { KycData } from '../App.tsx';
import type { VerifyResponse } from '../api.ts';

interface Props {
  data: KycData;
  onRestart: () => void;
}

export function ResultScreen({ data, onRestart }: Props) {
  const [verification, setVerification] = useState<VerifyResponse | null>(data.verification);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initRef = useRef(false);

  // Run verification on mount if not already done
  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;

    if (verification) return;
    if (!data.documentImage || !data.selfieImage) {
      setError('Missing document or selfie image');
      return;
    }

    async function verify() {
      setLoading(true);
      try {
        const result = await verifyDocument(data.documentImage!, data.selfieImage!);
        setVerification(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Verification failed');
      } finally {
        setLoading(false);
      }
    }
    verify();
  }, [data, verification]);

  const mrz = data.documentScan?.mrz;
  const quality = data.selfieDetect?.faces[0]?.quality;
  const isMatch = verification?.is_match ?? false;
  const similarity = verification?.similarity ?? 0;
  const overallPass = isMatch && data.livenessPass;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-slate-50 flex items-center justify-center p-4">
        <div className="text-center">
          <Spinner />
          <p className="mt-4 text-indigo-600 font-semibold">Verifying identity...</p>
          <p className="text-sm text-slate-500 mt-1">Comparing document photo with selfie</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-slate-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Header badge */}
        <div className="text-center mb-6">
          <div
            className={`inline-flex items-center justify-center w-20 h-20 rounded-full text-4xl mb-4 ${
              overallPass
                ? 'bg-emerald-100 text-emerald-600'
                : error
                  ? 'bg-red-100 text-red-600'
                  : 'bg-red-100 text-red-600'
            }`}
          >
            {overallPass ? '\u2713' : '\u2717'}
          </div>
          <h1
            className={`text-2xl font-bold ${
              overallPass ? 'text-emerald-700' : 'text-red-700'
            }`}
          >
            {error
              ? 'Verification Error'
              : overallPass
                ? 'Verification Complete'
                : 'Verification Failed'}
          </h1>
          {verification && (
            <p className="text-slate-500 mt-1">
              Similarity: {(similarity * 100).toFixed(1)}%
            </p>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Document card */}
          <SummaryCard
            title="Document"
            icon="&#x1F4C4;"
            ok={data.documentScan?.detected ?? false}
          >
            {mrz ? (
              <div className="space-y-1 text-sm">
                <Row label="Type" value={mrz.mrz_type === 'TD3' ? 'Passport' : 'ID Card'} />
                <Row label="Name" value={`${mrz.given_names} ${mrz.surname}`} />
                <Row label="Doc No." value={mrz.document_number} />
                <Row label="MRZ Valid" value={mrz.check_digits_valid ? 'Yes' : 'No'} />
              </div>
            ) : (
              <p className="text-sm text-slate-500">No MRZ data extracted</p>
            )}
          </SummaryCard>

          {/* Selfie card */}
          <SummaryCard
            title="Selfie"
            icon="&#x1F933;"
            ok={(data.selfieDetect?.count ?? 0) > 0}
          >
            <div className="space-y-1 text-sm">
              <Row
                label="Face Detected"
                value={(data.selfieDetect?.count ?? 0) > 0 ? 'Yes' : 'No'}
              />
              {quality && (
                <>
                  <Row label="Quality" value={`${(quality.overall_score * 100).toFixed(0)}%`} />
                  <Row label="Acceptable" value={quality.is_acceptable ? 'Yes' : 'No'} />
                </>
              )}
            </div>
          </SummaryCard>

          {/* Liveness card */}
          <SummaryCard title="Liveness" icon="&#x1F9D1;" ok={data.livenessPass}>
            <div className="space-y-1 text-sm">
              <Row label="Status" value={data.livenessPass ? 'Passed' : 'Failed'} />
              <Row
                label="Challenges"
                value={`${data.challengesCompleted}/${data.challengesTotal}`}
              />
            </div>
          </SummaryCard>

          {/* Verification card */}
          <SummaryCard
            title="Verification"
            icon="&#x1F50D;"
            ok={isMatch}
          >
            {verification ? (
              <div className="space-y-1 text-sm">
                <Row label="Match" value={isMatch ? 'Yes' : 'No'} />
                <Row label="Similarity" value={`${(similarity * 100).toFixed(1)}%`} />
              </div>
            ) : (
              <p className="text-sm text-slate-500">Not available</p>
            )}
          </SummaryCard>
        </div>

        {/* Restart */}
        <div className="text-center">
          <button
            onClick={onRestart}
            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors shadow-md cursor-pointer"
          >
            Start New Verification
          </button>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  icon,
  ok,
  children,
}: {
  title: string;
  icon: string;
  ok: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`bg-white rounded-xl border-2 p-4 ${
        ok ? 'border-emerald-200' : 'border-red-200'
      }`}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl" dangerouslySetInnerHTML={{ __html: icon }} />
        <h3 className="font-semibold text-slate-800">{title}</h3>
        <span
          className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full ${
            ok ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
          }`}
        >
          {ok ? 'PASS' : 'FAIL'}
        </span>
      </div>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800">{value}</span>
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin h-12 w-12 text-indigo-600 mx-auto" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
