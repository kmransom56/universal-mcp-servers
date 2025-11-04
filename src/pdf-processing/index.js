import { config } from 'dotenv';
import { dirname, resolve, join } from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import PDFDocument from 'pdfkit';
import PDFTableExtractor from 'pdf-table-extractor';
import { promises as fs } from 'fs';
import * as fsSync from 'fs';
import { PDFDocument as PDFLib } from 'pdf-lib';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, '../../.env') });

const app = express();
app.use(express.json());

const PORT = process.env.PORT_PDF || 3002;
const TEMP_DIR = process.env.PDF_PROCESSING_TEMP_DIR || join(__dirname, 'temp');

// Ensure temp directory exists
try {
  if (!fsSync.existsSync(TEMP_DIR)) {
    fsSync.mkdirSync(TEMP_DIR, { recursive: true });
  }
} catch (error) {
  console.error('Failed to create temp directory:', error.message);
  process.exit(1);
}

// Promise wrapper for PDFTableExtractor
function extractTables(pdfPath) {
  return new Promise((resolve, reject) => {
    PDFTableExtractor(pdfPath, result => {
      resolve(result);
    }, error => {
      reject(error);
    });
  });
}

// Helper function to detect header row
function detectHeaderRow(table) {
  if (!table || table.length < 2) return 0;
  
  // Heuristics for header detection:
  // 1. First row often contains column names
  // 2. Check if first row cells are shorter than average
  // 3. Check if first row has different formatting (all cells filled)
  const firstRow = table[0];
  const otherRows = table.slice(1);
  
  const firstRowAvgLength = firstRow.reduce((sum, cell) => sum + cell.length, 0) / firstRow.length;
  const otherRowsAvgLength = otherRows.reduce((sum, row) => 
    sum + row.reduce((rowSum, cell) => rowSum + cell.length, 0) / row.length, 0) / otherRows.length;
  
  const firstRowComplete = firstRow.every(cell => cell.trim().length > 0);
  const otherRowsIncomplete = otherRows.some(row => row.some(cell => cell.trim().length === 0));
  
  return (firstRowAvgLength < otherRowsAvgLength || (firstRowComplete && otherRowsIncomplete)) ? 0 : -1;
}

// Helper function to convert table to various formats
function convertTableToFormat(table, format, headers = null) {
  switch (format.toLowerCase()) {
    case 'csv':
      return table.map(row => row.join(',')).join('\n');
      
    case 'excel':
      // Return format suitable for Excel (CSV with extra processing)
      return table.map(row => 
        row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(',')
      ).join('\n');
      
    case 'markdown':
      if (table.length === 0) return '';
      const mdHeader = table[0].map(cell => cell.trim()).join(' | ');
      const mdSeparator = table[0].map(() => '---').join(' | ');
      const mdBody = table.slice(1).map(row => row.map(cell => cell.trim()).join(' | ')).join('\n');
      return `| ${mdHeader} |\n| ${mdSeparator} |\n${mdBody.split('\n').map(line => `| ${line} |`).join('\n')}`;
      
    case 'html':
      const headerRow = headers ? `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>` : '';
      const bodyRows = table.map(row => 
        `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`
      ).join('\n');
      return `<table>\n${headerRow}\n${bodyRows}\n</table>`;
      
    case 'objects':
      if (table.length < 2) return [];
      const columnNames = headers || table[0];
      return table.slice(headers ? 0 : 1).map(row => 
        Object.fromEntries(row.map((cell, i) => [columnNames[i], cell]))
      );
      
    default: // json
      return table;
  }
}

