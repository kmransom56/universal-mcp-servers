import { config } from 'dotenv';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import OpenAI from 'openai';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, '../../.env') });

const app = express();
app.use(express.json());

const PORT = process.env.PORT_OPENAI || 3014;

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

app.post('/chat/completions', async (req, res) => {
  try {
    const {
      model = 'gpt-3.5-turbo',
      messages,
      temperature = 0.7,
      max_tokens,
      top_p = 1,
      frequency_penalty = 0,
      presence_penalty = 0,
      stop,
      n = 1,
      stream = false,
      logit_bias,
      user
    } = req.body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      throw new Error('Messages array is required and must not be empty');
    }

    const response = await openai.chat.completions.create({
      model,
      messages,
      temperature,
      max_tokens,
      top_p,
      frequency_penalty,
      presence_penalty,
      stop,
      n,
      stream,
      logit_bias,
      user
    });

    res.json(response);
  } catch (error) {
    console.error('Error in chat completion:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/completions', async (req, res) => {
  try {
    const {
      model = 'text-davinci-003',
      prompt,
      suffix,
      max_tokens = 16,
      temperature = 0.7,
      top_p = 1,
      n = 1,
      stream = false,
      logprobs,
      echo = false,
      stop,
      presence_penalty = 0,
      frequency_penalty = 0,
      best_of = 1,
      logit_bias,
      user
    } = req.body;

    if (!prompt) {
      throw new Error('Prompt is required');
    }

    const response = await openai.completions.create({
      model,
      prompt,
      suffix,
      max_tokens,
      temperature,
      top_p,
      n,
      stream,
      logprobs,
      echo,
      stop,
      presence_penalty,
      frequency_penalty,
      best_of,
      logit_bias,
      user
    });

    res.json(response);
  } catch (error) {
    console.error('Error in completion:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/embeddings', async (req, res) => {
  try {
    const {
      model = 'text-embedding-ada-002',
      input,
      user
    } = req.body;

    if (!input) {
      throw new Error('Input is required');
    }

    const response = await openai.embeddings.create({
      model,
      input,
      user
    });

    res.json(response);
  } catch (error) {
    console.error('Error in embeddings:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/images/generations', async (req, res) => {
  try {
    const {
      prompt,
      n = 1,
      size = '1024x1024',
      quality = 'standard',
      style = 'vivid'
    } = req.body;

    const image = await openai.images.generate({
      prompt,
      n,
      size,
      quality,
      style
    });

    res.json(image);
  } catch (error) {
    console.error('Error in image generation:', error.message);
    res.status(500).json({ error: error.message });
  }
});

app.post('/audio/transcriptions', async (req, res) => {
  try {
    const {
      file,
      model = 'whisper-1',
      language,
      prompt,
      response_format = 'json',
      temperature
    } = req.body;

    const transcription = await openai.audio.transcriptions.create({
      file,
      model,
      language,
      prompt,
      response_format,
      temperature
    });

    res.json(transcription);
  } catch (error) {
    console.error('Error in audio transcription:', error.message);
    res.status(500).json({ error: error.message });
  }
});

app.post('/moderations', async (req, res) => {
  try {
    const { input, model = 'text-moderation-latest' } = req.body;

    const moderation = await openai.moderations.create({
      input,
      model
    });

    res.json(moderation);
  } catch (error) {
    console.error('Error in moderation:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  try {
    if (!process.env.OPENAI_API_KEY) {
      throw new Error('OPENAI_API_KEY is not set');
    }
    res.json({
      status: 'healthy',
      message: 'OpenAI server is ready'
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'OpenAI server is not healthy',
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`OpenAI server running on port ${PORT}`);
}); 