import React, { useState, useRef } from 'react';
import { Upload, Link as LinkIcon, FileText, Image, File as FileIcon, X, ExternalLink, Eye, Play } from 'lucide-react';
import { uploadContent } from '../api/client';
import toast from 'react-hot-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { cn } from '../lib/utils';
import { createPortal } from 'react-dom';

interface Resource {
    id: string;
    title: string;
    type: 'file' | 'youtube';
    file_type?: string;
    url: string;
    verified_url?: string;
    added_at: string;
}

interface ResourcesTabProps {
    planId: string;
    resources?: Resource[];
    onResourceAdded?: () => void;
}

const ResourcePreviewModal = ({ resource, onClose }: { resource: Resource; onClose: () => void }) => {
    // Construct the full URL for the preview
    // If it's a file, it's relative /api/static/..., we need to prepend API_BASE_URL if it's not on same origin, 
    // but usually /api is proxied or same origin. 
    // Wait, in dev, frontend is localhost:5173, backend is localhost:8000.
    // The url saved is /api/static/... 
    // We should ensure it points to the backend.
    
    const getPreviewUrl = (url: string) => {
        if (url.startsWith('http') || url.startsWith('//')) return url;
        // If relative, assume it's relative to backend. 
        // We need the VITE_API_BASE_URL.
        let baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        baseUrl = baseUrl.replace(/\/$/, '');

        // Handle double /api issue
        if (url.startsWith('/api/') && baseUrl.endsWith('/api')) {
            return `${baseUrl}${url.substring(4)}`;
        }
        
        // Remove trailing slash from base and leading slash from url if needed
        return `${baseUrl}${url.startsWith('/') ? '' : '/'}${url}`;
    };

    const previewUrl = getPreviewUrl(resource.url);
    
    // Helper to get YouTube embed URL
    const getYouTubeEmbedUrl = (url: string) => {
        let videoId = '';
        if (url.includes('youtu.be')) {
            videoId = url.split('/').pop()?.split('?')[0] || '';
        } else if (url.includes('v=')) {
            videoId = url.split('v=')[1]?.split('&')[0] || '';
        }
        return `https://www.youtube.com/embed/${videoId}`;
    };

    // Helper to receive download
    const triggerDownload = (url: string) => {
        const link = document.createElement('a');
        link.href = url;
        link.download = url.split('/').pop() || 'download';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-card w-full max-w-5xl h-[85vh] rounded-3xl overflow-hidden flex flex-col shadow-2xl relative">
                <div className="p-4 border-b flex justify-between items-center bg-muted/20">
                    <h3 className="font-bold text-lg truncate flex-1 pr-4">{resource.title}</h3>
                    <div className="flex gap-2">
                         <Button variant="outline" size="sm" onClick={() => window.open(previewUrl, '_blank')}>
                            <ExternalLink size={16} className="mr-2" />
                            Open Original
                        </Button>
                        <Button variant="ghost" size="sm" onClick={onClose} className="hover:bg-destructive/10 hover:text-destructive rounded-full h-8 w-8 p-0">
                            <X size={20} />
                        </Button>
                    </div>
                </div>
                <div className="flex-1 bg-muted/10 overflow-hidden relative">
                    {resource.type === 'youtube' ? (
                        <iframe 
                            src={getYouTubeEmbedUrl(resource.url)} 
                            className="w-full h-full border-none"
                            allowFullScreen
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        />
                    ) : resource.file_type?.startsWith('image/') ? (
                        <div className="w-full h-full flex items-center justify-center overflow-auto p-4">
                            <img src={previewUrl} alt={resource.title} className="max-w-full max-h-full object-contain rounded-lg shadow-lg" />
                        </div>
                    ) : resource.file_type === 'application/pdf' ? (
                        <iframe src={previewUrl} className="w-full h-full border-none" title={resource.title}>
                             {/* Fallback */}
                             <div className="flex flex-col items-center justify-center h-full gap-4">
                                <p>Your browser requires the file to be downloaded.</p>
                                <Button onClick={() => triggerDownload(previewUrl)}>
                                    Download PDF
                                </Button>
                             </div>
                        </iframe>
                    ) : (
                         <div className="flex flex-col items-center justify-center h-full gap-4 text-muted-foreground">
                            <FileText size={48} className="opacity-20" />
                            <p>Preview not available for this file type.</p>
                             <Button variant="secondary" onClick={() => triggerDownload(previewUrl)}>
                                Download File
                            </Button>
                         </div>
                    )}
                </div>
            </div>
        </div>,
        document.body
    );
};

