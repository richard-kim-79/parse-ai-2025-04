import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch('http://localhost:8008/sparql/logs/stats');
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: '통계 데이터를 가져오는데 실패했습니다.' },
      { status: 500 }
    );
  }
} 