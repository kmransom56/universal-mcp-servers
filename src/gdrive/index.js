import { config } from 'dotenv';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import { google } from 'googleapis';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, '../../.env') });

const app = express();
app.use(express.json());

const PORT = process.env.PORT_GDRIVE || 3012;

const oauth2Client = new google.auth.OAuth2(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  process.env.GOOGLE_REDIRECT_URI
);

oauth2Client.setCredentials({
  refresh_token: process.env.GOOGLE_REFRESH_TOKEN
});

const drive = google.drive({ version: 'v3', auth: oauth2Client });

app.post('/upload', async (req, res) => {
  try {
    const { name, mimeType, content } = req.body;
    
    if (!name || !mimeType || !content) {
      throw new Error('Name, mimeType, and content are required');
    }
    
    const buffer = Buffer.from(content, 'base64');
    
    const response = await drive.files.create({
      requestBody: {
        name,
        mimeType
      },
      media: {
        mimeType,
        body: buffer
      }
    });
    
    res.json(response.data);
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/list', async (req, res) => {
  try {
    const { pageSize = 10, pageToken, query } = req.query;
    
    const response = await drive.files.list({
      pageSize: parseInt(pageSize),
      pageToken,
      q: query,
      fields: 'nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size)'
    });
    
    res.json(response.data);
  } catch (error) {
    console.error('Error listing files:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/download/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    
    const response = await drive.files.get({
      fileId,
      alt: 'media'
    }, {
      responseType: 'arraybuffer'
    });
    
    const buffer = Buffer.from(response.data);
    const content = buffer.toString('base64');
    
    res.json({ content });
  } catch (error) {
    console.error('Error downloading file:', error);
    res.status(500).json({ error: error.message });
  }
});

app.delete('/delete/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    
    await drive.files.delete({
      fileId
    });
    
    res.json({ success: true });
  } catch (error) {
    console.error('Error deleting file:', error);
    res.status(500).json({ error: error.message });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  try {
    if (!process.env.GOOGLE_CLIENT_ID || !process.env.GOOGLE_CLIENT_SECRET || !process.env.GOOGLE_REFRESH_TOKEN) {
      throw new Error('Google Drive credentials are not properly configured');
    }
    res.json({
      status: 'healthy',
      message: 'Google Drive server is ready'
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Google Drive server is not healthy',
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`Google Drive server running on port ${PORT}`);
}); 