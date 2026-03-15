import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return NextResponse.json({ detail: 'Authorization header required' }, { status: 401 });
    }

    const res = await fetch(`${BACKEND_URL}/admin/mail-config`, {
      headers: { 'Authorization': authHeader, 'Content-Type': 'application/json' },
    });

    const data = await res.json();
    if (!res.ok) return NextResponse.json({ detail: data.detail || 'Failed' }, { status: res.status });
    return NextResponse.json(data);
  } catch (error) {
    console.error('Admin mail-config proxy error:', error);
    return NextResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }
}
