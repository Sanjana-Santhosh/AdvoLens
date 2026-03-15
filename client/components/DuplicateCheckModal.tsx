'use client';
import { useState } from 'react';
import { X, Search, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react';
import Link from 'next/link';

interface PreCheckResult {
  visual_score: number;
  score_label: string;
  spatial_distance_m: number | null;
  nearby_count: number;
  is_likely_duplicate: boolean;
  verdict: string;
  matched_issue_id: number | null;
  matched_issue_title: string | null;
  matched_issue_status: string | null;
  matched_thumbnail_url: string | null;
  matched_department: string | null;
}

interface DuplicateCheckModalProps {
  imageFile: File;
  latitude: number;
  longitude: number;
  onClose: () => void;
  onSubmitAnyway: () => void;
}

export default function DuplicateCheckModal({
  imageFile,
  latitude,
  longitude,
  onClose,
  onSubmitAnyway,
}: DuplicateCheckModalProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PreCheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const runCheck = async () => {
    setLoading(true);
    setError(null);
    try {
      // Convert image file to base64
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const dataUrl = reader.result as string;
          // Strip the data URL prefix (e.g. "data:image/jpeg;base64,")
          const b64 = dataUrl.split(',')[1];
          resolve(b64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(imageFile);
      });

      const res = await fetch(`${API_URL}/issues/pre-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_base64: base64,
          latitude,
          longitude,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Check failed');
      }

      const data: PreCheckResult = await res.json();
      setResult(data);
      setChecked(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check for duplicates');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (label: string) => {
    if (label.startsWith('🔴')) return 'text-red-600 bg-red-50 border-red-200';
    if (label.startsWith('🟡')) return 'text-yellow-700 bg-yellow-50 border-yellow-200';
    return 'text-green-700 bg-green-50 border-green-200';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Search size={20} className="text-blue-600" />
            <h2 className="text-lg font-bold text-gray-800">Check for Similar Issues</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded-lg"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-5">
          {/* Initial state — not yet checked */}
          {!checked && !loading && (
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-5">
                We&apos;ll scan existing reports for visual similarity and proximity to see if this
                issue has already been reported.
              </p>
              {error && (
                <p className="text-sm text-red-600 mb-4 p-3 bg-red-50 rounded-lg">{error}</p>
              )}
              <button
                onClick={runCheck}
                className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
              >
                🔍 Run Duplicate Check
              </button>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="text-center py-8">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-sm text-gray-600">Analyzing image and location…</p>
            </div>
          )}

          {/* Results */}
          {checked && result && (
            <div className="space-y-4">
              {/* Score table */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-3 text-gray-500 font-medium">Signal</th>
                      <th className="text-right p-3 text-gray-500 font-medium">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    <tr>
                      <td className="p-3 text-gray-700">🖼️ Visual Similarity</td>
                      <td className="p-3 text-right">
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getScoreColor(result.score_label)}`}>
                          {result.score_label}
                        </span>
                        <span className="ml-2 text-gray-500 text-xs">
                          {(result.visual_score * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 text-gray-700">📍 Nearby Issues</td>
                      <td className="p-3 text-right text-gray-700">
                        {result.nearby_count > 0
                          ? `${result.nearby_count} within 50 m`
                          : 'None within 50 m'}
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 text-gray-700">🧠 Verdict</td>
                      <td className="p-3 text-right font-semibold text-gray-800">{result.verdict}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Matched issue card */}
              {result.matched_issue_id && (
                <div className="border border-amber-200 bg-amber-50 rounded-xl p-4">
                  <p className="text-xs font-semibold text-amber-700 uppercase mb-2">Similar Issue Found</p>
                  <div className="flex gap-3">
                    {result.matched_thumbnail_url && (
                      <img
                        src={result.matched_thumbnail_url}
                        alt="Similar issue"
                        className="w-16 h-16 rounded-lg object-cover border border-amber-200 flex-shrink-0"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {result.matched_issue_title || `Issue #${result.matched_issue_id}`}
                      </p>
                      {result.matched_department && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          Dept: {result.matched_department.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </p>
                      )}
                      {result.matched_issue_status && (
                        <p className="text-xs text-gray-500">Status: {result.matched_issue_status}</p>
                      )}
                      <Link
                        href={`/issues/${result.matched_issue_id}`}
                        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-1"
                        target="_blank"
                      >
                        View Original Issue <ExternalLink size={11} />
                      </Link>
                    </div>
                  </div>
                </div>
              )}

              {/* No match */}
              {!result.matched_issue_id && !result.is_likely_duplicate && (
                <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-xl">
                  <CheckCircle size={20} className="text-green-600 flex-shrink-0" />
                  <p className="text-sm text-green-800">
                    ✅ No similar issues found nearby — you&apos;re clear to submit!
                  </p>
                </div>
              )}

              {/* Warning for duplicate */}
              {result.is_likely_duplicate && (
                <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                  <AlertCircle size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800">
                    A similar issue may already exist. You can still submit if you believe it&apos;s
                    a different problem.
                  </p>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-3 pt-1">
                {result.matched_issue_id ? (
                  <>
                    <button
                      onClick={onSubmitAnyway}
                      className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50"
                    >
                      Submit Anyway
                    </button>
                    <Link
                      href={`/issues/${result.matched_issue_id}`}
                      className="flex-1 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 text-center"
                    >
                      Go to Original →
                    </Link>
                  </>
                ) : (
                  <button
                    onClick={onSubmitAnyway}
                    className="w-full py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700"
                    autoFocus
                  >
                    ✅ Submit Report
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
