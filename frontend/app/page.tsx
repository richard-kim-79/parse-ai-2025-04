'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

interface File {
  filename: string;
  size: number;
  uploaded_at: number;
  is_parsed: boolean;
  converted_files?: Array<{
    format: string;
    path: string;
    converted_at: number;
  }>;
}

interface SearchFilters {
  author: string;
  startDate: Date | null;
  endDate: Date | null;
  tags: string[];
}

interface FileVersion {
  version: string;
  created_at: number;
  size: number;
}

interface Analysis {
  keywords: Array<{
    word: string;
    count: number;
  }>;
  summary: string;
}

interface Entities {
  organizations: string[];
  dates: string[];
  locations: string[];
  persons: string[];
  keywords: string[];
}

const API_BASE_URL = 'http://localhost:8008';

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    author: '',
    startDate: null,
    endDate: null,
    tags: [],
  });
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newFilename, setNewFilename] = useState('');
  const [versions, setVersions] = useState<FileVersion[]>([]);
  const [versionNote, setVersionNote] = useState('');
  const [allTags, setAllTags] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [converting, setConverting] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [entities, setEntities] = useState<Entities | null>(null);
  const [convertedFiles, setConvertedFiles] = useState<Array<{
    format: string;
    path: string;
    converted_at: number;
  }>>([]);

  useEffect(() => {
    fetchFiles();
    fetchAllTags();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await axios.get('http://localhost:8008/files/');
      setFiles(response.data);
    } catch (error) {
      toast.error('파일 목록을 불러오는데 실패했습니다.');
    }
  };

  const fetchAllTags = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/tags/`);
      setAllTags(response.data);
    } catch (error) {
      console.error('태그 목록을 불러오는데 실패했습니다:', error);
    }
  };

  const handleParse = async (filename: string) => {
    try {
      setLoading(true);
      await axios.post(`http://localhost:8008/parse/${filename}`);
      toast.success('파싱이 시작되었습니다.');
      router.push(`/document/${filename}`);
    } catch (error) {
      toast.error('파싱을 시작하는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (filename: string) => {
    if (window.confirm('정말로 이 파일을 삭제하시겠습니까?')) {
      try {
        await axios.delete(`http://localhost:8007/files/${filename}`);
        toast.success('파일이 삭제되었습니다.');
        fetchFiles();
      } catch (error) {
        toast.error('파일 삭제에 실패했습니다.');
      }
    }
  };

  const handleDownload = async (filename: string) => {
    try {
      const response = await axios.get(`http://localhost:8007/download/${filename}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${filename}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error('파일 다운로드에 실패했습니다.');
    }
  };

  const handleAdvancedSearch = async () => {
    if (!searchQuery.trim() && !searchFilters.author && !searchFilters.startDate && !searchFilters.endDate && searchFilters.tags.length === 0) {
      setSearchResults([]);
      return;
    }

    try {
      const params = new URLSearchParams({
        query: searchQuery,
        ...(searchFilters.author && { author: searchFilters.author }),
        ...(searchFilters.startDate && { start_date: searchFilters.startDate.toISOString().split('T')[0] }),
        ...(searchFilters.endDate && { end_date: searchFilters.endDate.toISOString().split('T')[0] }),
        ...(searchFilters.tags.length > 0 && { tags: searchFilters.tags.join(',') }),
      });

      const response = await axios.get(`${API_BASE_URL}/advanced-search/?${params}`);
      setSearchResults(response.data);
    } catch (error) {
      toast.error('검색 중 오류가 발생했습니다.');
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
      toast.error('PDF 파일만 업로드 가능합니다.');
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      await axios.post(`${API_BASE_URL}/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('파일이 업로드되었습니다.');
      fetchFiles(); // 파일 목록 새로고침
    } catch (error) {
      toast.error('파일 업로드 중 오류가 발생했습니다.');
    } finally {
      setUploading(false);
      event.target.value = ''; // 파일 입력 초기화
    }
  };

  const updateFileMetadata = async (filename: string, metadata: { title?: string; author?: string; tags?: string[] }) => {
    try {
      await axios.put(`${API_BASE_URL}/files/${filename}/metadata`, metadata);
      toast.success('메타데이터가 업데이트되었습니다.');
      fetchFiles();
    } catch (error) {
      toast.error('메타데이터 업데이트 중 오류가 발생했습니다.');
    }
  };

  const handleRename = async (filename: string) => {
    if (!newFilename.trim()) return;
    
    try {
      await axios.put(`${API_BASE_URL}/files/${filename}/rename`, {
        new_filename: newFilename
      });
      toast.success('파일 이름이 변경되었습니다.');
      setIsRenaming(false);
      setNewFilename('');
      fetchFiles();
    } catch (error) {
      toast.error('파일 이름 변경 중 오류가 발생했습니다.');
    }
  };

  const fetchVersions = async (filename: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/files/${filename}/versions`);
      setVersions(response.data);
    } catch (error) {
      toast.error('버전 정보를 불러오는데 실패했습니다.');
    }
  };

  const createVersion = async (filename: string) => {
    try {
      await axios.post(`${API_BASE_URL}/files/${filename}/version`, {
        version_note: versionNote
      });
      toast.success('새 버전이 생성되었습니다.');
      setVersionNote('');
      fetchVersions(filename);
    } catch (error) {
      toast.error('버전 생성 중 오류가 발생했습니다.');
    }
  };

  const analyzeDocument = async (filename: string) => {
    try {
      setAnalyzing(true);
      const response = await axios.get(`${API_BASE_URL}/files/${filename}/analysis`);
      setAnalysis(response.data);
    } catch (error) {
      toast.error('문서 분석 중 오류가 발생했습니다.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConvert = async (filename: string, format: string) => {
    try {
      setConverting(filename);
      const response = await axios.get(`${API_BASE_URL}/convert/${filename}?format=${format}`);
      
      // 다운로드 링크 생성
      const downloadResponse = await axios.get(`${API_BASE_URL}/download/${filename}?format=${format}`);
      const blob = new Blob([downloadResponse.data.content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success(`${format.toUpperCase()} 형식으로 변환되었습니다.`);
    } catch (error) {
      toast.error('변환에 실패했습니다.');
    } finally {
      setConverting(null);
    }
  };

  const handleGetSummary = async (filename: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/files/${filename}/summary`);
      setSummary(response.data.summary);
    } catch (error) {
      toast.error('요약 생성에 실패했습니다.');
    }
  };

  const handleExtractEntities = async (filename: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/files/${filename}/entities`);
      setEntities(response.data);
    } catch (error) {
      toast.error('개체 추출에 실패했습니다.');
    }
  };

  const handleConvertAll = async (filename: string) => {
    try {
      setConverting(filename);
      const response = await axios.post(`${API_BASE_URL}/files/${filename}/convert-all`);
      
      // ZIP 파일 다운로드
      const blob = new Blob([response.data.content], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.data.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success('모든 형식으로 변환이 완료되었습니다.');
      fetchFiles(); // 파일 목록 새로고침
    } catch (error) {
      toast.error('일괄 변환에 실패했습니다.');
    } finally {
      setConverting(null);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">문서 목록</h1>
          <div className="flex gap-4 w-full md:w-auto">
            <label className="flex-1 md:flex-none">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                className="hidden"
                disabled={uploading}
              />
              <span className="block w-full md:w-auto bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 cursor-pointer text-center">
                {uploading ? '업로드 중...' : '파일 업로드'}
              </span>
            </label>
          </div>
        </div>

        <div className="mb-8">
          <div className="flex flex-col md:flex-row gap-4 mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="문서 검색..."
              className="flex-1 px-4 py-2 border rounded bg-white text-gray-900 border-gray-300"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setShowAdvancedSearch(!showAdvancedSearch)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                고급 검색
              </button>
              <button
                onClick={handleAdvancedSearch}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                검색
              </button>
            </div>
          </div>

          {showAdvancedSearch && (
            <div className="bg-gray-100 p-4 rounded mb-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    작성자
                  </label>
                  <input
                    type="text"
                    value={searchFilters.author}
                    onChange={(e) => setSearchFilters({ ...searchFilters, author: e.target.value })}
                    placeholder="작성자 검색..."
                    className="w-full px-4 py-2 border rounded bg-white text-gray-900 border-gray-300"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    태그
                  </label>
                  <input
                    type="text"
                    value={searchFilters.tags.join(', ')}
                    onChange={(e) => setSearchFilters({ ...searchFilters, tags: e.target.value.split(',').map(tag => tag.trim()) })}
                    placeholder="태그 (쉼표로 구분)"
                    className="w-full px-4 py-2 border rounded bg-white text-gray-900 border-gray-300"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    시작일
                  </label>
                  <DatePicker
                    selected={searchFilters.startDate}
                    onChange={(date) => setSearchFilters({ ...searchFilters, startDate: date })}
                    className="w-full px-4 py-2 border rounded bg-white text-gray-900 border-gray-300"
                    dateFormat="yyyy-MM-dd"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    종료일
                  </label>
                  <DatePicker
                    selected={searchFilters.endDate}
                    onChange={(date) => setSearchFilters({ ...searchFilters, endDate: date })}
                    className="w-full px-4 py-2 border rounded bg-white text-gray-900 border-gray-300"
                    dateFormat="yyyy-MM-dd"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {searchResults.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">검색 결과</h2>
            <div className="grid gap-4">
              {searchResults.map((result) => (
                <div
                  key={result.filename}
                  className="bg-white p-4 rounded-lg shadow"
                >
                  <h3 className="text-lg font-semibold">{result.title}</h3>
                  <p className="text-sm text-gray-500">
                    작성자: {result.author} | 작성일: {result.date}
                  </p>
                  <p className="mt-2 text-gray-700">{result.snippet}</p>
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => router.push(`/document/${result.filename}`)}
                      className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
                    >
                      보기
                    </button>
                    <button
                      onClick={() => handleDownload(result.filename)}
                      className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
                    >
                      다운로드
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid gap-4">
          {files.map((file) => (
            <div
              key={file.filename}
              className="bg-white p-4 rounded-lg shadow"
            >
              <div className="flex justify-between items-center">
                <div>
                  {isRenaming && selectedFile === file.filename ? (
                    <div className="flex gap-2 items-center">
                      <input
                        type="text"
                        value={newFilename}
                        onChange={(e) => setNewFilename(e.target.value)}
                        className="px-2 py-1 border rounded"
                        placeholder="새 파일 이름"
                      />
                      <button
                        onClick={() => handleRename(file.filename)}
                        className="bg-green-500 text-white px-2 py-1 rounded text-sm"
                      >
                        확인
                      </button>
                      <button
                        onClick={() => {
                          setIsRenaming(false);
                          setNewFilename('');
                        }}
                        className="bg-gray-500 text-white px-2 py-1 rounded text-sm"
                      >
                        취소
                      </button>
                    </div>
                  ) : (
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                      {file.filename}
                      <button
                        onClick={() => {
                          setSelectedFile(file.filename);
                          setIsRenaming(true);
                          setNewFilename(file.filename.replace('.pdf', ''));
                        }}
                        className="text-sm text-blue-500 hover:text-blue-700"
                      >
                        이름 변경
                      </button>
                    </h2>
                  )}
                  <p className="text-sm text-gray-500">
                    크기: {(file.size / 1024).toFixed(2)} KB
                  </p>
                  <div className="mt-2">
                    <input
                      type="text"
                      value={selectedFile === file.filename ? versionNote : ''}
                      onChange={(e) => setVersionNote(e.target.value)}
                      placeholder="버전 노트"
                      className="px-2 py-1 border rounded mr-2"
                    />
                    <button
                      onClick={() => createVersion(file.filename)}
                      className="bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600"
                    >
                      새 버전 생성
                    </button>
                  </div>
                </div>
                <div className="flex gap-2">
                  {!file.is_parsed && (
                    <button
                      onClick={() => handleParse(file.filename)}
                      disabled={loading}
                      className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
                    >
                      {loading ? '처리 중...' : '파싱 시작'}
                    </button>
                  )}
                  <button
                    onClick={() => handleDownload(file.filename)}
                    className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                  >
                    다운로드
                  </button>
                  <button
                    onClick={() => handleDelete(file.filename)}
                    className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                  >
                    삭제
                  </button>
                </div>
              </div>
              {selectedFile === file.filename && versions.length > 0 && (
                <div className="mt-4 border-t pt-4">
                  <h3 className="text-lg font-semibold mb-2">버전 기록</h3>
                  <div className="space-y-2">
                    {versions.map((version) => (
                      <div
                        key={version.version}
                        className="flex justify-between items-center bg-gray-50 p-2 rounded"
                      >
                        <div>
                          <span className="font-medium">버전 {version.version}</span>
                          <span className="text-sm text-gray-500 ml-2">
                            {new Date(version.created_at * 1000).toLocaleString()}
                          </span>
                        </div>
                        <span className="text-sm text-gray-500">
                          {(version.size / 1024).toFixed(2)} KB
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedFile === file.filename && (
                <div className="mt-4 border-t pt-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold">문서 분석</h3>
                    <button
                      onClick={() => analyzeDocument(file.filename)}
                      disabled={analyzing}
                      className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 disabled:opacity-50"
                    >
                      {analyzing ? '분석 중...' : '분석하기'}
                    </button>
                  </div>
                  
                  {analysis && (
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium mb-2">주요 키워드</h4>
                        <div className="flex flex-wrap gap-2">
                          {analysis.keywords.map((keyword) => (
                            <span
                              key={keyword.word}
                              className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm"
                            >
                              {keyword.word} ({keyword.count})
                            </span>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium mb-2">요약</h4>
                        <p className="text-gray-700 text-sm bg-gray-50 p-3 rounded">
                          {analysis.summary}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <div className="mt-4">
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleGetSummary(file.filename)}
                    className="bg-blue-500 text-white px-4 py-2 rounded"
                  >
                    요약 보기
                  </button>
                  <button
                    onClick={() => handleExtractEntities(file.filename)}
                    className="bg-green-500 text-white px-4 py-2 rounded"
                  >
                    개체 추출
                  </button>
                  <button
                    onClick={() => handleConvertAll(file.filename)}
                    disabled={converting === file.filename}
                    className="bg-purple-500 text-white px-4 py-2 rounded"
                  >
                    전체 변환
                  </button>
                </div>
                
                {summary && (
                  <div className="mt-4 p-4 bg-gray-100 rounded">
                    <h3 className="font-bold mb-2">문서 요약</h3>
                    <p>{summary}</p>
                  </div>
                )}
                
                {entities && (
                  <div className="mt-4 p-4 bg-gray-100 rounded">
                    <h3 className="font-bold mb-2">추출된 개체</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold">기관</h4>
                        <div className="flex flex-wrap gap-2">
                          {entities.organizations.map((org, index) => (
                            <span key={index} className="bg-blue-100 px-2 py-1 rounded">
                              {org}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold">날짜</h4>
                        <div className="flex flex-wrap gap-2">
                          {entities.dates.map((date, index) => (
                            <span key={index} className="bg-green-100 px-2 py-1 rounded">
                              {date}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold">지명</h4>
                        <div className="flex flex-wrap gap-2">
                          {entities.locations.map((loc, index) => (
                            <span key={index} className="bg-yellow-100 px-2 py-1 rounded">
                              {loc}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold">인물</h4>
                        <div className="flex flex-wrap gap-2">
                          {entities.persons.map((person, index) => (
                            <span key={index} className="bg-red-100 px-2 py-1 rounded">
                              {person}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="col-span-2">
                        <h4 className="font-semibold">주요 키워드</h4>
                        <div className="flex flex-wrap gap-2">
                          {entities.keywords.map((keyword, index) => (
                            <span key={index} className="bg-purple-100 px-2 py-1 rounded">
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {file.converted_files && file.converted_files.length > 0 && (
                  <div className="mt-4 p-4 bg-gray-100 rounded">
                    <h3 className="font-bold mb-2">변환된 파일</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {file.converted_files.map((converted, index) => (
                        <div key={index} className="border rounded p-2">
                          <p className="font-semibold">{converted.format.toUpperCase()}</p>
                          <p className="text-sm text-gray-600">
                            변환일: {new Date(converted.converted_at * 1000).toLocaleString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 