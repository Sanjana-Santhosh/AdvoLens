'use client';
import { useEffect, useState } from 'react';
import { getIssues, updateIssueStatus, getImageUrl } from '@/lib/api';
import { Filter, CheckCircle, AlertCircle, RefreshCw, BarChart3, Home } from 'lucide-react';
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

export default function AdminDashboard() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [filter, setFilter] = useState('All');
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<number | null>(null);

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const data = await getIssues();
      setIssues(data);
    } catch (err) {
      console.error('Failed to fetch issues:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // In real app, check for admin token here!
    fetchIssues();
  }, []);

  const handleResolve = async (issueId: number) => {
    setUpdating(issueId);
    try {
      await updateIssueStatus(issueId, 'Resolved');
      // Refresh the list
      await fetchIssues();
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('Failed to resolve issue. Please try again.');
    } finally {
      setUpdating(null);
    }
  };

  const handleReopen = async (issueId: number) => {
    setUpdating(issueId);
    try {
      await updateIssueStatus(issueId, 'Open');
      await fetchIssues();
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('Failed to reopen issue. Please try again.');
    } finally {
      setUpdating(null);
    }
  };

  const filteredIssues = issues.filter((i) => 
    filter === 'All' ? true : i.status === filter
  );

  const stats = {
    total: issues.length,
    open: issues.filter(i => i.status === 'Open').length,
    resolved: issues.filter(i => i.status === 'Resolved').length,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-800">City Admin Dashboard</h1>
            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">Admin</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/admin/analytics" className="flex items-center text-gray-600 hover:text-blue-600">
              <BarChart3 size={20} className="mr-1" />
              Analytics
            </Link>
            <Link href="/" className="flex items-center text-gray-600 hover:text-blue-600">
              <Home size={20} className="mr-1" />
              Home
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Total Issues</div>
            <div className="text-3xl font-bold text-gray-800">{stats.total}</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-red-200 shadow-sm">
            <div className="text-sm text-red-500 mb-1">Open</div>
            <div className="text-3xl font-bold text-red-600">{stats.open}</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-green-200 shadow-sm">
            <div className="text-sm text-green-500 mb-1">Resolved</div>
            <div className="text-3xl font-bold text-green-600">{stats.resolved}</div>
          </div>
        </div>

        {/* Filter & Refresh */}
        <div className="flex justify-between items-center mb-6">
          <div className="bg-white p-1 rounded-lg shadow-sm border flex gap-1">
            {['All', 'Open', 'Resolved'].map(status => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  filter === status 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {status}
                {status !== 'All' && (
                  <span className="ml-1 text-xs">
                    ({status === 'Open' ? stats.open : stats.resolved})
                  </span>
                )}
              </button>
            ))}
          </div>
          <button
            onClick={fetchIssues}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-white border rounded-lg shadow-sm hover:bg-gray-50 text-gray-600"
          >
            <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Loading State */}
        {loading && filteredIssues.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border p-8 text-center text-gray-500">
            <RefreshCw className="animate-spin mx-auto mb-2" size={24} />
            Loading issues...
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredIssues.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border p-8 text-center text-gray-500">
            No issues found
          </div>
        )}

        {/* Mobile Card View - Hidden on Desktop */}
        {filteredIssues.length > 0 && (
          <div className="lg:hidden space-y-4">
            {filteredIssues.map((issue) => (
              <div key={issue.id} className="bg-white rounded-xl shadow-sm border overflow-hidden">
                {/* Image Header */}
                <div className="relative h-40">
                  <img 
                    src={getImageUrl(issue.image_url)} 
                    alt="Issue"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/placeholder.svg';
                    }}
                  />
                  <div className="absolute top-2 left-2 bg-black/60 text-white px-2 py-1 rounded text-xs font-mono">
                    #{issue.id}
                  </div>
                  <span className={`absolute top-2 right-2 inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                    issue.status === 'Open' 
                      ? 'bg-red-100 text-red-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {issue.status === 'Open' ? <AlertCircle size={12}/> : <CheckCircle size={12}/>}
                    {issue.status}
                  </span>
                </div>

                {/* Card Content */}
                <div className="p-4">
                  {/* Description */}
                  <p className="text-gray-800 text-sm mb-3 line-clamp-2">
                    {issue.caption || 'No description'}
                  </p>

                  {/* Tags */}
                  {issue.tags && issue.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {issue.tags.slice(0, 4).map((t) => (
                        <span key={t} className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">
                          {t}
                        </span>
                      ))}
                      {issue.tags.length > 4 && (
                        <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-400">
                          +{issue.tags.length - 4}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Meta Info */}
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                    <span>{new Date(issue.created_at).toLocaleDateString()}</span>
                    {issue.lat && issue.lon ? (
                      <a 
                        href={`https://maps.google.com/?q=${issue.lat},${issue.lon}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        📍 View on Map
                      </a>
                    ) : (
                      <span className="text-gray-400">No location</span>
                    )}
                  </div>

                  {/* Action Button */}
                  {issue.status === 'Open' ? (
                    <button 
                      onClick={() => handleResolve(issue.id)}
                      disabled={updating === issue.id}
                      className="w-full text-sm bg-green-600 text-white px-4 py-2.5 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                    >
                      {updating === issue.id ? 'Updating...' : '✓ Mark as Resolved'}
                    </button>
                  ) : (
                    <button 
                      onClick={() => handleReopen(issue.id)}
                      disabled={updating === issue.id}
                      className="w-full text-sm bg-gray-600 text-white px-4 py-2.5 rounded-lg hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                    >
                      {updating === issue.id ? 'Updating...' : '↩ Reopen Issue'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Desktop Table View - Hidden on Mobile */}
        {filteredIssues.length > 0 && (
          <div className="hidden lg:block bg-white rounded-xl shadow-sm border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="p-4 font-semibold text-gray-600 text-sm">ID</th>
                    <th className="p-4 font-semibold text-gray-600 text-sm">Image</th>
                    <th className="p-4 font-semibold text-gray-600 text-sm">Description (AI)</th>
                    <th className="p-4 font-semibold text-gray-600 text-sm">Tags</th>
                    <th className="p-4 font-semibold text-gray-600 text-sm">Location</th>
                    <th className="p-4 font-semibold text-gray-600 text-sm">Date</th>
                    <th className="p-4 font-semibold text-gray-600 text-sm">Status</th>
                    <th className="p-4 font-semibold text-gray-600 text-sm">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredIssues.map((issue) => (
                    <tr key={issue.id} className="hover:bg-gray-50">
                      <td className="p-4 text-gray-500 font-mono">#{issue.id}</td>
                      <td className="p-4">
                        <img 
                          src={getImageUrl(issue.image_url)} 
                          alt="Issue"
                          className="w-16 h-16 object-cover rounded-lg border"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/placeholder.svg';
                          }}
                        />
                      </td>
                      <td className="p-4 max-w-xs">
                        <p className="truncate text-gray-800" title={issue.caption || ''}>
                          {issue.caption || 'No description'}
                        </p>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1">
                          {issue.tags?.slice(0, 3).map((t) => (
                            <span key={t} className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">
                              {t}
                            </span>
                          ))}
                          {issue.tags && issue.tags.length > 3 && (
                            <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-400">
                              +{issue.tags.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-4 text-sm text-gray-500">
                        {issue.lat && issue.lon ? (
                          <a 
                            href={`https://maps.google.com/?q=${issue.lat},${issue.lon}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            📍 View Map
                          </a>
                        ) : (
                          <span className="text-gray-400">No location</span>
                        )}
                      </td>
                      <td className="p-4 text-sm text-gray-500">
                        {new Date(issue.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-4">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                          issue.status === 'Open' 
                            ? 'bg-red-100 text-red-800' 
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {issue.status === 'Open' ? <AlertCircle size={12}/> : <CheckCircle size={12}/>}
                          {issue.status}
                        </span>
                      </td>
                      <td className="p-4">
                        {issue.status === 'Open' ? (
                          <button 
                            onClick={() => handleResolve(issue.id)}
                            disabled={updating === issue.id}
                            className="text-sm bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                          >
                            {updating === issue.id ? 'Updating...' : 'Resolve'}
                          </button>
                        ) : (
                          <button 
                            onClick={() => handleReopen(issue.id)}
                            disabled={updating === issue.id}
                            className="text-sm bg-gray-600 text-white px-3 py-1.5 rounded hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                          >
                            {updating === issue.id ? 'Updating...' : 'Reopen'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