app.post('/parse-tables', async (req, res) => {
  try {
    const {
      inputPath,
      outputFormat = 'json',
      pageNumbers = [], // Optional: specific pages to process
      tableIndices = [], // Optional: specific tables to extract
      detectHeaders = false, // Optional: auto-detect header rows
      columnMap = null, // Optional: map for column names
      skipEmptyRows = true // Optional: skip rows with all empty cells
    } = req.body;

    const result = await extractTables(inputPath);
    
    // Filter and process tables
    let processedTables = result.pageTables.map((page, pageIndex) => {
      // Filter by page numbers if specified
      if (pageNumbers.length > 0 && !pageNumbers.includes(pageIndex + 1)) {
        return [];
      }

      return page.tables.map((table, tableIndex) => {
        // Filter by table indices if specified
        if (tableIndices.length > 0 && !tableIndices.includes(tableIndex)) {
          return null;
        }

        // Clean and process table data
        let processedTable = table.map(row => 
          row.map(cell => cell.trim())
        );

        // Skip empty rows if requested
        if (skipEmptyRows) {
          processedTable = processedTable.filter(row => 
            row.some(cell => cell.length > 0)
          );
        }

        // Detect headers if requested
        let headers = null;
        if (detectHeaders) {
          const headerIndex = detectHeaderRow(processedTable);
          if (headerIndex >= 0) {
            headers = processedTable[headerIndex];
            processedTable = processedTable.slice(headerIndex + 1);
          }
        }

        // Apply column mapping if provided
        if (columnMap && headers) {
          headers = headers.map(header => columnMap[header] || header);
        }

        return {
          pageNumber: pageIndex + 1,
          tableIndex,
          headers,
          data: processedTable
        };
      }).filter(Boolean); // Remove null tables
    }).flat();

    // Generate output filename
    const outputFilename = path.basename(inputPath, '.pdf') + '_tables.' + outputFormat;
    const outputPath = path.join(TEMP_DIR, outputFilename);

    // Convert tables to requested format and save
    const formattedTables = processedTables.map(table => ({
      ...table,
      data: convertTableToFormat(table.data, outputFormat, table.headers)
    }));

    // Save the results
    fs.writeFileSync(outputPath, JSON.stringify(formattedTables, null, 2));

    res.json({
      path: outputPath,
      tables: formattedTables.map(table => ({
        pageNumber: table.pageNumber,
        tableIndex: table.tableIndex,
        rowCount: table.data.length,
        headers: table.headers
      }))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/create', async (req, res) => {
  try {
    const { content, filename = 'output.pdf', options = {} } = req.body;
    
    if (!content) {
      throw new Error('Content is required');
    }

    const outputPath = join(TEMP_DIR, filename);
    const doc = new PDFDocument(options);
    const writeStream = fsSync.createWriteStream(outputPath);

    // Set up error handling for the stream
    writeStream.on('error', (error) => {
      console.error('Error writing PDF:', error);
      res.status(500).json({ error: error.message });
    });

    // Handle content writing
    doc.pipe(writeStream);
    doc.text(content);
    doc.end();

    // Wait for the write stream to finish
    await new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });

    res.json({
      path: outputPath,
      filename
    });
  } catch (error) {
    console.error('Error creating PDF:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/merge', async (req, res) => {
  try {
    const { files, outputFilename = 'merged.pdf' } = req.body;
    
    if (!Array.isArray(files) || files.length === 0) {
      throw new Error('Files array is required and must not be empty');
    }

    // Create a new PDF document
    const mergedPdf = await PDFLib.create();

    // Add each PDF file to the merged document
    for (const file of files) {
      const pdfBytes = await fs.readFile(file);
      const pdf = await PDFLib.load(pdfBytes);
      const copiedPages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
      copiedPages.forEach((page) => mergedPdf.addPage(page));
    }

    // Save the merged PDF
    const outputPath = join(TEMP_DIR, outputFilename);
    const mergedPdfBytes = await mergedPdf.save();
    await fs.writeFile(outputPath, mergedPdfBytes);

    res.json({
      path: outputPath,
      filename: outputFilename
    });
  } catch (error) {
    console.error('Error merging PDFs:', error);
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
      message: 'PDF processing server is ready'
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'error',
      message: 'PDF processing server is not healthy',
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`PDF processing server running on port ${PORT}`);
}); 