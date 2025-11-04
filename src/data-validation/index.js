import { config } from 'dotenv';
import { dirname, resolve, join } from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import Joi from 'joi';
import validator from 'validator';
import { existsSync, mkdirSync, writeFileSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, '../../.env') });

const app = express();
app.use(express.json());

const PORT = process.env.PORT_DATA_VALIDATION || 3008;
const TEMP_DIR = process.env.DATA_VALIDATION_TEMP_DIR || join(__dirname, 'temp');

// Ensure temp directory exists
if (!existsSync(TEMP_DIR)) {
  mkdirSync(TEMP_DIR, { recursive: true });
}

// Common validation schemas
const commonSchemas = {
  email: Joi.string().email(),
  phone: Joi.string().pattern(/^\+?[\d\s-()]{8,}$/),
  url: Joi.string().uri(),
  date: Joi.date(),
  ipAddress: Joi.string().ip(),
  creditCard: Joi.string().creditCard(),
  postalCode: Joi.string().pattern(/^\d{5}(-\d{4})?$/),
  password: Joi.string()
    .min(8)
    .pattern(/^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$/)
};

app.post('/validate-schema', async (req, res) => {
  try {
    const { data, schema, outputFilename } = req.body;
    
    // Convert schema definition to Joi schema
    const joiSchema = Joi.object(
      Object.entries(schema).reduce((acc, [key, value]) => {
        if (commonSchemas[value]) {
          acc[key] = commonSchemas[value];
        } else if (typeof value === 'object') {
          acc[key] = Joi.object(value);
        } else {
          acc[key] = Joi[value]();
        }
        return acc;
      }, {})
    );

    const result = joiSchema.validate(data, { abortEarly: false });
    const validation = {
      isValid: !result.error,
      errors: result.error ? result.error.details.map(err => ({
        field: err.path.join('.'),
        message: err.message
      })) : [],
      value: result.value
    };

    if (outputFilename) {
      const outputPath = join(TEMP_DIR, outputFilename);
      writeFileSync(outputPath, JSON.stringify(validation, null, 2));
      validation.outputPath = outputPath;
    }

    res.json(validation);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/clean-data', async (req, res) => {
  try {
    const { data, rules, outputFilename } = req.body;
    const cleaned = { ...data };

    // Apply cleaning rules
    Object.entries(rules).forEach(([field, rule]) => {
      if (cleaned[field]) {
        switch (rule) {
          case 'trim':
            cleaned[field] = cleaned[field].trim();
            break;
          case 'lowercase':
            cleaned[field] = cleaned[field].toLowerCase();
            break;
          case 'uppercase':
            cleaned[field] = cleaned[field].toUpperCase();
            break;
          case 'number':
            cleaned[field] = Number(cleaned[field]);
            break;
          case 'boolean':
            cleaned[field] = Boolean(cleaned[field]);
            break;
          case 'email':
            cleaned[field] = validator.normalizeEmail(cleaned[field]);
            break;
          case 'phone':
            cleaned[field] = cleaned[field].replace(/[^\d+]/g, '');
            break;
        }
      }
    });

    if (outputFilename) {
      const outputPath = join(TEMP_DIR, outputFilename);
      writeFileSync(outputPath, JSON.stringify(cleaned, null, 2));
      res.json({ path: outputPath, data: cleaned });
    } else {
      res.json({ data: cleaned });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/verify-format', async (req, res) => {
  try {
    const { data, format } = req.body;
    let isValid = false;
    let error = null;

    switch (format) {
      case 'email':
        isValid = validator.isEmail(data);
        break;
      case 'url':
        isValid = validator.isURL(data);
        break;
      case 'date':
        isValid = validator.isDate(data);
        break;
      case 'creditCard':
        isValid = validator.isCreditCard(data);
        break;
      case 'json':
        try {
          JSON.parse(data);
          isValid = true;
        } catch (e) {
          error = 'Invalid JSON format';
        }
        break;
      case 'base64':
        isValid = validator.isBase64(data);
        break;
      case 'ipAddress':
        isValid = validator.isIP(data);
        break;
      case 'macAddress':
        isValid = validator.isMACAddress(data);
        break;
      case 'uuid':
        isValid = validator.isUUID(data);
        break;
      default:
        error = 'Unsupported format';
    }

    res.json({
      isValid,
      format,
      error
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/batch-validate', async (req, res) => {
  try {
    const { items, schema, outputFilename } = req.body;
    
    const joiSchema = Joi.object(
      Object.entries(schema).reduce((acc, [key, value]) => {
        if (commonSchemas[value]) {
          acc[key] = commonSchemas[value];
        } else if (typeof value === 'object') {
          acc[key] = Joi.object(value);
        } else {
          acc[key] = Joi[value]();
        }
        return acc;
      }, {})
    );

    const results = items.map((item, index) => {
      const result = joiSchema.validate(item, { abortEarly: false });
      return {
        index,
        isValid: !result.error,
        errors: result.error ? result.error.details.map(err => ({
          field: err.path.join('.'),
          message: err.message
        })) : [],
        value: result.value
      };
    });

    const summary = {
      total: items.length,
      valid: results.filter(r => r.isValid).length,
      invalid: results.filter(r => !r.isValid).length,
      results
    };

    if (outputFilename) {
      const outputPath = join(TEMP_DIR, outputFilename);
      writeFileSync(outputPath, JSON.stringify(summary, null, 2));
      summary.outputPath = outputPath;
    }

    res.json(summary);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  try {
    // Check if temp directory is accessible
    if (!existsSync(TEMP_DIR)) {
      throw new Error('Temporary directory is not accessible');
    }
    res.json({ 
      status: 'healthy',
      tempDir: TEMP_DIR,
      message: 'Data validation server is ready'
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'error',
      message: 'Data validation server is not healthy',
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`Data validation server running on port ${PORT}`);
}); 