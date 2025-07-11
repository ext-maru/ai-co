import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFiles } from '../../services/api';
import { FileUploadProgress } from './FileUploadProgress';
import { ImagePreview } from './ImagePreview';
import './FileUploader.css';

interface UploadedFile {
  id: string;
  name: string;
  status: 'uploading' | 'completed' | 'error';
  progress: number;
  preview?: string;
}

export const FileUploader: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);

    // プレビュー生成
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36),
      name: file.name,
      status: 'uploading' as const,
      progress: 0,
      preview: URL.createObjectURL(file)
    }));

    setFiles(prev => [...prev, ...newFiles]);

    try {
      // アップロード実行
      const results = await uploadFiles(acceptedFiles, (progress) => {
        setFiles(prev => prev.map(f =>
          f.id === progress.fileId
            ? { ...f, progress: progress.percent }
            : f
        ));
      });

      // 完了状態に更新
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'completed',
        progress: 100
      })));

    } catch (error) {
      console.error('Upload error:', error);
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'error'
      })));
    } finally {
      setUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp']
    },
    multiple: true
  });

  return (
    <div className="file-uploader">
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>ファイルをここにドロップ...</p>
        ) : (
          <p>ファイルをドラッグ＆ドロップ、またはクリックして選択</p>
        )}
      </div>

      <div className="upload-list">
        {files.map(file => (
          <div key={file.id} className="upload-item">
            {file.preview && <ImagePreview src={file.preview} alt={file.name} />}
            <div className="upload-info">
              <span className="file-name">{file.name}</span>
              <FileUploadProgress
                progress={file.progress}
                status={file.status}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
