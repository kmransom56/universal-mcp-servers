import { config } from 'dotenv';
import { dirname, resolve, join } from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import xlsx from 'xlsx';
import { promises as fs } from 'fs';
import * as fsSync from 'fs';
import { parse } from 'csv-parse/sync';
import { stringify } from 'csv-stringify/sync';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, '../../.env') });

const app = express();
app.use(express.json());

const PORT = process.env.PORT_SPREADSHEET || 3003;
const TEMP_DIR = process.env.SPREADSHEET_PROCESSING_TEMP_DIR || join(__dirname, 'temp');

// Ensure temp directory exists
try {
  if (!fsSync.existsSync(TEMP_DIR)) {
    fsSync.mkdirSync(TEMP_DIR, { recursive: true });
  }
} catch (error) {
  console.error('Failed to create temp directory:', error.message);
  process.exit(1);
}

app.post('/convert', async (req, res) => {
  try {
    const { 
      inputFile, 
      outputFormat = 'xlsx',
      outputFilename,
      sheetName,
      options = {}
    } = req.body;

    if (!inputFile) {
      throw new Error('Input file is required');
    }

    // Read the input file
    const inputBuffer = await fs.readFile(inputFile);
    let workbook;

    try {
      workbook = xlsx.read(inputBuffer, { type: 'buffer', ...options });
    } catch (error) {
      throw new Error(`Failed to read spreadsheet: ${error.message}`);
    }

    const defaultFilename = `output.${outputFormat}`;
    const finalOutputFilename = outputFilename || defaultFilename;
    const outputPath = join(TEMP_DIR, finalOutputFilename);

    switch (outputFormat.toLowerCase()) {
      case 'csv': {
        // Get the first sheet if no sheet name specified
        const ws = sheetName ? 
          workbook.Sheets[sheetName] : 
          workbook.Sheets[workbook.SheetNames[0]];
        
        if (!ws) {
          throw new Error('Sheet not found');
        }

        const csvData = xlsx.utils.sheet_to_csv(ws, options);
        await fs.writeFile(outputPath, csvData);
        break;
      }

      case 'json': {
        const ws = sheetName ? 
          workbook.Sheets[sheetName] : 
          workbook.Sheets[workbook.SheetNames[0]];
        
        if (!ws) {
          throw new Error('Sheet not found');
        }

        const jsonData = xlsx.utils.sheet_to_json(ws, options);
        await fs.writeFile(outputPath, JSON.stringify(jsonData, null, 2));
        break;
      }

      default: {
        // Default to xlsx format
        await fs.writeFile(outputPath, xlsx.write(workbook, { 
          type: 'buffer',
          bookType: outputFormat,
          ...options
        }));
      }
    }

    res.json({
      path: outputPath,
      format: outputFormat,
      filename: finalOutputFilename
    });
  } catch (error) {
    console.error('Error converting spreadsheet:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/merge', async (req, res) => {
  try {
    const { 
      files,
      outputFilename = 'merged.xlsx',
      sheetNames = [],
      options = {}
    } = req.body;

    if (!Array.isArray(files) || files.length === 0) {
      throw new Error('Files array is required and must not be empty');
    }

    // Create a new workbook
    const mergedWorkbook = xlsx.utils.book_new();

    // Process each file
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileBuffer = await fs.readFile(file);
      const workbook = xlsx.read(fileBuffer, { type: 'buffer', ...options });
      
      // Get the first sheet
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];
      
      // Add the sheet to the merged workbook
      const sheetName = sheetNames[i] || `Sheet${i + 1}`;
      xlsx.utils.book_append_sheet(mergedWorkbook, worksheet, sheetName);
    }

    const outputPath = join(TEMP_DIR, outputFilename);
    
    // Write the merged workbook
    const outputBuffer = xlsx.write(mergedWorkbook, { type: 'buffer', ...options });
    await fs.writeFile(outputPath, outputBuffer);

    res.json({
      path: outputPath,
      filename: outputFilename,
      sheetCount: mergedWorkbook.SheetNames.length
    });
  } catch (error) {
    console.error('Error merging spreadsheets:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/extract-tables', async (req, res) => {
  try {
    const { 
      inputFile,
      outputFormat = 'json',
      sheetName,
      options = {}
    } = req.body;

    if (!inputFile) {
      throw new Error('Input file is required');
    }

    const inputBuffer = await fs.readFile(inputFile);
    const workbook = xlsx.read(inputBuffer, { type: 'buffer', ...options });
    
    const ws = sheetName ? 
      workbook.Sheets[sheetName] : 
      workbook.Sheets[workbook.SheetNames[0]];

    if (!ws) {
      throw new Error('Sheet not found');
    }

    // Extract tables based on format
    let tables;
    if (outputFormat === 'json') {
      tables = xlsx.utils.sheet_to_json(ws, { 
        header: 1,
        raw: false,
        ...options
      });
    } else {
      tables = xlsx.utils.sheet_to_csv(ws, options);
    }

    res.json({
      tables,
      format: outputFormat,
      sheetName: sheetName || workbook.SheetNames[0]
    });
  } catch (error) {
    console.error('Error extracting tables:', error);
    res.status(500).json({ error: error.message });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  try {
    // Check if temp directory is accessible
    fsSync.accessSync(TEMP_DIR, fsSync.constants.R_OK | fsSync.constants.W_OK);
    res.json({ 
      status: 'healthy',
      tempDir: TEMP_DIR,
      message: 'Spreadsheet processing server is ready'
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'error',
      message: 'Spreadsheet processing server is not healthy',
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`Spreadsheet processing server running on port ${PORT}`);
}); 