import React, {
 useState, useRef 
} from 'react';

import {

  X,
  UploadCloud,
  FileText,
  Image,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Sparkles,

} from 'lucide-react';

import {
 api 
} from '../api/client';

import type {
 InvoiceIntakeResponse, InvoiceDraft 
} from '../types';


interface AddInvoiceModalProps {

  isOpen: boolean;

  onClose: () => void;

  onSuccess?: (res: InvoiceIntakeResponse) => void;

  onExtractDraft?: (draft: InvoiceDraft) => void;


}

const MAX_FILE_SIZE = 10 * 1024 * 1024;
 // 10 MB
const ALLOWED_TYPES = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];

const ALLOWED_EXTS = ['.pdf', '.png', '.jpg', '.jpeg'];


function formatBytes(bytes: number): string {

  if (bytes === 0) return '0 B';

  const k = 1024;

  const sizes = ['B', 'KB', 'MB', 'GB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${
parseFloat((bytes / Math.pow(k, i)).toFixed(1))
} ${
sizes[i]
}`;


}

export const AddInvoiceModal: React.FC<AddInvoiceModalProps> = ({

  isOpen,
  onClose,
  onSuccess,
  onExtractDraft,

}) => {

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [dragActive, setDragActive] = useState(false);

  const [isUploading, setIsUploading] = useState(false);

  const [isExtracting, setIsExtracting] = useState(false);

  const [uploadResult, setUploadResult] = useState<InvoiceIntakeResponse | null>(null);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);


  const fileInputRef = useRef<HTMLInputElement>(null);


  if (!isOpen) return null;


  const resetState = () => {

    setSelectedFile(null);

    setUploadResult(null);

    setErrorMessage(null);

    setIsUploading(false);

    setIsExtracting(false);

    if (fileInputRef.current) {

      fileInputRef.current.value = '';

    
}
  
};


  const handleExtract = async () => {

    if (!uploadResult?.document_id) return;

    try {

      setIsExtracting(true);

      setErrorMessage(null);

      const draft = await api.extractDocument(uploadResult.document_id);

      if (onExtractDraft) {

        onExtractDraft(draft);

      
}
      handleClose();

    
} catch (err: any) {

      setErrorMessage(err.message || 'AI extraction failed. Please try again.');

    
} finally {

      setIsExtracting(false);

    
}
  
};


  const handleClose = () => {

    resetState();

    onClose();

  
};


  const validateLocalFile = (file: File): string | null => {

    if (file.size > MAX_FILE_SIZE) {

      return 'File is too large. Please upload a file smaller than 10 MB.';

    
}
    const ext = `.${
file.name.split('.').pop()?.toLowerCase()
}`;

    const mime = file.type.toLowerCase();


    const extValid = ALLOWED_EXTS.includes(ext);

    const mimeValid = ALLOWED_TYPES.includes(mime) || mime === '';


    if (!extValid || !mimeValid) {

      return 'Unsupported file type. Please upload a PDF, PNG, or JPEG file.';

    
}
    return null;

  
};


  const processFile = (file: File) => {

    setErrorMessage(null);

    const err = validateLocalFile(file);

    if (err) {

      setErrorMessage(err);

      setSelectedFile(null);

      return;

    
}
    setSelectedFile(file);

  
};


  const handleDrag = (e: React.DragEvent) => {

    e.preventDefault();

    e.stopPropagation();

    if (e.type === 'dragenter' || e.type === 'dragover') {

      setDragActive(true);

    
} else if (e.type === 'dragleave') {

      setDragActive(false);

    
}
  
};


  const handleDrop = (e: React.DragEvent) => {

    e.preventDefault();

    e.stopPropagation();

    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {

      processFile(e.dataTransfer.files[0]);

    
}
  
};


  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {

    if (e.target.files && e.target.files[0]) {

      processFile(e.target.files[0]);

    
}
  
};


  const handleUpload = async () => {

    if (!selectedFile) return;


    try {

      setIsUploading(true);

      setErrorMessage(null);


      const result = await api.uploadInvoiceDocument(selectedFile);

      setUploadResult(result);


      if (onSuccess) {

        onSuccess(result);

      
}
    
} catch (err: any) {

      setErrorMessage(err.message || "That file can't be uploaded.");

    
} finally {

      setIsUploading(false);

    
}
  
};


  const isPdf = selectedFile?.name.toLowerCase().endsWith('.pdf');


  return (
    <div
      className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4 overflow-y-auto"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isUploading) handleClose();
      }}
    >
      <div className="bg-popover text-popover-foreground rounded-[24px] max-w-lg w-full shadow-modal border border-border overflow-hidden my-6 animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="px-6 py-5 border-b border-border flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-foreground">Add a new invoice</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Upload an invoice and we'll prepare it for automated verification.
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-40"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* STATE 1: Success State */}
          {uploadResult && !uploadResult.duplicate && (
            <div className="text-center py-6 space-y-4">
              <div className="w-14 h-14 bg-emerald-500/10 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 dark:text-emerald-400">
                <CheckCircle className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground">Invoice uploaded</h3>
                <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
                  We've received your document. Next, we'll read the invoice details.
                </p>
              </div>

              <div className="bg-muted/50 border border-border rounded-xl p-3.5 text-left max-w-md mx-auto flex items-center gap-3">
                <div className="w-9 h-9 bg-card rounded-lg border border-border flex items-center justify-center text-primary flex-shrink-0">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold text-foreground truncate">
                    {uploadResult.filename}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {formatBytes(uploadResult.size_bytes)} · Ready for extraction
                  </div>
                </div>
              </div>

              <div className="pt-4 space-y-2">
                <button
                  type="button"
                  onClick={handleExtract}
                  disabled={isExtracting}
                  className="w-full py-2.5 bg-primary hover:opacity-90 text-primary-foreground font-semibold rounded-xl text-sm transition-all shadow-xs flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4" />
                  {isExtracting ? 'Extracting with Gemini AI...' : 'Extract details with AI'}
                </button>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={resetState}
                    className="flex-1 py-2 bg-muted hover:bg-muted/80 text-foreground font-medium rounded-xl text-xs transition-colors"
                  >
                    Upload another
                  </button>
                  <button
                    type="button"
                    onClick={handleClose}
                    className="flex-1 py-2 bg-card border border-border hover:bg-muted text-foreground font-medium rounded-xl text-xs transition-colors"
                  >
                    Review later
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STATE 2: Duplicate Document Detected */}
          {uploadResult && uploadResult.duplicate && (
            <div className="text-center py-6 space-y-4">
              <div className="w-14 h-14 bg-amber-500/10 rounded-2xl flex items-center justify-center mx-auto text-amber-600 dark:text-amber-400">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground">
                  This invoice document has already been uploaded.
                </h3>
                <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
                  An identical document exists in our system. We avoid creating duplicate copies to prevent double payments.
                </p>
              </div>

              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3.5 text-left max-w-md mx-auto flex items-center gap-3">
                <div className="w-9 h-9 bg-card rounded-lg border border-amber-500/30 flex items-center justify-center text-amber-600 dark:text-amber-400 flex-shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold text-foreground truncate">
                    {uploadResult.filename}
                  </div>
                  <div className="text-xs text-amber-700 dark:text-amber-400">
                    {formatBytes(uploadResult.size_bytes)} · Already recorded
                  </div>
                </div>
              </div>

              <div className="pt-4 flex items-center gap-3">
                <button
                  type="button"
                  onClick={resetState}
                  className="flex-1 py-2.5 bg-muted hover:bg-muted/80 text-foreground font-semibold rounded-xl text-sm transition-colors"
                >
                  Upload a different invoice
                </button>
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 py-2.5 bg-foreground text-background dark:bg-card dark:text-foreground hover:opacity-90 font-semibold rounded-xl text-sm transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* STATE 3: Select & Upload Form */}
          {!uploadResult && (
            <div className="space-y-5">
              {/* Error Banner */}
              {errorMessage && (
                <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-bold text-rose-700 dark:text-rose-400">That file can't be uploaded.</div>
                    <div className="text-xs text-rose-600 dark:text-rose-300 mt-0.5">{errorMessage}</div>
                  </div>
                </div>
              )}

              {/* Upload Dropzone */}
              {!selectedFile && (
                <div
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
                    dragActive
                      ? 'border-primary bg-primary/10 scale-[0.99]'
                      : 'border-border hover:border-muted-foreground/30 hover:bg-muted/30 bg-muted/10'
                  }`}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={handleFileChange}
                  />
                  <div className="w-12 h-12 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mx-auto mb-3">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div className="text-base font-semibold text-foreground">
                    Drag &amp; drop your invoice here
                  </div>
                  <div className="text-xs text-muted-foreground my-1.5 font-medium">or</div>
                  <button
                    type="button"
                    className="px-4 py-1.5 bg-card border border-border hover:bg-muted rounded-xl text-xs font-semibold text-foreground shadow-xs transition-colors inline-block"
                  >
                    Browse files
                  </button>
                  <div className="text-xs text-muted-foreground mt-4">
                    PDF, JPG, PNG · Maximum 10 MB
                  </div>
                </div>
              )}

              {/* Selected File Details */}
              {selectedFile && (
                <div className="space-y-4">
                  <div className="border border-border rounded-2xl p-4 bg-muted/20 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-10 h-10 rounded-xl bg-card border border-border flex items-center justify-center flex-shrink-0 text-primary shadow-xs">
                        {isPdf ? <FileText className="w-5 h-5" /> : <Image className="w-5 h-5" />}
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-foreground truncate">
                          {selectedFile.name}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5 flex items-center gap-2">
                          <span>{formatBytes(selectedFile.size)}</span>
                          <span>·</span>
                          <span className="uppercase text-[10px] font-bold text-muted-foreground">
                            {selectedFile.name.split('.').pop()}
                          </span>
                        </div>
                      </div>
                    </div>
                    {!isUploading && (
                      <button
                        type="button"
                        onClick={resetState}
                        className="text-xs font-medium text-muted-foreground hover:text-rose-600 px-2 py-1 rounded-lg transition-colors"
                      >
                        Remove
                      </button>
                    )}
                  </div>

                  {/* Uploading Status */}
                  {isUploading ? (
                    <div className="bg-primary/10 border border-primary/20 rounded-xl p-4 text-center">
                      <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                      <div className="text-sm font-semibold text-primary">Uploading invoice...</div>
                      <div className="text-xs text-muted-foreground mt-0.5">
                        Securing document in storage and checking for duplicates.
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3 pt-2">
                      <button
                        type="button"
                        onClick={resetState}
                        className="flex-1 py-2.5 bg-muted hover:bg-muted/80 text-foreground font-semibold rounded-xl text-sm transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleUpload}
                        className="flex-1 py-2.5 bg-primary hover:opacity-90 text-primary-foreground font-semibold rounded-xl text-sm transition-all shadow-xs flex items-center justify-center gap-2"
                      >
                        <UploadCloud className="w-4 h-4" />
                        Upload invoice
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );


};

