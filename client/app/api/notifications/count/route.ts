import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

// GET /api/notifications/count - Get notification count for badge
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const token = searchParams.get('token');
    
    if (!token) {
      return NextResponse.json(
        { total: 0, unread: 0 }
      );
    }

    const backendResponse = await fetch(
      `${BACKEND_URL}/notifications/count?token=${token}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    const data = await backendResponse.json();

    if (!backendResponse.ok) {
      return NextResponse.json(
        { total: 0, unread: 0 }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Notification count proxy error:', error);
    return NextResponse.json(
      { total: 0, unread: 0 }
    );
  }
}
