import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { get, set, del } from 'idb-keyval';
import { FileSystemService } from '../services/fs';

interface FileSystemContextType {
  isConnected: boolean;
  isRestoring: boolean;
  fsService: FileSystemService | null;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  error: string | null;
}

const FileSystemContext = createContext<FileSystemContextType | undefined>(undefined);
const HANDLE_KEY = 'cycling_power_ai_dir_handle';

export const FileSystemProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [fsService, setFsService] = useState<FileSystemService | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState<boolean>(true);

  useEffect(() => {
    async function restoreHandle() {
      try {
        const handle = await get<FileSystemDirectoryHandle>(HANDLE_KEY);
        if (handle) {
          // Verify permission is still granted
          const options: FileSystemHandlePermissionDescriptor = { mode: 'read' };
          if (await handle.queryPermission(options) === 'granted') {
            const service = new FileSystemService(handle);
            setFsService(service);
          } else {
             // Ask for permission silently if possible
             if (await handle.requestPermission(options) === 'granted') {
               const service = new FileSystemService(handle);
               setFsService(service);
             } else {
               console.log("Permission denied for saved handle.");
             }
          }
        }
      } catch (err) {
        console.error("Failed to restore directory handle:", err);
      } finally {
        setIsRestoring(false);
      }
    }
    restoreHandle();
  }, []);

  const connect = async () => {
    try {
      setError(null);
      // Request access to the directory
      const handle = await window.showDirectoryPicker({
        mode: 'read',
      });
      
      // Basic validation - check if it looks like the right folder
      let isValid = false;
      try {
         await handle.getDirectoryHandle('reports');
         isValid = true;
      } catch {
         try {
             await handle.getDirectoryHandle('data');
             isValid = true;
         } catch {
             isValid = false;
         }
      }

      if (!isValid) {
         setError("This doesn't look like the cycling_power_ai project directory. We couldn't find 'reports/' or 'data/'.");
         return;
      }

      // Save handle for future sessions
      await set(HANDLE_KEY, handle);

      const service = new FileSystemService(handle);
      setFsService(service);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to connect to directory.');
        console.error(err);
      }
    }
  };

  const disconnect = async () => {
    await del(HANDLE_KEY);
    setFsService(null);
    setError(null);
  };

  return (
    <FileSystemContext.Provider value={{ isConnected: !!fsService, isRestoring, fsService, connect, disconnect, error }}>
      {children}
    </FileSystemContext.Provider>
  );
};

export const useFileSystem = (): FileSystemContextType => {
  const context = useContext(FileSystemContext);
  if (!context) {
    throw new Error('useFileSystem must be used within a FileSystemProvider');
  }
  return context;
};
