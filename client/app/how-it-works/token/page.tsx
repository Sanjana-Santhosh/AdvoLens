'use client';
import { useEffect, useState } from 'react';
import { ArrowLeft, Copy, Key, Smartphone, Shield, AlertTriangle, Bell, MessageSquare } from 'lucide-react';
import Link from 'next/link';

const SECTIONS = [
  {
    icon: Key,
    title: 'What it is',
    body: 'A unique random code generated the moment you submit a report. It\'s your anonymous identity on AdvoLens — no account, no email, just a token.',
  },
  {
    icon: Bell,
    title: 'What you can do with it',
    body: 'Track status updates, receive notifications, upvote issues, leave comments, and delete your own comments — all without signing up.',
  },
  {
    icon: Smartphone,
    title: 'Where it lives',
    body: 'Automatically saved in your browser\'s local storage. You never have to type it on the device you submitted from.',
  },
  {
    icon: Shield,
    title: 'Is it private?',
    body: 'Yes. It\'s a cryptographically random URL-safe string. Nobody can guess or brute-force it.',
  },
  {
    icon: MessageSquare,
    title: 'Switching devices',
    body: 'Go to Notifications → "Claim a Token" and paste it. Your reports appear instantly on your new device.',
  },
  {
    icon: AlertTriangle,
    title: 'Can I lose it?',
    body: 'If you clear your browser data, the token is gone from that device. Always copy it after submitting — it\'s shown clearly on your confirmation screen.',
  },
];

export default function TokenExplainerPage() {
  const [token, setToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setToken(localStorage.getItem('tracking_token'));
  }, []);

  const copyToken = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center">
        <Link href="/notifications" className="mr-4">
          <ArrowLeft size={24} className="text-gray-600" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-800">How Your Token Works</h1>
          <p className="text-xs text-gray-500">No account. No email. Just a token.</p>
        </div>
      </div>

      <div className="p-4 max-w-xl mx-auto space-y-4 pb-16">
        {/* Hero card */}
        <div className="bg-blue-600 text-white rounded-2xl p-6 text-center shadow-sm mt-2">
          <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <Key size={28} />
          </div>
          <h2 className="text-xl font-bold mb-1">🔑 Your Privacy Token</h2>
          <p className="text-blue-100 text-sm">Simple. Secure. Anonymous.</p>
        </div>

        {/* Explainer cards */}
        {SECTIONS.map(({ icon: Icon, title, body }) => (
          <div key={title} className="bg-white rounded-xl border border-gray-200 p-4 flex gap-4">
            <div className="w-9 h-9 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
              <Icon size={18} className="text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800 mb-0.5">{title}</p>
              <p className="text-sm text-gray-600">{body}</p>
            </div>
          </div>
        ))}

        {/* Analogy callout */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-sm text-amber-800 italic">
            💡 Think of it like a cloakroom ticket — whoever holds it, owns the report. Simple,
            private, no password needed.
          </p>
        </div>

        {/* Copy token */}
        {token ? (
          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <p className="text-sm font-semibold text-gray-700 mb-2">📋 Copy My Current Token</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-xs font-mono bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-gray-700 truncate">
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
            {copied && <p className="text-xs text-green-600 mt-2">✓ Copied to clipboard!</p>}
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-center">
            <p className="text-sm text-gray-500 mb-3">You don&apos;t have a token on this device yet.</p>
            <Link
              href="/report"
              className="inline-block bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              Report an Issue to Get Started
            </Link>
          </div>
        )}

        {/* Back to notifications */}
        <Link
          href="/notifications"
          className="flex items-center justify-center gap-2 text-sm text-blue-600 hover:underline pt-2"
        >
          ← Back to My Updates
        </Link>
      </div>
    </div>
  );
}
