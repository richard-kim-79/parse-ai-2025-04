'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'next/navigation';
import toast from 'react-hot-toast';

interface Document {
  filename: string;
  content: string;
  metadata: {
    title: string;
    author: string;
    date: string;
  };
}

export default function DocumentPage() {
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const params = useParams();

  useEffect(() => {
    fetchDocument();
  }, [params.filename]);

  const fetchDocument = async () => {
    try {
      const response = await axios.get(`http://localhost:8008/documents/${params.filename}`);
      setDocument(response.data);
    } catch (error) {
      toast.error('문서를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">로딩 중...</div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-red-500">문서를 찾을 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">{document.metadata.title}</h1>
          <div className="text-gray-500">
            <span>작성자: {document.metadata.author}</span>
            <span className="mx-2">|</span>
            <span>작성일: {document.metadata.date}</span>
          </div>
        </div>
        <div className="prose max-w-none">
          {document.content}
        </div>
      </div>
    </div>
  );
} 