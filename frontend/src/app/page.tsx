'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast({
        title: '오류',
        description: '파일을 선택해주세요.',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8012/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('파일 업로드 실패');
      }

      const data = await response.json();
      setText(data.text);
      toast({
        title: '성공',
        description: '파일이 성공적으로 업로드되었습니다.',
      });
    } catch (error) {
      toast({
        title: '오류',
        description: '파일 업로드 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleConvert = async () => {
    if (!file) {
      toast({
        title: '오류',
        description: '파일을 선택해주세요.',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8012/convert', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('파일 변환 실패');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'converted.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: '성공',
        description: '파일이 성공적으로 변환되었습니다.',
      });
    } catch (error) {
      toast({
        title: '오류',
        description: '파일 변환 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <Card className="mb-4">
        <CardHeader>
          <CardTitle>PDF 파일 업로드</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            <Input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="w-full"
            />
            <div className="flex gap-2">
              <Button
                onClick={handleUpload}
                disabled={!file || isLoading}
                className="flex-1"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    처리 중...
                  </>
                ) : (
                  '텍스트 추출'
                )}
              </Button>
              <Button
                onClick={handleConvert}
                disabled={!file || isLoading}
                className="flex-1"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    처리 중...
                  </>
                ) : (
                  'PDF 변환'
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {text && (
        <Card>
          <CardHeader>
            <CardTitle>추출된 텍스트</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={text}
              readOnly
              className="min-h-[200px]"
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
} 