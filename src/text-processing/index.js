const express = require('express');
const marked = require('marked');
const TurndownService = require('turndown');
const readability = require('text-readability');
const { franc } = require('franc');
const { htmlToText } = require('html-to-text');
const { gfmHeadingId } = require('marked-gfm-heading-id');
const { mangle } = require('marked-mangle');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3005;
const TEMP_DIR = process.env.TEXT_PROCESSING_TEMP_DIR;

// Ensure temp directory exists
if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true });
}

// Configure marked with GFM and other extensions
marked.use(gfmHeadingId());
marked.use(mangle());
const turndownService = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced'
});

// Helper function for text analysis
function analyzeText(text) {
  return {
    wordCount: text.trim().split(/\s+/).length,
    characterCount: text.length,
    lineCount: text.split('\n').length,
    readingTime: Math.ceil(text.trim().split(/\s+/).length / 200), // Assuming 200 WPM
    readabilityScores: {
      fleschReadingEase: readability.fleschReadingEase(text),
      fleschKincaidGrade: readability.fleschKincaidGrade(text),
      colemanLiauIndex: readability.colemanLiauIndex(text),
      automatedReadabilityIndex: readability.automatedReadabilityIndex(text),
      daleChallReadabilityScore: readability.daleChallReadabilityScore(text)
    },
    detectedLanguage: franc(text)
  };
}

app.post('/analyze', async (req, res) => {
  try {
    const { text, outputFilename } = req.body;
    const analysis = analyzeText(text);
    
    if (outputFilename) {
      const outputPath = path.join(TEMP_DIR, outputFilename);
      fs.writeFileSync(outputPath, JSON.stringify(analysis, null, 2));
      analysis.outputPath = outputPath;
    }
    
    res.json(analysis);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/convert', async (req, res) => {
  try {
    const { text, fromFormat, toFormat, outputFilename } = req.body;
    let converted;
    
    // Convert between formats
    switch (`${fromFormat}-${toFormat}`) {
      case 'markdown-html':
        converted = marked.parse(text);
        break;
      case 'html-markdown':
        converted = turndownService.turndown(text);
        break;
      case 'html-text':
        converted = htmlToText(text, {
          wordwrap: 130,
          preserveNewlines: true
        });
        break;
      case 'markdown-text':
        converted = htmlToText(marked.parse(text), {
          wordwrap: 130,
          preserveNewlines: true
        });
        break;
      default:
        throw new Error('Unsupported conversion format');
    }
    
    const outputPath = path.join(TEMP_DIR, outputFilename);
    fs.writeFileSync(outputPath, converted);
    
    res.json({
      path: outputPath,
      preview: converted.substring(0, 200) + (converted.length > 200 ? '...' : '')
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/extract-text', async (req, res) => {
  try {
    const { inputPath, outputFilename } = req.body;
    const fileContent = fs.readFileSync(inputPath, 'utf8');
    const outputPath = path.join(TEMP_DIR, outputFilename);
    
    // Extract text based on file type
    const fileExt = path.extname(inputPath).toLowerCase();
    let extractedText;
    
    switch (fileExt) {
      case '.html':
      case '.htm':
        extractedText = htmlToText(fileContent, {
          wordwrap: 130,
          preserveNewlines: true
        });
        break;
      case '.md':
        extractedText = htmlToText(marked.parse(fileContent), {
          wordwrap: 130,
          preserveNewlines: true
        });
        break;
      case '.txt':
        extractedText = fileContent;
        break;
      default:
        throw new Error('Unsupported file format for text extraction');
    }
    
    fs.writeFileSync(outputPath, extractedText);
    
    res.json({
      path: outputPath,
      analysis: analyzeText(extractedText),
      preview: extractedText.substring(0, 200) + (extractedText.length > 200 ? '...' : '')
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/summarize', async (req, res) => {
  try {
    const { text, maxSentences = 3, outputFilename } = req.body;
    
    // Simple extractive summarization
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [];
    const wordFreq = {};
    
    // Calculate word frequencies
    sentences.forEach(sentence => {
      const words = sentence.toLowerCase().match(/\b\w+\b/g) || [];
      words.forEach(word => {
        wordFreq[word] = (wordFreq[word] || 0) + 1;
      });
    });
    
    // Score sentences based on word frequency
    const sentenceScores = sentences.map(sentence => {
      const words = sentence.toLowerCase().match(/\b\w+\b/g) || [];
      const score = words.reduce((sum, word) => sum + (wordFreq[word] || 0), 0);
      return { sentence, score: score / words.length };
    });
    
    // Get top sentences
    const summary = sentenceScores
      .sort((a, b) => b.score - a.score)
      .slice(0, maxSentences)
      .sort((a, b) => sentences.indexOf(a.sentence) - sentences.indexOf(b.sentence))
      .map(item => item.sentence)
      .join(' ');
    
    if (outputFilename) {
      const outputPath = path.join(TEMP_DIR, outputFilename);
      fs.writeFileSync(outputPath, summary);
      res.json({
        path: outputPath,
        summary,
        originalLength: text.length,
        summaryLength: summary.length,
        compressionRatio: (summary.length / text.length * 100).toFixed(1) + '%'
      });
    } else {
      res.json({
        summary,
        originalLength: text.length,
        summaryLength: summary.length,
        compressionRatio: (summary.length / text.length * 100).toFixed(1) + '%'
      });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Text Processing server running on port ${PORT}`);
}); 