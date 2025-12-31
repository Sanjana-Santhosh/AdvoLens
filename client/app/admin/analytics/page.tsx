'use client';
import { useEffect, useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import { getIssues } from '@/lib/api';
import { ArrowLeft, RefreshCw, MapPin } from 'lucide-react';
import Link from 'next/link';
import dynamic from 'next/dynamic';

// Dynamically import the map component (client-side only)
const IssueMap = dynamic(() => import('@/components/IssueMap'), { 
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  )
});

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

interface Issue {
  id: number;
  tags: string[] | null;
  status: string;
  created_at: string;
  lat?: number | null;
  lon?: number | null;
  caption?: string | null;
  department?: string | null;
  image_url?: string;
}

interface Hotspot {
  cluster_id: number;
  center: { lat: number; lon: number };
  issue_count: number;
  issue_ids: number[];
  primary_department?: string;
}

export default function AnalyticsPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [loading, setLoading] = useState(true);

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

  const fetchHotspots = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/analytics/hotspots?status=null`);
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

  // Calculate tag distribution
  const tagCounts: Record<string, number> = {};
  issues.forEach(issue => {
    issue.tags?.forEach(tag => {
      tagCounts[tag] = (tagCounts[tag] || 0) + 1;
    });
  });

  // Get top 6 tags
  const sortedTags = Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const tagLabels = sortedTags.map(([tag]) => tag);
  const tagData = sortedTags.map(([, count]) => count);

  // Status distribution
  const statusCounts = {
    Open: issues.filter(i => i.status === 'Open').length,
    Resolved: issues.filter(i => i.status === 'Resolved').length,
    'In Progress': issues.filter(i => i.status === 'In Progress').length,
  };

  // Issues by day (last 7 days)
  const last7Days: Record<string, number> = {};
  const today = new Date();
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const dateStr = date.toLocaleDateString('en-US', { weekday: 'short' });
    last7Days[dateStr] = 0;
  }
  
  issues.forEach(issue => {
    const issueDate = new Date(issue.created_at);
    const daysDiff = Math.floor((today.getTime() - issueDate.getTime()) / (1000 * 60 * 60 * 24));
    if (daysDiff < 7) {
      const dateStr = issueDate.toLocaleDateString('en-US', { weekday: 'short' });
      if (last7Days[dateStr] !== undefined) {
        last7Days[dateStr]++;
      }
    }
  });

  const pieData = {
    labels: Object.keys(statusCounts),
    datasets: [
      {
        label: '# of Issues',
        data: Object.values(statusCounts),
        backgroundColor: [
          'rgba(239, 68, 68, 0.7)',   // Red for Open
          'rgba(34, 197, 94, 0.7)',   // Green for Resolved
          'rgba(234, 179, 8, 0.7)',   // Yellow for In Progress
        ],
        borderColor: [
          'rgba(239, 68, 68, 1)',
          'rgba(34, 197, 94, 1)',
          'rgba(234, 179, 8, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const tagChartData = {
    labels: tagLabels,
    datasets: [
      {
        label: 'Issues by Category',
        data: tagData,
        backgroundColor: [
          'rgba(59, 130, 246, 0.7)',
          'rgba(147, 51, 234, 0.7)',
          'rgba(236, 72, 153, 0.7)',
          'rgba(14, 165, 233, 0.7)',
          'rgba(249, 115, 22, 0.7)',
          'rgba(34, 197, 94, 0.7)',
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(147, 51, 234, 1)',
          'rgba(236, 72, 153, 1)',
          'rgba(14, 165, 233, 1)',
          'rgba(249, 115, 22, 1)',
          'rgba(34, 197, 94, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const weeklyData = {
    labels: Object.keys(last7Days),
    datasets: [
      {
        label: 'Issues Reported',
        data: Object.values(last7Days),
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        borderRadius: 8,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <Link href="/admin/dashboard" className="text-gray-600 hover:text-gray-800">
              <ArrowLeft size={24} />
            </Link>
            <h1 className="text-2xl font-bold text-gray-800">Analytics Dashboard</h1>
          </div>
          <button
            onClick={() => { fetchIssues(); fetchHotspots(); }}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-white border rounded-lg shadow-sm hover:bg-gray-50 text-gray-600"
          >
            <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl p-6 border shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Total Issues</div>
            <div className="text-3xl font-bold text-gray-800">{issues.length}</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-red-200 shadow-sm">
            <div className="text-sm text-red-500 mb-1">Open</div>
            <div className="text-3xl font-bold text-red-600">{statusCounts.Open}</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-green-200 shadow-sm">
            <div className="text-sm text-green-500 mb-1">Resolved</div>
            <div className="text-3xl font-bold text-green-600">{statusCounts.Resolved}</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-blue-200 shadow-sm">
            <div className="text-sm text-blue-500 mb-1">Resolution Rate</div>
            <div className="text-3xl font-bold text-blue-600">
              {issues.length > 0 
                ? Math.round((statusCounts.Resolved / issues.length) * 100) 
                : 0}%
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Status Pie Chart */}
          <div className="bg-white rounded-xl p-6 border shadow-sm">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Issue Status Distribution</h2>
            <div className="max-w-xs mx-auto">
              {loading ? (
                <div className="h-64 flex items-center justify-center">
                  <RefreshCw className="animate-spin text-gray-400" size={32} />
                </div>
              ) : issues.length > 0 ? (
                <Pie data={pieData} />
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  No data available
                </div>
              )}
            </div>
          </div>

          {/* Category Bar Chart */}
          <div className="bg-white rounded-xl p-6 border shadow-sm">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Top Issue Categories</h2>
            {loading ? (
              <div className="h-64 flex items-center justify-center">
                <RefreshCw className="animate-spin text-gray-400" size={32} />
              </div>
            ) : tagLabels.length > 0 ? (
              <Bar data={tagChartData} options={barOptions} />
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No category data available
              </div>
            )}
          </div>
        </div>

        {/* Weekly Trend */}
        <div className="bg-white rounded-xl p-6 border shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Issues Reported (Last 7 Days)</h2>
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <RefreshCw className="animate-spin text-gray-400" size={32} />
            </div>
          ) : (
            <Bar data={weeklyData} options={barOptions} />
          )}
        </div>

        {/* Geographic Hotspots Map */}
        <div className="bg-white rounded-xl p-6 border shadow-sm mt-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <MapPin className="text-amber-500" size={20} />
              Problem Hotspots
            </h2>
            <span className="text-sm text-gray-500">
              {hotspots.length} cluster{hotspots.length !== 1 ? 's' : ''} detected
            </span>
          </div>
          
          {/* Map */}
          <div className="h-96 rounded-lg overflow-hidden mb-4">
            <IssueMap 
              issues={issues.filter(i => i.status === 'Open')} 
              hotspots={hotspots}
              height="100%"
            />
          </div>
          
          {/* Hotspot List */}
          {hotspots.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium text-sm text-gray-600 mb-2">Top Hotspots</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {hotspots.slice(0, 6).map((h, idx) => (
                  <div 
                    key={idx} 
                    className="flex justify-between items-center p-3 bg-amber-50 border border-amber-200 rounded-lg"
                  >
                    <div>
                      <span className="text-sm font-medium text-amber-800">🔥 Cluster #{idx + 1}</span>
                      {h.primary_department && (
                        <p className="text-xs text-amber-600 mt-0.5">
                          {h.primary_department.replace('_', ' ')}
                        </p>
                      )}
                    </div>
                    <span className="text-lg font-bold text-amber-700">{h.issue_count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Top Tags - Mobile Friendly Cards */}
        <div className="bg-white rounded-xl p-6 border shadow-sm mt-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">All Categories</h2>
          
          {/* Desktop Table - Hidden on Mobile */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="p-3 font-semibold text-gray-600 text-sm">Category</th>
                  <th className="p-3 font-semibold text-gray-600 text-sm">Count</th>
                  <th className="p-3 font-semibold text-gray-600 text-sm">Percentage</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {Object.entries(tagCounts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([tag, count]) => (
                    <tr key={tag} className="hover:bg-gray-50">
                      <td className="p-3">
                        <span className="px-2 py-1 bg-gray-100 rounded text-sm text-gray-700">
                          {tag}
                        </span>
                      </td>
                      <td className="p-3 text-gray-600">{count}</td>
                      <td className="p-3 text-gray-600">
                        {issues.length > 0 ? Math.round((count / issues.length) * 100) : 0}%
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards - Hidden on Desktop */}
          <div className="md:hidden grid grid-cols-2 gap-3">
            {Object.entries(tagCounts)
              .sort((a, b) => b[1] - a[1])
              .map(([tag, count]) => {
                const percentage = issues.length > 0 ? Math.round((count / issues.length) * 100) : 0;
                return (
                  <div key={tag} className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div className="text-sm font-medium text-gray-800 truncate" title={tag}>
                      {tag}
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-xl font-bold text-blue-600">{count}</span>
                      <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">{percentage}%</span>
                    </div>
                    {/* Progress bar */}
                    <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 rounded-full" 
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
          
          {Object.keys(tagCounts).length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No categories found
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
