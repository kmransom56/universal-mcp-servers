const express = require('express');
const archiver = require('archiver');
const unzipper = require('unzipper');
const tar = require('tar');
const zlib = require('zlib');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3009;
const TEMP_DIR = process.env.FILE_COMPRESSION_TEMP_DIR;

// Ensure temp directory exists
if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true });
}

app.post('/compress', async (req, res) => {
  try {
    const { inputPaths, outputFilename, format = 'zip', level = 9 } = req.body;
    const outputPath = path.join(TEMP_DIR, outputFilename);

    switch (format.toLowerCase()) {
      case 'zip': {
        const output = fs.createWriteStream(outputPath);
        const archive = archiver('zip', {
          zlib: { level }
        });

        await new Promise((resolve, reject) => {
          output.on('close', resolve);
          archive.on('error', reject);
          archive.pipe(output);

          inputPaths.forEach(inputPath => {
            const stats = fs.statSync(inputPath);
            if (stats.isDirectory()) {
              archive.directory(inputPath, path.basename(inputPath));
            } else {
              archive.file(inputPath, { name: path.basename(inputPath) });
            }
          });

          archive.finalize();
        });
        break;
      }

      case 'tar': {
        await tar.c(
          {
            gzip: true,
            file: outputPath,
            cwd: path.dirname(inputPaths[0])
          },
          inputPaths.map(p => path.basename(p))
        );
        break;
      }

      case 'gz': {
        if (inputPaths.length > 1) {
          throw new Error('GZ format only supports single file compression');
        }
        const input = fs.createReadStream(inputPaths[0]);
        const output = fs.createWriteStream(outputPath);
        await new Promise((resolve, reject) => {
          input
            .pipe(zlib.createGzip({ level }))
            .pipe(output)
            .on('finish', resolve)
            .on('error', reject);
        });
        break;
      }

      default:
        throw new Error('Unsupported compression format');
    }

    res.json({
      path: outputPath,
      format,
      originalSize: inputPaths.reduce((size, file) => size + fs.statSync(file).size, 0),
      compressedSize: fs.statSync(outputPath).size
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/decompress', async (req, res) => {
  try {
    const { inputPath, outputDir } = req.body;
    const format = path.extname(inputPath).toLowerCase();
    const extractDir = path.join(TEMP_DIR, outputDir);

    // Ensure output directory exists
    if (!fs.existsSync(extractDir)) {
      fs.mkdirSync(extractDir, { recursive: true });
    }

    switch (format) {
      case '.zip': {
        const directory = await unzipper.Open.file(inputPath);
        await directory.extract({ path: extractDir });
        break;
      }

      case '.tar':
      case '.tgz': {
        await tar.x({
          file: inputPath,
          cwd: extractDir
        });
        break;
      }

      case '.gz': {
        const filename = path.basename(inputPath, '.gz');
        const output = fs.createWriteStream(path.join(extractDir, filename));
        await new Promise((resolve, reject) => {
          fs.createReadStream(inputPath)
            .pipe(zlib.createGunzip())
            .pipe(output)
            .on('finish', resolve)
            .on('error', reject);
        });
        break;
      }

      default:
        throw new Error('Unsupported decompression format');
    }

    res.json({
      path: extractDir,
      format: format.substring(1)
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/list-contents', async (req, res) => {
  try {
    const { inputPath } = req.body;
    const format = path.extname(inputPath).toLowerCase();
    let contents = [];

    switch (format) {
      case '.zip': {
        const directory = await unzipper.Open.file(inputPath);
        contents = directory.files.map(file => ({
          name: file.path,
          size: file.uncompressedSize,
          compressedSize: file.compressedSize,
          type: file.type // 'File' or 'Directory'
        }));
        break;
      }

      case '.tar':
      case '.tgz': {
        contents = await new Promise((resolve, reject) => {
          const entries = [];
          tar.t({
            file: inputPath,
            onentry: entry => {
              entries.push({
                name: entry.path,
                size: entry.size,
                type: entry.type // 'File' or 'Directory'
              });
            }
          }).then(() => resolve(entries)).catch(reject);
        });
        break;
      }

      default:
        throw new Error('Unsupported format for listing contents');
    }

    res.json({
      format: format.substring(1),
      contents
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/add-to-archive', async (req, res) => {
  try {
    const { archivePath, filesToAdd, outputFilename } = req.body;
    const outputPath = path.join(TEMP_DIR, outputFilename);
    const format = path.extname(archivePath).toLowerCase();

    if (format !== '.zip') {
      throw new Error('Only ZIP archives support adding files');
    }

    const output = fs.createWriteStream(outputPath);
    const archive = archiver('zip');

    await new Promise((resolve, reject) => {
      output.on('close', resolve);
      archive.on('error', reject);
      archive.pipe(output);

      // Add existing contents
      fs.createReadStream(archivePath)
        .pipe(unzipper.Parse())
        .on('entry', entry => {
          const buffer = [];
          entry.on('data', data => buffer.push(data));
          entry.on('end', () => {
            archive.append(Buffer.concat(buffer), { name: entry.path });
          });
        })
        .on('finish', () => {
          // Add new files
          filesToAdd.forEach(file => {
            const stats = fs.statSync(file);
            if (stats.isDirectory()) {
              archive.directory(file, path.basename(file));
            } else {
              archive.file(file, { name: path.basename(file) });
            }
          });
          archive.finalize();
        });
    });

    res.json({
      path: outputPath,
      format: 'zip'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`File Compression server running on port ${PORT}`);
}); 