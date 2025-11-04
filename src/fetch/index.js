import { config } from 'dotenv';
import { dirname, resolve, join } from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import fetch from 'node-fetch';
import FormData from 'form-data';
import { promises as fs, createWriteStream, existsSync, mkdirSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, '../../.env') });

const app = express();
app.use(express.json());

const PORT = process.env.PORT_FETCH || 3011;
const TEMP_DIR = process.env.FETCH_TEMP_DIR || join(__dirname, 'temp');

// Ensure temp directory exists
if (!existsSync(TEMP_DIR)) {
  mkdirSync(TEMP_DIR, { recursive: true });
}

app.post('/request', async (req, res) => {
  try {
    const {
      url,
      method = 'GET',
      headers = {},
      body,
      responseType = 'json',
      outputFilename
    } = req.body;

    const options = {
      method,
      headers: {
        ...headers,
        'User-Agent': 'MCP-Fetch-Server/1.0'
      }
    };

    if (body) {
      if (typeof body === 'object') {
        options.body = JSON.stringify(body);
        options.headers['Content-Type'] = 'application/json';
      } else {
        options.body = body;
      }
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    let data;
    switch (responseType) {
      case 'json':
        data = await response.json();
        break;
      case 'text':
        data = await response.text();
        break;
      case 'buffer':
        data = await response.buffer();
        if (outputFilename) {
          const outputPath = join(TEMP_DIR, outputFilename);
          await fs.writeFile(outputPath, data);
          return res.json({
            path: outputPath,
            size: data.length,
            headers: Object.fromEntries(response.headers.entries())
          });
        }
        break;
      default:
        throw new Error('Unsupported response type');
    }

    res.json({
      data,
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries())
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/upload', async (req, res) => {
  try {
    const { url, files, fields = {}, headers = {} } = req.body;
    
    const form = new FormData();
    
    // Add fields
    Object.entries(fields).forEach(([key, value]) => {
      form.append(key, value);
    });
    
    // Add files
    for (const file of files) {
      const content = await fs.readFile(file.path);
      form.append(file.fieldName || 'file', content, file.filename || path.basename(file.path));
    }
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        ...headers,
        ...form.getHeaders()
      },
      body: form
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    res.json({
      data,
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries())
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/download', async (req, res) => {
  try {
    const { url, outputFilename, headers = {} } = req.body;
    const outputPath = path.join(TEMP_DIR, outputFilename);
    
    const response = await fetch(url, {
      headers: {
        ...headers,
        'User-Agent': 'MCP-Fetch-Server/1.0'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const buffer = await response.buffer();
    await fs.writeFile(outputPath, buffer);
    
    res.json({
      path: outputPath,
      size: buffer.length,
      type: response.headers.get('content-type'),
      headers: Object.fromEntries(response.headers.entries())
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/stream', async (req, res) => {
  try {
    const { url, outputFilename, headers = {} } = req.body;
    const outputPath = path.join(TEMP_DIR, outputFilename);
    
    const response = await fetch(url, {
      headers: {
        ...headers,
        'User-Agent': 'MCP-Fetch-Server/1.0'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const fileStream = fs.createWriteStream(outputPath);
    
    await new Promise((resolve, reject) => {
      response.body.pipe(fileStream)
        .on('finish', resolve)
        .on('error', reject);
    });
    
    const stats = await fs.stat(outputPath);
    
    res.json({
      path: outputPath,
      size: stats.size,
      type: response.headers.get('content-type'),
      headers: Object.fromEntries(response.headers.entries())
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Fetch server running on port ${PORT}`);
}); 