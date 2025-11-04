import { config } from 'dotenv';
import { dirname, resolve, join } from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import ffmpeg from 'fluent-ffmpeg';
import { existsSync, mkdirSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(__dirname, '../../.env') });

const app = express();
app.use(express.json());

const PORT = process.env.PORT_AUDIO || 3007;
const TEMP_DIR = process.env.AUDIO_PROCESSING_TEMP_DIR || join(__dirname, 'temp');

// Ensure temp directory exists
if (!existsSync(TEMP_DIR)) {
  mkdirSync(TEMP_DIR, { recursive: true });
}

// Helper function to get audio metadata
function getAudioMetadata(inputPath) {
  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(inputPath, (err, metadata) => {
      if (err) reject(err);
      else resolve(metadata);
    });
  });
}

app.post('/convert', async (req, res) => {
  try {
    const { inputPath, outputFormat, outputFilename, options = {} } = req.body;
    const outputPath = join(TEMP_DIR, outputFilename);

    const command = ffmpeg(inputPath);
    
    // Apply audio options
    if (options.bitrate) command.audioBitrate(options.bitrate);
    if (options.channels) command.audioChannels(options.channels);
    if (options.frequency) command.audioFrequency(options.frequency);
    if (options.quality) command.audioQuality(options.quality);

    await new Promise((resolve, reject) => {
      command
        .toFormat(outputFormat)
        .on('end', resolve)
        .on('error', reject)
        .save(outputPath);
    });

    res.json({ path: outputPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/trim', async (req, res) => {
  try {
    const { inputPath, outputFilename, startTime, duration } = req.body;
    const outputPath = join(TEMP_DIR, outputFilename);

    await new Promise((resolve, reject) => {
      ffmpeg(inputPath)
        .setStartTime(startTime)
        .setDuration(duration)
        .on('end', resolve)
        .on('error', reject)
        .save(outputPath);
    });

    res.json({ path: outputPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/apply-effect', async (req, res) => {
  try {
    const { inputPath, outputFilename, effect, options = {} } = req.body;
    const outputPath = join(TEMP_DIR, outputFilename);

    const command = ffmpeg(inputPath);

    // Apply audio effects
    switch (effect) {
      case 'fade':
        if (options.fadeIn) command.audioFilters(`afade=t=in:st=0:d=${options.fadeIn}`);
        if (options.fadeOut) {
          const metadata = await getAudioMetadata(inputPath);
          const duration = metadata.format.duration;
          command.audioFilters(`afade=t=out:st=${duration - options.fadeOut}:d=${options.fadeOut}`);
        }
        break;
      case 'volume':
        command.audioFilters(`volume=${options.level}`);
        break;
      case 'bass':
        command.audioFilters(`bass=g=${options.gain}`);
        break;
      case 'treble':
        command.audioFilters(`treble=g=${options.gain}`);
        break;
      case 'normalize':
        command.audioFilters('loudnorm');
        break;
      default:
        throw new Error('Unsupported effect');
    }

    await new Promise((resolve, reject) => {
      command
        .on('end', resolve)
        .on('error', reject)
        .save(outputPath);
    });

    res.json({ path: outputPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/get-metadata', async (req, res) => {
  try {
    const { inputPath } = req.body;
    const metadata = await getAudioMetadata(inputPath);
    
    const audioStream = metadata.streams.find(stream => stream.codec_type === 'audio');
    
    res.json({
      format: metadata.format.format_name,
      duration: metadata.format.duration,
      size: metadata.format.size,
      bitrate: metadata.format.bit_rate,
      audio: audioStream ? {
        codec: audioStream.codec_name,
        channels: audioStream.channels,
        sampleRate: audioStream.sample_rate,
        bitrate: audioStream.bit_rate
      } : null
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/merge', async (req, res) => {
  try {
    const { inputPaths, outputFilename } = req.body;
    const outputPath = join(TEMP_DIR, outputFilename);

    const command = ffmpeg();
    
    // Add input files
    inputPaths.forEach(inputPath => {
      command.input(inputPath);
    });

    await new Promise((resolve, reject) => {
      command
        .mergeToFile(outputPath, TEMP_DIR)
        .on('end', resolve)
        .on('error', reject);
    });

    res.json({ path: outputPath });
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
      message: 'Audio processing server is ready'
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'error',
      message: 'Audio processing server is not healthy',
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`Audio processing server running on port ${PORT}`);
}); 