import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';

const FileUpload = ({ onFilesSelected, disabled }) => {
    const onDrop = useCallback(acceptedFiles => {
        onFilesSelected(acceptedFiles);
    }, [onFilesSelected]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf']
        },
        disabled
    });

    return (
        <div
            {...getRootProps()}
            className={`dropzone ${isDragActive ? 'active' : ''}`}
            style={{
                padding: '40px 20px',
                borderStyle: 'dashed',
                borderWidth: 2,
                borderRadius: 12,
                opacity: disabled ? 0.5 : 1,
                cursor: disabled ? 'not-allowed' : 'pointer'
            }}
        >
            <input {...getInputProps()} />
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
                <div className="dropzone-icon" style={{ width: 48, height: 48, marginBottom: 0 }}>
                    <Upload size={24} strokeWidth={1.5} />
                </div>
                <div>
                    <p style={{ fontSize: 14, fontWeight: 600, color: '#ffffff', marginBottom: 4 }}>
                        {isDragActive ? "Drop here..." : "Drag PDF Here"}
                    </p>
                    <p style={{ fontSize: 12, color: '#86868b' }}>
                        or
                    </p>
                    <div style={{
                        marginTop: 8,
                        padding: '6px 12px',
                        background: 'rgba(255,255,255,0.1)',
                        borderRadius: 6,
                        fontSize: 12,
                        display: 'inline-block'
                    }}>
                        Select Files
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FileUpload;
