'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckCircle, Copy, Bell, ArrowRight, HelpCircle } from 'lucide-react';
import Link from 'next/link';

function ConfirmationPageContent() {
  const searchParams = useSearchParams();
  const [copied, setCopied] = useState(false);

  const issueId = searchParams.get('id');
  const dept = searchParams.get('dept') || '';
  const token = searchParams.get('token') || '';
  const duplicateOf = searchParams.get('duplicate_of');

  // Also persist the token in localStorage (belt-and-suspenders in case it
  // wasn't saved by the report page before the redirect)
  useEffect(() => {
    if (token) {
      localStorage.setItem('tracking_token', token);
    }
  }, [token]);

  const deptLabel = dept
    ? dept.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Unknown';

  const copyToken = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-md overflow-hidden">
        {/* Success header */}
        <div className="bg-green-600 text-white px-6 py-8 text-center">
          <CheckCircle size={52} className="mx-auto mb-3" />
          <h1 className="text-2xl font-bold">Report Submitted!</h1>
          {issueId && (
            <p className="text-green-100 mt-1 text-sm">Issue #{issueId} · {deptLabel}</p>
          )}
        </div>

        <div className="p-6 space-y-5">
          {/* Duplicate warning */}
          {duplicateOf && (
            <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <span className="text-amber-500 text-lg">⚠️</span>
              <p className="text-sm text-amber-800">
                A similar issue #{duplicateOf} was already found. Your report has been linked to it.{' '}
                <Link href={`/issues/${duplicateOf}`} className="underline font-medium">
                  View original →
                </Link>
              </p>
            </div>
          )}

          {/* Token display */}
          {token && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-blue-800 mb-1">Your Tracking Token</p>
              <p className="text-xs text-blue-500 mb-3">
                Save this to track your report and receive status updates on any device.
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-xs font-mono bg-white border border-blue-200 rounded-lg px-3 py-2 text-blue-700 truncate">
                  {token}
                </code>
                <button
                  onClick={copyToken}
                  className="p-2 bg-blue-100 hover:bg-blue-200 rounded-lg transition-colors flex-shrink-0"
                  aria-label="Copy token"
                >
                  <Copy size={16} className={copied ? 'text-green-600' : 'text-blue-600'} />
                </button>
              </div>
              {copied && <p className="text-xs text-green-600 mt-2">✓ Copied!</p>}
            </div>
          )}

          {/* Explainer link */}
          <Link
            href="/how-it-works/token"
            className="flex items-center gap-2 text-sm text-blue-600 hover:underline"
          >
            <HelpCircle size={16} />
            How does my token work?
          </Link>

          {/* Action buttons */}
          <div className="space-y-3 pt-1">
            <Link
              href="/notifications"
              className="flex items-center justify-center gap-2 w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
            >
              <Bell size={18} />
              Track My Issue
            </Link>
            <Link
              href="/report"
              className="flex items-center justify-center gap-2 w-full border border-gray-300 text-gray-700 py-3 rounded-xl font-medium hover:bg-gray-50 transition-colors"
            >
              Report Another Issue
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ConfirmationPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="text-sm text-gray-600">Loading confirmation...</div>
        </div>
      }
    >
      <ConfirmationPageContent />
    </Suspense>
  );
}
