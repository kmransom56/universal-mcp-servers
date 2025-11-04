const express = require('express');
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3004;
const TEMP_DIR = process.env.IMAGE_PROCESSING_TEMP_DIR;

// Ensure temp directory exists
if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true });
}

app.post('/resize', async (req, res) => {
  try {
    const { inputPath, width, height, outputFilename } = req.body;
    const outputPath = path.join(TEMP_DIR, outputFilename);
    
    await sharp(inputPath)
      .resize(width, height, {
        fit: 'contain',
        background: { r: 255, g: 255, b: 255, alpha: 1 }
      })
      .toFile(outputPath);
    
    res.json({ path: outputPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/convert', async (req, res) => {
  try {
    const { inputPath, format, quality, outputFilename } = req.body;
    const outputPath = path.join(TEMP_DIR, outputFilename);
    
    const image = sharp(inputPath);
    switch (format.toLowerCase()) {
      case 'jpeg':
      case 'jpg':
        await image.jpeg({ quality: quality || 80 }).toFile(outputPath);
        break;
      case 'png':
        await image.png({ quality: quality || 80 }).toFile(outputPath);
        break;
      case 'webp':
        await image.webp({ quality: quality || 80 }).toFile(outputPath);
        break;
      default:
        throw new Error('Unsupported format');
    }
    
    res.json({ path: outputPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/optimize', async (req, res) => {
  try {
    const { inputPath, outputFilename } = req.body;
    const outputPath = path.join(TEMP_DIR, outputFilename);
    
    await sharp(inputPath)
      .jpeg({ quality: 80, mozjpeg: true })
      .toFile(outputPath);
    
    res.json({ path: outputPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Image Processing server running on port ${PORT}`);
}); 