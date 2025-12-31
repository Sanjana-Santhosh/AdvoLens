'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Send, ThumbsUp, MapPin, Clock, Tag } from 'lucide-react';
import Link from 'next/link';

interface Issue {
  id: number;
  image_url: string;
  caption: string | null;
  tags: string[] | null;
  status: string;
  department: string | null;
  lat: number;
  lon: number;
  created_at: string;
  upvote_count: number;
  priority_score: number;
}

interface Comment {
  id: number;
  issue_id: number;
  text: string;
  created_at: string;
}

export default function IssueDetailPage() {
  const params = useParams();
  const router = useRouter();
  const issueId = params.id;
  
  const [issue, setIssue] = useState<Issue | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [userVote, setUserVote] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (!issueId) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch issue details
        const issueRes = await fetch(`${API_URL}/issues/${issueId}`);
        if (issueRes.ok) {
          const issueData = await issueRes.json();
          setIssue(issueData);
        }
        
        // Fetch comments
        const commentsRes = await fetch(`${API_URL}/issues/${issueId}/comments`);
        if (commentsRes.ok) {
          const commentsData = await commentsRes.json();
          setComments(commentsData);
        }

        // Check user's vote status
        const token = localStorage.getItem('tracking_token');
        if (token) {
          const voteRes = await fetch(`${API_URL}/issues/${issueId}/vote?citizen_token=${token}`);
          if (voteRes.ok) {
            const voteData = await voteRes.json();
            setUserVote(voteData.your_vote);
          }
        }
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [issueId, API_URL]);

  const handleVote = async () => {
    const token = localStorage.getItem('tracking_token');
    if (!token) {
      alert('Submit a report first to vote!');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/issues/${issueId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ citizen_token: token, vote_type: 'upvote' })
      });
      
      if (res.ok) {
        const data = await res.json();
        setIssue(prev => prev ? { 
          ...prev, 
          upvote_count: data.upvotes, 
          priority_score: data.priority_score 
        } : null);
        setUserVote(data.your_vote);
      }
    } catch (err) {
      console.error('Vote failed:', err);
    }
  };

  const handleComment = async () => {
    const token = localStorage.getItem('tracking_token');
    if (!token) {
      alert('Submit a report first to comment!');
      return;
    }
    
    if (!newComment.trim()) return;
    
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/issues/${issueId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ citizen_token: token, text: newComment })
      });
      
      if (res.ok) {
        const data = await res.json();
        setComments([data, ...comments]);
        setNewComment('');
      }
    } catch (err) {
      console.error('Comment failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open': return 'bg-red-100 text-red-700';
      case 'in progress': return 'bg-yellow-100 text-yellow-700';
      case 'resolved': return 'bg-green-100 text-green-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!issue) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <p className="text-gray-500 mb-4">Issue not found</p>
        <Link href="/feed" className="text-blue-600 hover:underline">
          Back to Feed
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-600 hover:text-gray-800">
            <ArrowLeft size={24} />
          </button>
          <h1 className="font-semibold text-gray-800">Issue #{issue.id}</h1>
        </div>
      </header>

      <div className="max-w-2xl mx-auto p-4">
        {/* Issue Card */}
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden mb-6">
          {/* Image */}
          <img 
            src={issue.image_url.startsWith('http') ? issue.image_url : `${API_URL}${issue.image_url}`}
            alt="Issue"
            className="w-full h-64 object-cover"
          />
          
          {/* Content */}
          <div className="p-6">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800 flex-1">
                {issue.caption || 'No description'}
              </h2>
              <span className={`ml-3 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(issue.status)}`}>
                {issue.status}
              </span>
            </div>
            
            {/* Tags */}
            {issue.tags && issue.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {issue.tags.map((tag) => (
                  <span key={tag} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full flex items-center gap-1">
                    <Tag size={10} />
                    {tag}
                  </span>
                ))}
              </div>
            )}
            
            {/* Meta Info */}
            <div className="flex flex-wrap gap-4 text-sm text-gray-500 mb-4">
              {issue.department && (
                <span className="flex items-center gap-1">
                  📋 {issue.department.replace('_', ' ')}
                </span>
              )}
              <span className="flex items-center gap-1">
                <MapPin size={14} />
                {issue.lat.toFixed(4)}, {issue.lon.toFixed(4)}
              </span>
              <span className="flex items-center gap-1">
                <Clock size={14} />
                {formatDate(issue.created_at)}
              </span>
            </div>
            
            {/* Voting & Priority */}
            <div className="flex items-center gap-4 pt-4 border-t">
              <button 
                onClick={handleVote}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
                  userVote === 'upvote' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'bg-gray-100 text-gray-700 hover:bg-blue-50'
                }`}
              >
                <ThumbsUp size={18} className={userVote === 'upvote' ? 'fill-current' : ''} />
                <span className="font-medium">{issue.upvote_count} upvotes</span>
              </button>
              
              {issue.priority_score > 50 && (
                <span className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded-full font-medium">
                  🔥 High Priority (Score: {issue.priority_score})
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Comments Section */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-bold mb-4">Community Discussion ({comments.length})</h3>
          
          {/* New Comment Input */}
          <div className="flex gap-2 mb-6">
            <input 
              type="text"
              value={newComment}
              onChange={e => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyPress={e => e.key === 'Enter' && !submitting && handleComment()}
              disabled={submitting}
            />
            <button 
              onClick={handleComment}
              disabled={submitting || !newComment.trim()}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Send size={18} />
            </button>
          </div>
          
          {/* Comments List */}
          <div className="space-y-4">
            {comments.map((comment) => (
              <div key={comment.id} className="border-l-2 border-gray-200 pl-4 py-2">
                <p className="text-gray-700">{comment.text}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {formatDate(comment.created_at)}
                </p>
              </div>
            ))}
            
            {comments.length === 0 && (
              <p className="text-center text-gray-400 py-8">
                No comments yet. Be the first to share your thoughts!
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
