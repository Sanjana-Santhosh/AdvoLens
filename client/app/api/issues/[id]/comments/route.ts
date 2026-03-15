import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const res = await fetch(`${BACKEND_URL}/issues/${id}/comments`, {
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await res.json();
    if (!res.ok) return NextResponse.json({ detail: data.detail || 'Failed' }, { status: res.status });
    return NextResponse.json(data);
  } catch (error) {
    console.error('Comments GET proxy error:', error);
    return NextResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();

    const res = await fetch(`${BACKEND_URL}/issues/${id}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    if (!res.ok) return NextResponse.json({ detail: data.detail || 'Failed' }, { status: res.status });
    return NextResponse.json(data);
  } catch (error) {
    console.error('Comments POST proxy error:', error);
    return NextResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }
}
