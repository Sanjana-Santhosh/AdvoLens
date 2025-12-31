'use client';
import { useEffect, useState } from 'react';
import { Bell, CheckCircle, AlertCircle, Info, Copy, ArrowLeft, RefreshCw } from 'lucide-react';
import Link from 'next/link';

interface Notification {
  id: number;
  issue_id: number;
  type: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('tracking_token');
    setToken(savedToken);
    
    if (savedToken) {
      fetchNotifications(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchNotifications = async (trackingToken: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/notifications?token=${trackingToken}`);
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: number) => {
    if (!token) return;
    
    try {
      await fetch(`/api/notifications/${id}/read?token=${token}`, {
        method: 'PATCH',
      });
      
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      );
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  };

  const copyToken = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'issue_resolved':
        return <CheckCircle className="text-green-600" size={20} />;
      case 'issue_created':
        return <Info className="text-blue-600" size={20} />;
      case 'duplicate_detected':
        return <AlertCircle className="text-yellow-600" size={20} />;
      default:
        return <Bell className="text-gray-600" size={20} />;
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

  // No token state
  if (!token && !loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center">
          <Link href="/" className="mr-4">
            <ArrowLeft size={24} className="text-gray-600" />
          </Link>
          <h1 className="text-xl font-bold text-gray-800">My Updates</h1>
        </div>

        <div className="p-8 text-center max-w-md mx-auto">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Bell size={40} className="text-gray-300" />
          </div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">No Tracking Token</h2>
          <p className="text-gray-500 mb-6">
            Submit a report to start tracking notifications. Your tracking token will be saved automatically.
          </p>
          <Link
            href="/report"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Report an Issue
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center justify-between">
        <div className="flex items-center">
          <Link href="/" className="mr-4">
            <ArrowLeft size={24} className="text-gray-600" />
          </Link>
          <div className="flex items-center gap-2">
            <Bell size={24} className="text-blue-600" />
            <h1 className="text-xl font-bold text-gray-800">My Updates</h1>
          </div>
        </div>
        <button
          onClick={() => token && fetchNotifications(token)}
          disabled={loading}
          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="p-4 max-w-2xl mx-auto">
        {/* Token Display */}
        {token && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-800">Your Tracking Token</p>
                <p className="text-xs text-blue-600 mt-1 font-mono">{token}</p>
              </div>
              <button
                onClick={copyToken}
                className="p-2 bg-blue-100 hover:bg-blue-200 rounded-lg transition-colors"
              >
                <Copy size={18} className={copied ? 'text-green-600' : 'text-blue-600'} />
              </button>
            </div>
            {copied && (
              <p className="text-xs text-green-600 mt-2">Copied to clipboard!</p>
            )}
            <p className="text-xs text-blue-500 mt-2">
              Save this token to track your reports on any device.
            </p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg p-4 border animate-pulse">
                <div className="flex items-start gap-3">
                  <div className="w-5 h-5 bg-gray-200 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4" />
                    <div className="h-3 bg-gray-200 rounded w-1/4" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Notifications List */}
        {!loading && notifications.length > 0 && (
          <div className="space-y-3">
            {notifications.map((notif) => (
              <div
                key={notif.id}
                onClick={() => !notif.is_read && markAsRead(notif.id)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  notif.is_read
                    ? 'bg-white border-gray-200'
                    : 'bg-blue-50 border-blue-300 shadow-sm'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {getNotificationIcon(notif.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${notif.is_read ? 'text-gray-700' : 'text-gray-900 font-medium'}`}>
                      {notif.message}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-gray-400">
                        {formatDate(notif.created_at)}
                      </span>
                      <span className="text-xs text-gray-300">•</span>
                      <Link
                        href={`/feed`}
                        className="text-xs text-blue-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        View Issue #{notif.issue_id}
                      </Link>
                    </div>
                  </div>
                  {!notif.is_read && (
                    <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && notifications.length === 0 && token && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Bell size={32} className="text-gray-300" />
            </div>
            <h3 className="text-lg font-medium text-gray-700 mb-2">No updates yet</h3>
            <p className="text-gray-500 text-sm">
              You&apos;ll receive notifications when your reported issues are updated.
            </p>
          </div>
        )}
      </div>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-3">
        <div className="max-w-md mx-auto flex justify-around">
          <Link href="/feed" className="flex flex-col items-center text-gray-500 hover:text-blue-600">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
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
          <Link href="/notifications" className="flex flex-col items-center text-blue-600">
            <Bell size={24} />
            <span className="text-xs mt-1">Updates</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}
