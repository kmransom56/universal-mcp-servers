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

const PORT = process.env.PORT_VIDEO || 3006;
const TEMP_DIR = process.env.VIDEO_PROCESSING_TEMP_DIR || join(__dirname, 'temp');

// Ensure temp directory exists
if (!existsSync(TEMP_DIR)) {
  mkdirSync(TEMP_DIR, { recursive: true });
}

// Helper function to get video metadata
function getVideoMetadata(inputPath) {
  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(inputPath, (err, metadata) => {
      if (err) reject(err);
      else resolve(metadata);
    });
  });
}

app.post('/transcode', async (req, res) => {
  try {
    const { inputPath, outputFormat, outputFilename, options = {} } = req.body;
    const outputPath = join(TEMP_DIR, outputFilename);

    const command = ffmpeg(inputPath);
    
    // Apply video options
    if (options.videoBitrate) command.videoBitrate(options.videoBitrate);
    if (options.fps) command.fps(options.fps);
    if (options.size) command.size(options.size);
    
    // Apply audio options
    if (options.audioBitrate) command.audioBitrate(options.audioBitrate);
    if (options.audioChannels) command.audioChannels(options.audioChannels);
    if (options.audioFrequency) command.audioFrequency(options.audioFrequency);

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

app.post('/generate-thumbnail', async (req, res) => {
  try {
    const { inputPath, outputFilename, timestamp = '00:00:01', size = '320x240' } = req.body;
    const outputPath = join(TEMP_DIR, outputFilename);

    await new Promise((resolve, reject) => {
      ffmpeg(inputPath)
        .screenshots({
          timestamps: [timestamp],
          filename: outputFilename,
          folder: TEMP_DIR,
          size: size
        })
        .on('end', resolve)
        .on('error', reject);
    });

    res.json({ path: outputPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/extract-clip', async (req, res) => {
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

app.post('/get-metadata', async (req, res) => {
  try {
    const { inputPath } = req.body;
    const metadata = await getVideoMetadata(inputPath);
    
    res.json({
      format: metadata.format,
      duration: metadata.format.duration,
      size: metadata.format.size,
      bitrate: metadata.format.bit_rate,
      streams: metadata.streams.map(stream => ({
        codec_type: stream.codec_type,
        codec_name: stream.codec_name,
        width: stream.width,
        height: stream.height,
        fps: stream.r_frame_rate,
        bitrate: stream.bit_rate
      }))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/compress', async (req, res) => {
  try {
    const { inputPath, outputFilename, quality = 'medium' } = req.body;
    const outputPath = join(TEMP_DIR, outputFilename);

    const presets = {
      low: { videoBitrate: '500k', audioBitrate: '64k' },
      medium: { videoBitrate: '1000k', audioBitrate: '128k' },
      high: { videoBitrate: '2000k', audioBitrate: '192k' }
    };

    const preset = presets[quality] || presets.medium;

    await new Promise((resolve, reject) => {
      ffmpeg(inputPath)
        .videoBitrate(preset.videoBitrate)
        .audioBitrate(preset.audioBitrate)
        .on('end', resolve)
        .on('error', reject)
        .save(outputPath);
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
      message: 'Video processing server is ready'
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'error',
      message: 'Video processing server is not healthy',
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`Video processing server running on port ${PORT}`);
}); 