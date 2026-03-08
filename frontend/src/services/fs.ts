/**
 * File System Service wrapping the Browser File System Access API.
 */

export interface ReportFile {
  name: string;
  path: string; // e.g., 'reports/2026/W10/session.md'
  handle: FileSystemFileHandle;
}

export interface ReportDirectory {
  name: string; // e.g., 'W10'
  path: string;
  files: ReportFile[];
  directories: ReportDirectory[];
}

export class FileSystemService {
  private rootHandle: FileSystemDirectoryHandle;

  constructor(handle: FileSystemDirectoryHandle) {
    this.rootHandle = handle;
  }

  /**
   * Reads a file from a given path relative to the root handle.
   */
  async readFile(filePath: string): Promise<string> {
    const parts = filePath.split('/').filter(p => p.length > 0);
    if (parts.length === 0) throw new Error("Invalid path");

    let currentHandle: FileSystemDirectoryHandle = this.rootHandle;

    // Traverse directories
    for (let i = 0; i < parts.length - 1; i++) {
      currentHandle = await currentHandle.getDirectoryHandle(parts[i]);
    }

    // Get file handle and read
    const fileHandle = await currentHandle.getFileHandle(parts[parts.length - 1]);
    const file = await fileHandle.getFile();
    return await file.text();
  }

  /**
   * Recursively traverses a directory and returns its structure.
   */
  private async traverseDirectory(
    dirHandle: FileSystemDirectoryHandle, 
    currentPath: string
  ): Promise<ReportDirectory> {
    const dir: ReportDirectory = {
      name: dirHandle.name,
      path: currentPath,
      files: [],
      directories: [],
    };

    // @ts-ignore - TS doesn't fully support async iterators for FileSystem API yet without proper dom libs configured
    for await (const [name, handle] of (dirHandle as any).entries()) {
      const childPath = currentPath ? `${currentPath}/${name}` : name;
      
      if (handle.kind === 'file') {
        if (name.endsWith('.md') || name.endsWith('.json')) {
          dir.files.push({
            name,
            path: childPath,
            handle,
          });
        }
      } else if (handle.kind === 'directory') {
        const subDirHandle = handle as FileSystemDirectoryHandle;
        const subDir = await this.traverseDirectory(subDirHandle, childPath);
        dir.directories.push(subDir);
      }
    }

    // Sort files and directories for consistent display
    dir.files.sort((a, b) => a.name.localeCompare(b.name));
    dir.directories.sort((a, b) => b.name.localeCompare(a.name)); // Reverse alphabetical for dates (newest first)

    return dir;
  }

  /**
   * Finds a file in the directory structure by its path.
   */
  findFileByPath(dir: ReportDirectory, path: string): ReportFile | null {
    // Check if any file in current dir matches
    const file = dir.files.find(f => f.path === path);
    if (file) return file;

    // Search subdirectories
    for (const subDir of dir.directories) {
      const found = this.findFileByPath(subDir, path);
      if (found) return found;
    }

    return null;
  }

  /**
   * Gets the entire reports directory structure.
   */
  async listReports(): Promise<ReportDirectory | null> {
    try {
      const reportsHandle = await this.rootHandle.getDirectoryHandle('reports');
      return await this.traverseDirectory(reportsHandle, 'reports');
    } catch (e) {
      console.error("Could not find or read 'reports' directory:", e);
      return null;
    }
  }
}
