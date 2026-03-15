import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const queryString = searchParams.toString();
    const url = `${BACKEND_URL}/analytics/hotspots${queryString ? `?${queryString}` : ''}`;

    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await res.json();
    if (!res.ok) return NextResponse.json({ detail: data.detail || 'Failed' }, { status: res.status });
    return NextResponse.json(data);
  } catch (error) {
    console.error('Analytics hotspots proxy error:', error);
    return NextResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }
}
