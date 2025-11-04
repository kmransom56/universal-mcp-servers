const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const chokidar = require('chokidar');
const glob = require('glob-promise');
const mkdirp = require('mkdirp');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3010;
const WORKSPACE_DIR = process.env.WORKSPACE_DIR || process.cwd();

// File watchers store
const watchers = new Map();

app.post('/read', async (req, res) => {
  try {
    const { filePath, encoding = 'utf8' } = req.body;
    const absolutePath = path.resolve(WORKSPACE_DIR, filePath);
    const content = await fs.readFile(absolutePath, encoding);
    
    res.json({
      content,
      path: absolutePath,
      size: (await fs.stat(absolutePath)).size
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/write', async (req, res) => {
  try {
    const { filePath, content, encoding = 'utf8' } = req.body;
    const absolutePath = path.resolve(WORKSPACE_DIR, filePath);
    
    // Ensure directory exists
    await mkdirp(path.dirname(absolutePath));
    await fs.writeFile(absolutePath, content, encoding);
    
    res.json({
      path: absolutePath,
      size: (await fs.stat(absolutePath)).size
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/copy', async (req, res) => {
  try {
    const { sourcePath, destinationPath, overwrite = false } = req.body;
    const sourceAbs = path.resolve(WORKSPACE_DIR, sourcePath);
    const destAbs = path.resolve(WORKSPACE_DIR, destinationPath);
    
    // Ensure destination directory exists
    await mkdirp(path.dirname(destAbs));
    
    if (!overwrite && (await fs.stat(destAbs).catch(() => false))) {
      throw new Error('Destination already exists');
    }
    
    await fs.copyFile(sourceAbs, destAbs);
    
    res.json({
      source: sourceAbs,
      destination: destAbs,
      size: (await fs.stat(destAbs)).size
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/move', async (req, res) => {
  try {
    const { sourcePath, destinationPath, overwrite = false } = req.body;
    const sourceAbs = path.resolve(WORKSPACE_DIR, sourcePath);
    const destAbs = path.resolve(WORKSPACE_DIR, destinationPath);
    
    // Ensure destination directory exists
    await mkdirp(path.dirname(destAbs));
    
    if (!overwrite && (await fs.stat(destAbs).catch(() => false))) {
      throw new Error('Destination already exists');
    }
    
    await fs.rename(sourceAbs, destAbs);
    
    res.json({
      source: sourceAbs,
      destination: destAbs
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/delete', async (req, res) => {
  try {
    const { filePath, recursive = false } = req.body;
    const absolutePath = path.resolve(WORKSPACE_DIR, filePath);
    
    if (recursive) {
      await fs.rm(absolutePath, { recursive: true, force: true });
    } else {
      await fs.unlink(absolutePath);
    }
    
    res.json({
      path: absolutePath,
      deleted: true
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/list', async (req, res) => {
  try {
    const { dirPath, pattern } = req.body;
    const absolutePath = path.resolve(WORKSPACE_DIR, dirPath);
    
    let files;
    if (pattern) {
      files = await glob(path.join(absolutePath, pattern));
    } else {
      files = await fs.readdir(absolutePath, { withFileTypes: true });
      files = await Promise.all(files.map(async (dirent) => {
        const fullPath = path.join(absolutePath, dirent.name);
        const stats = await fs.stat(fullPath);
        return {
          name: dirent.name,
          path: fullPath,
          type: dirent.isDirectory() ? 'directory' : 'file',
          size: stats.size,
          modified: stats.mtime
        };
      }));
    }
    
    res.json({
      path: absolutePath,
      contents: files
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/watch', async (req, res) => {
  try {
    const { dirPath, pattern } = req.body;
    const absolutePath = path.resolve(WORKSPACE_DIR, dirPath);
    const watchId = Buffer.from(absolutePath).toString('base64');
    
    if (watchers.has(watchId)) {
      throw new Error('Already watching this path');
    }
    
    const watcher = chokidar.watch(pattern ? path.join(absolutePath, pattern) : absolutePath, {
      persistent: true,
      ignoreInitial: true
    });
    
    // Store watcher reference
    watchers.set(watchId, watcher);
    
    // Set up WebSocket connection for real-time updates
    watcher
      .on('add', path => res.write(JSON.stringify({ event: 'add', path })))
      .on('change', path => res.write(JSON.stringify({ event: 'change', path })))
      .on('unlink', path => res.write(JSON.stringify({ event: 'delete', path })))
      .on('error', error => res.write(JSON.stringify({ event: 'error', error: error.message })));
    
    res.json({
      watchId,
      path: absolutePath,
      pattern: pattern || '*'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/unwatch', async (req, res) => {
  try {
    const { watchId } = req.body;
    
    if (!watchers.has(watchId)) {
      throw new Error('Watch ID not found');
    }
    
    const watcher = watchers.get(watchId);
    await watcher.close();
    watchers.delete(watchId);
    
    res.json({
      watchId,
      unwatched: true
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/stats', async (req, res) => {
  try {
    const { filePath } = req.body;
    const absolutePath = path.resolve(WORKSPACE_DIR, filePath);
    const stats = await fs.stat(absolutePath);
    
    res.json({
      path: absolutePath,
      size: stats.size,
      created: stats.birthtime,
      modified: stats.mtime,
      accessed: stats.atime,
      isDirectory: stats.isDirectory(),
      isFile: stats.isFile(),
      isSymbolicLink: stats.isSymbolicLink(),
      mode: stats.mode.toString(8)
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Filesystem server running on port ${PORT}`);
}); 