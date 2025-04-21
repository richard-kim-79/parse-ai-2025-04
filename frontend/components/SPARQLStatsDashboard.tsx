'use client';

import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  ResponsiveContainer
} from 'recharts';

interface StatsData {
  total_queries: number;
  avg_execution_time_ms: number;
  top_prefixes: Array<{
    prefix: string;
    count: number;
    uri: string;
  }>;
  top_patterns: Array<{
    pattern: string;
    count: number;
  }>;
  date_range: {
    start: string | null;
    end: string | null;
  };
}

interface LogData {
  total: number;
  keyword: string;
  logs: Array<{
    timestamp: string;
    query: string;
    results_count: number;
    execution_time_ms: number;
  }>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8008';

export default function SPARQLStatsDashboard() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [logs, setLogs] = useState<LogData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${BACKEND_URL}/sparql/logs/stats`, {
        method: 'GET',
        headers: {
          'Authorization': `Basic ${btoa(`${username}:${password}`)}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include',
        mode: 'cors'
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
        setIsAuthenticated(true);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '인증에 실패했습니다.' }));
        setError(errorData.detail || '인증에 실패했습니다. 사용자명과 비밀번호를 확인해주세요.');
      }
    } catch (err) {
      setError('서버와 통신 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchKeyword.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${BACKEND_URL}/sparql/logs/search?keyword=${encodeURIComponent(searchKeyword)}`, {
        headers: {
          'Authorization': `Basic ${btoa(`${username}:${password}`)}`,
          'Accept': 'application/json'
        },
        credentials: 'include',
        mode: 'cors'
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '검색 중 오류가 발생했습니다.' }));
        setError(errorData.detail || '검색 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError('서버와 통신 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              SPARQL 통계 대시보드
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              관리자 로그인이 필요합니다
            </p>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleLogin}>
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="username" className="sr-only">사용자명</label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  autoComplete="username"
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="사용자명"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="password" className="sr-only">비밀번호</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  autoComplete="current-password"
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="비밀번호"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {error && (
              <div className="text-red-500 text-sm text-center">{error}</div>
            )}

            <div>
              <button
                type="submit"
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                disabled={loading}
              >
                {loading ? '로그인 중...' : '로그인'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">SPARQL 통계 대시보드</h2>
        <button
          onClick={() => setIsAuthenticated(false)}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
        >
          로그아웃
        </button>
      </div>

      {/* 검색 폼 */}
      <div className="bg-white p-4 rounded-lg shadow">
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="검색어를 입력하세요"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {loading ? '검색 중...' : '검색'}
          </button>
        </form>
      </div>

      {/* 검색 결과 */}
      {logs && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">검색 결과 ({logs.total}건)</h3>
          <div className="space-y-4">
            {logs.logs.map((log, index) => (
              <div key={index} className="border-b pb-4">
                <div className="text-sm text-gray-500">{new Date(log.timestamp).toLocaleString()}</div>
                <div className="font-mono bg-gray-50 p-2 rounded mt-2">{log.query}</div>
                <div className="mt-2 text-sm">
                  <span className="text-gray-600">결과 수: {log.results_count}</span>
                  <span className="mx-2">|</span>
                  <span className="text-gray-600">실행 시간: {log.execution_time_ms.toFixed(2)}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Prefix 사용 비율 파이차트 */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Prefix 사용 비율</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats?.top_prefixes}
                dataKey="count"
                nameKey="prefix"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {stats?.top_prefixes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 패턴 사용 바 차트 */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">쿼리 패턴 사용 현황</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats?.top_patterns}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="pattern" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 요약 정보 */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">요약 정보</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-gray-600">전체 쿼리 수</p>
            <p className="text-2xl font-bold">{stats?.total_queries}</p>
          </div>
          <div>
            <p className="text-gray-600">평균 실행 시간</p>
            <p className="text-2xl font-bold">{stats?.avg_execution_time_ms.toFixed(2)}ms</p>
          </div>
        </div>
      </div>
    </div>
  );
} 