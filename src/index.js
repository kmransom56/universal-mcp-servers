const { trustCustomCA } = require("ssl-helper");
trustCustomCA();

import { config } from 'dotenv';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, '../.env') });

// Import all server modules
import './audio-processing/index.js';
import './video-processing/index.js';
import './gdrive/index.js';
import './data-validation/index.js';
import './pdf-processing/index.js';
import './spreadsheet-processing/index.js';
import './openai/index.js';
import './fetch/index.js';

console.log('All MCP servers started successfully!');
console.log(`
Server Status:
- Audio Processing: Running on port ${process.env.PORT_AUDIO || 3007}
- Video Processing: Running on port ${process.env.PORT_VIDEO || 3006}
- Google Drive: Running on port ${process.env.PORT_GDRIVE || 3012}
- Data Validation: Running on port ${process.env.PORT_DATA_VALIDATION || 3008}
- PDF Processing: Running on port ${process.env.PORT_PDF || 3002}
- Spreadsheet Processing: Running on port ${process.env.PORT_SPREADSHEET || 3003}
- OpenAI: Running on port ${process.env.PORT_OPENAI || 3014}
- Fetch: Running on port ${process.env.PORT_FETCH || 3011}
`); 
