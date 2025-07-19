import React from 'react';

interface ImagePreviewProps {
  src: string;
  alt: string;
  onRemove?: () => void;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({ src, alt, onRemove }) => {
  return (
    <div style={{
      position: 'relative',
      display: 'inline-block',
      marginRight: '10px'
    }}>
      <img
        src={src}
        alt={alt}
        style={{
          maxWidth: '100px',
          maxHeight: '100px',
          objectFit: 'contain',
          border: '1px solid #ddd',
          borderRadius: '4px'
        }}
      />
      {onRemove && (
        <button
          onClick={onRemove}
          type="button"
          style={{
            position: 'absolute',
            top: '2px',
            right: '2px',
            background: 'rgba(0,0,0,0.7)',
            color: 'white',
            border: 'none',
            borderRadius: '50%',
            width: '20px',
            height: '20px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0,0,0,0.9)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(0,0,0,0.7)';
          }}
        >
          ×
        </button>
      )}
    </div>
  );
};