export const ResourcesTab: React.FC<ResourcesTabProps> = ({ planId, resources = [], onResourceAdded }) => {
    const [isUploading, setIsUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [url, setUrl] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewResource, setPreviewResource] = useState<Resource | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    };

    const handleFileSelect = (file: File) => {
        // Validate file type
        const validTypes = [
            'application/pdf', 
            'text/plain', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword', 
            'application/json',
            'image/jpeg', 
            'image/png', 
            'image/webp'
        ];
        
        if (!validTypes.includes(file.type)) {
            toast.error('Unsupported file type. Please upload PDF, Word, Text, or Image files.');
            return;
        }

        setSelectedFile(file);
        setUrl(''); // Clear URL if file selected
    };

    const handleUpload = async () => {
        if (!selectedFile && !url) {
            toast.error('Please select a file or enter a URL');
            return;
        }

        setIsUploading(true);
        const toastId = toast.loading('Uploading and processing content...');

        try {
            await uploadContent(planId, selectedFile, url || null);
            toast.success('Content added to Knowledge Base!', { id: toastId });
            setSelectedFile(null);
            setUrl('');
            if (fileInputRef.current) fileInputRef.current.value = '';
            
            // Notify parent to refresh
            onResourceAdded?.();
        } catch (error: any) {
            console.error(error);
            toast.error(error?.response?.data?.detail || 'Failed to upload content', { id: toastId });
        } finally {
            setIsUploading(false);
        }
    };

    const getFileIcon = (type: string, fileType?: string) => {
        if (type === 'youtube') return <Play className="h-6 w-6 text-red-600" />;
        const ft = fileType || '';
        if (ft.includes('pdf')) return <FileText className="h-6 w-6 text-red-500" />;
        if (ft.includes('word') || ft.includes('document')) return <FileText className="h-6 w-6 text-blue-500" />;
        if (ft.includes('image')) return <Image className="h-6 w-6 text-purple-500" />;
        return <FileIcon className="h-6 w-6 text-gray-500" />;
    };

    return (
        <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-6">
            <Card className="rounded-[2.5rem] border-none shadow-xl overflow-hidden bg-card">
                <CardHeader className="p-8 pb-4">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2.5 bg-primary/10 rounded-xl text-primary">
                            <FileText size={24} />
                        </div>
                        <div>
                            <CardTitle className="text-2xl font-black">Knowledge Base</CardTitle>
                            <CardDescription>Upload syllabus, notes, or books to personalize your AI study plan.</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="p-8 pt-4 space-y-8">
                    
                    {/* Upload Area */}
                    <div 
                        className={cn(
                            "relative group border-2 border-dashed rounded-3xl p-8 transition-all duration-300 flex flex-col items-center justify-center text-center gap-4 cursor-pointer",
                            dragActive ? "border-primary bg-primary/5 scale-[1.01]" : "border-border/50 hover:border-primary/50 hover:bg-muted/30",
                            selectedFile ? "bg-muted/30 border-solid border-primary/20" : ""
                        )}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onClick={() => !selectedFile && fileInputRef.current?.click()}
                    >
                        <input 
                            ref={fileInputRef}
                            type="file" 
                            className="hidden" 
                            accept=".pdf,.txt,.doc,.docx,.jpg,.jpeg,.png,.webp"
                            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                        />

                        {selectedFile ? (
                            <div className="flex flex-col items-center gap-3 animate-in zoom-in-50 duration-300">
                                <FileText className="h-8 w-8 text-primary" />
                                <div>
                                    <p className="text-sm font-bold text-foreground">{selectedFile.name}</p>
                                    <p className="text-xs text-muted-foreground uppercase font-semibold">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                                <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    className="h-8 w-8 rounded-full p-0 text-muted-foreground hover:text-red-500 hover:bg-red-500/10"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setSelectedFile(null);
                                    }}
                                >
                                    <X size={16} />
                                </Button>
                            </div>
                        ) : (
                            <>
                                <div className="h-16 w-16 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-2 group-hover:scale-110 transition-transform duration-300">
                                    <Upload size={32} />
                                </div>
                                <div className="space-y-1">
                                    <p className="text-base font-bold text-foreground">Click to upload or drag & drop</p>
                                    <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">PDF, Word, Text, Images (MAX 10MB)</p>
                                </div>
                            </>
                        )}
                    </div>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-border/50" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-card px-2 text-muted-foreground font-bold tracking-widest">Or Import via URL</span>
                        </div>
                    </div>

                    {/* URL Input */}
                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input 
                                placeholder="Paste YouTube Video URL..." 
                                value={url}
                                onChange={(e) => {
                                    setUrl(e.target.value);
                                    if (e.target.value) setSelectedFile(null);
                                }}
                                className="pl-10 h-12 rounded-2xl bg-muted/30 border-border/50 focus-visible:ring-primary/20"
                                disabled={isUploading || !!selectedFile}
                            />
                        </div>
                        <Button 
                            onClick={handleUpload} 
                            disabled={isUploading || (!selectedFile && !url)}
                            className="h-12 px-8 rounded-2xl font-bold"
                            isLoading={isUploading}
                        >
                            {isUploading ? 'Processing...' : 'Add to Plan'}
                        </Button>
                    </div>

                </CardContent>
            </Card>

            {/* Resources List */}
            {resources && resources.length > 0 && (
                <div className="space-y-4">
                     <h3 className="text-lg font-bold px-4">Your Resources ({resources.length})</h3>
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {resources.map((resource) => (
                            <Card key={resource.id} className="rounded-3xl border-none shadow-sm hover:shadow-md transition-all cursor-pointer group" onClick={() => setPreviewResource(resource)}>
                                <div className="p-4 flex items-center gap-4">
                                    <div className="h-12 w-12 rounded-2xl bg-muted flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                                        {getFileIcon(resource.type, resource.file_type)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-bold text-sm truncate">{resource.title}</h4>
                                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                                            {resource.type === 'youtube' ? 'YouTube' : resource.file_type?.split('/')[1]?.toUpperCase() || 'FILE'} 
                                            <span className="text-[10px] opacity-50">• {new Date(resource.added_at || Date.now()).toLocaleDateString()}</span>
                                        </p>
                                    </div>
                                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Eye size={16} />
                                    </Button>
                                </div>
                            </Card>
                        ))}
                     </div>
                </div>
            )}
            
            {/* Preview Modal */}
            {previewResource && (
                <ResourcePreviewModal 
                    resource={previewResource} 
                    onClose={() => setPreviewResource(null)} 
                />
            )}
        </div>
    );
};
