'use client';
import { useEffect, useState } from 'react';
import { getIssues, getImageUrl } from '@/lib/api';
import { RefreshCw, MapPin, Clock, List, Map as MapIcon, ThumbsUp, MessageCircle } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// Dynamically import the map component (client-side only)
const IssueMap = dynamic(() => import('@/components/IssueMap'), { 
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gray-100">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  )
});

interface Issue {
  id: number;
  image_url: string;
  caption: string | null;
  tags: string[] | null;
  status: string;
  lat: number;
  lon: number;
  created_at: string;
  department?: string;
  upvote_count?: number;
  priority_score?: number;
  comment_count?: number;
}

interface Hotspot {
  cluster_id: number;
  center: { lat: number; lon: number };
  issue_count: number;
  issue_ids: number[];
  primary_department?: string;
}

export default function FeedPage() {
  const router = useRouter();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  const [votingIssueId, setVotingIssueId] = useState<number | null>(null);

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

  const handleVote = async (issueId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const token = localStorage.getItem('tracking_token');
    if (!token) {
      alert('Submit a report first to vote!');
      return;
    }
    
    setVotingIssueId(issueId);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/issues/${issueId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ citizen_token: token, vote_type: 'upvote' })
      });
      
      if (res.ok) {
        const data = await res.json();
        // Update UI
        setIssues(prev => prev.map(issue => 
          issue.id === issueId 
            ? { ...issue, upvote_count: data.upvotes, priority_score: data.priority_score }
            : issue
        ));
      }
    } catch (err) {
      console.error('Vote failed:', err);
    } finally {
      setVotingIssueId(null);
    }
  };

  const fetchHotspots = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/analytics/hotspots`);
      if (res.ok) {
        const data = await res.json();
        setHotspots(data.hotspots || []);
      }
    } catch (err) {
      console.error('Failed to fetch hotspots:', err);
    }
  };

  useEffect(() => {
    fetchIssues();
    fetchHotspots();
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
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center justify-between sticky top-0 z-10">
        <h1 className="text-xl font-bold text-gray-800">Community Issues</h1>
        <div className="flex items-center gap-2">
          {/* View Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'list' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              title="List View"
            >
              <List size={18} />
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'map' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              title="Map View"
            >
              <MapIcon size={18} />
            </button>
          </div>
          <button
            onClick={() => { fetchIssues(); fetchHotspots(); }}
            disabled={loading}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'map' ? (
          /* Map View */
          <div className="h-full">
            <IssueMap 
              issues={issues} 
              hotspots={hotspots} 
              height="calc(100vh - 130px)"
            />
            {/* Hotspot Legend */}
            {hotspots.length > 0 && (
              <div className="absolute bottom-20 left-4 bg-white rounded-lg shadow-lg p-3 z-10 max-w-xs">
                <h4 className="font-semibold text-sm mb-2">🔥 Hotspots ({hotspots.length})</h4>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {hotspots.slice(0, 5).map((h, idx) => (
                    <div key={idx} className="text-xs flex justify-between items-center">
                      <span className="text-gray-600">Cluster #{idx + 1}</span>
                      <span className="font-medium text-amber-600">{h.issue_count} issues</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* List View */
          <div className="p-4 pb-24 max-w-6xl mx-auto overflow-y-auto h-full">
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
                    {issue.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* Engagement Bar */}
                <div className="mt-4 flex items-center gap-4 pt-3 border-t">
                  <button 
                    onClick={(e) => handleVote(issue.id, e)}
                    disabled={votingIssueId === issue.id}
                    className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-blue-600 transition disabled:opacity-50"
                  >
                    <ThumbsUp size={16} className={votingIssueId === issue.id ? 'animate-pulse' : ''} />
                    <span className="font-medium">{issue.upvote_count || 0}</span>
                  </button>
                  
                  <button 
                    onClick={() => router.push(`/issues/${issue.id}`)}
                    className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-blue-600 transition"
                  >
                    <MessageCircle size={16} />
                    <span>{issue.comment_count || 0}</span>
                  </button>
                  
                  {(issue.priority_score || 0) > 50 && (
                    <span className="ml-auto text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full font-medium">
                      🔥 High Priority
                    </span>
                  )}
                </div>

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
        )}
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
