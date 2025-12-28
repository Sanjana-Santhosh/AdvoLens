'use client';
import { useEffect, useState } from 'react';
import { getIssues, getImageUrl } from '@/lib/api';
import { RefreshCw, MapPin, Clock } from 'lucide-react';
import Link from 'next/link';

interface Issue {
  id: number;
  image_url: string;
  caption: string | null;
  tags: string[] | null;
  status: string;
  lat: number;
  lon: number;
  created_at: string;
}

export default function FeedPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIssues = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getIssues();
      setIssues(data);
    } catch (err) {
      console.error('Failed to fetch issues:', err);
      setError('Failed to load reports. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return 'bg-red-100 text-red-700';
      case 'in_progress':
      case 'in progress':
        return 'bg-yellow-100 text-yellow-700';
      case 'resolved':
      case 'closed':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center justify-between sticky top-0 z-10">
        <h1 className="text-xl font-bold text-gray-800">Community Issues</h1>
        <button
          onClick={fetchIssues}
          disabled={loading}
          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="p-4 pb-24 max-w-6xl mx-auto">
        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 max-w-md mx-auto lg:max-w-none">
            <p className="text-red-700 text-center">{error}</p>
            <button
              onClick={fetchIssues}
              className="mt-2 w-full text-red-600 font-medium"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && issues.length === 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-pulse">
                <div className="h-48 bg-gray-200" />
                <div className="p-4 space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && issues.length === 0 && !error && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <MapPin size={48} className="mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-700 mb-2">No issues reported yet</h3>
            <p className="text-gray-500 mb-4">Be the first to report an issue!</p>
            <Link
              href="/report"
              className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Report Now
            </Link>
          </div>
        )}

        {/* Issues List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {issues.map((issue) => (
            <div
              key={issue.id}
              className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100 hover:shadow-md transition-shadow"
            >
              {/* Image */}
              <div className="h-48 bg-gray-200 relative">
                <img
                  src={getImageUrl(issue.image_url)}
                  alt="Issue"
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder.svg';
                  }}
                />
                <span
                  className={`absolute top-2 right-2 px-2 py-1 rounded text-xs font-bold ${getStatusColor(issue.status)}`}
                >
                  {issue.status}
                </span>
              </div>

              {/* Content */}
              <div className="p-4">
                <h3 className="font-semibold text-gray-800 line-clamp-2">
                  {issue.caption || 'No description provided'}
                </h3>

                {/* Tags */}
                {issue.tags && issue.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {issue.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* Footer */}
                <div className="mt-3 text-xs text-gray-400 flex justify-between items-center">
                  <span className="flex items-center">
                    <MapPin size={12} className="mr-1" />
                    #{issue.id}
                  </span>
                  <span className="flex items-center">
                    <Clock size={12} className="mr-1" />
                    {formatDate(issue.created_at)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-3">
        <div className="max-w-md mx-auto flex justify-around">
          <Link href="/feed" className="flex flex-col items-center text-blue-600">
            <MapPin size={24} />
            <span className="text-xs mt-1">Feed</span>
          </Link>
          <Link href="/report" className="flex flex-col items-center text-gray-500 hover:text-blue-600">
            <div className="bg-blue-600 text-white p-3 rounded-full -mt-6 shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </div>
            <span className="text-xs mt-1">Report</span>
          </Link>
          <Link href="/" className="flex flex-col items-center text-gray-500 hover:text-blue-600">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>
            <span className="text-xs mt-1">Home</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}
