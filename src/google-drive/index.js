const express = require('express');
const { google } = require('googleapis');
const fs = require('fs').promises;
const path = require('path');
const stream = require('stream');
const { promisify } = require('util');
const pipeline = promisify(stream.pipeline);

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3012;
const TEMP_DIR = process.env.GDRIVE_TEMP_DIR;

// Ensure temp directory exists
if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true });
}

// Initialize Google Drive API client
function getDriveClient() {
  const auth = new google.auth.GoogleAuth({
    keyFile: process.env.GOOGLE_APPLICATION_CREDENTIALS,
    scopes: ['https://www.googleapis.com/auth/drive']
  });
  
  return google.drive({ version: 'v3', auth });
}

app.post('/upload', async (req, res) => {
  try {
    const { filePath, parentFolderId, mimeType } = req.body;
    const drive = getDriveClient();
    
    const fileMetadata = {
      name: path.basename(filePath),
      parents: parentFolderId ? [parentFolderId] : undefined
    };
    
    const media = {
      mimeType: mimeType || 'application/octet-stream',
      body: fs.createReadStream(filePath)
    };
    
    const file = await drive.files.create({
      requestBody: fileMetadata,
      media: media,
      fields: 'id, name, mimeType, size, webViewLink, webContentLink'
    });
    
    res.json({
      fileId: file.data.id,
      name: file.data.name,
      mimeType: file.data.mimeType,
      size: file.data.size,
      webViewLink: file.data.webViewLink,
      webContentLink: file.data.webContentLink
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/download', async (req, res) => {
  try {
    const { fileId, outputFilename } = req.body;
    const drive = getDriveClient();
    const outputPath = path.join(TEMP_DIR, outputFilename);
    
    const response = await drive.files.get(
      { fileId, alt: 'media' },
      { responseType: 'stream' }
    );
    
    const dest = fs.createWriteStream(outputPath);
    await pipeline(response.data, dest);
    
    const metadata = await drive.files.get({
      fileId,
      fields: 'name, mimeType, size, modifiedTime'
    });
    
    res.json({
      path: outputPath,
      name: metadata.data.name,
      mimeType: metadata.data.mimeType,
      size: metadata.data.size,
      modifiedTime: metadata.data.modifiedTime
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/list', async (req, res) => {
  try {
    const { folderId, query, pageSize = 100, pageToken } = req.body;
    const drive = getDriveClient();
    
    let queryString = query || '';
    if (folderId) {
      queryString = `${queryString ? queryString + ' and ' : ''}'${folderId}' in parents`;
    }
    
    const response = await drive.files.list({
      q: queryString,
      pageSize,
      pageToken,
      fields: 'nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink)'
    });
    
    res.json({
      files: response.data.files,
      nextPageToken: response.data.nextPageToken
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/create-folder', async (req, res) => {
  try {
    const { name, parentFolderId } = req.body;
    const drive = getDriveClient();
    
    const fileMetadata = {
      name,
      mimeType: 'application/vnd.google-apps.folder',
      parents: parentFolderId ? [parentFolderId] : undefined
    };
    
    const folder = await drive.files.create({
      requestBody: fileMetadata,
      fields: 'id, name, mimeType, webViewLink'
    });
    
    res.json({
      folderId: folder.data.id,
      name: folder.data.name,
      mimeType: folder.data.mimeType,
      webViewLink: folder.data.webViewLink
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/delete', async (req, res) => {
  try {
    const { fileId } = req.body;
    const drive = getDriveClient();
    
    await drive.files.delete({ fileId });
    
    res.json({
      fileId,
      deleted: true
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/share', async (req, res) => {
  try {
    const { fileId, role, type, emailAddress } = req.body;
    const drive = getDriveClient();
    
    const permission = {
      role: role || 'reader',
      type: type || 'user',
      emailAddress
    };
    
    const result = await drive.permissions.create({
      fileId,
      requestBody: permission,
      fields: 'id, emailAddress, role, type'
    });
    
    res.json({
      permissionId: result.data.id,
      emailAddress: result.data.emailAddress,
      role: result.data.role,
      type: result.data.type
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/copy', async (req, res) => {
  try {
    const { fileId, name, parentFolderId } = req.body;
    const drive = getDriveClient();
    
    const requestBody = {
      name,
      parents: parentFolderId ? [parentFolderId] : undefined
    };
    
    const file = await drive.files.copy({
      fileId,
      requestBody,
      fields: 'id, name, mimeType, size, webViewLink, webContentLink'
    });
    
    res.json({
      fileId: file.data.id,
      name: file.data.name,
      mimeType: file.data.mimeType,
      size: file.data.size,
      webViewLink: file.data.webViewLink,
      webContentLink: file.data.webContentLink
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Google Drive server running on port ${PORT}`);
}); 