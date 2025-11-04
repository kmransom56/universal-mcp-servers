const express = require('express');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs').promises;
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3013;
const STORAGE_DIR = process.env.SEQUENTIAL_THINKING_STORAGE_DIR || path.join(__dirname, 'storage');

// Ensure storage directory exists
if (!fs.existsSync(STORAGE_DIR)) {
  fs.mkdirSync(STORAGE_DIR, { recursive: true });
}

// In-memory storage for active thought processes
const thoughtProcesses = new Map();

app.post('/start-process', async (req, res) => {
  try {
    const { 
      initialThought,
      context,
      estimatedSteps = 5,
      metadata = {}
    } = req.body;

    const processId = uuidv4();
    const timestamp = new Date().toISOString();

    const process = {
      id: processId,
      status: 'active',
      currentStep: 1,
      estimatedSteps,
      thoughts: [{
        number: 1,
        content: initialThought,
        timestamp,
        type: 'initial'
      }],
      context,
      metadata,
      branches: [],
      createdAt: timestamp,
      updatedAt: timestamp
    };

    thoughtProcesses.set(processId, process);
    await saveProcess(processId, process);

    res.json({
      processId,
      currentStep: 1,
      estimatedSteps,
      thought: {
        content: initialThought,
        timestamp
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/add-thought', async (req, res) => {
  try {
    const {
      processId,
      thought,
      isRevision = false,
      revisesThought = null,
      branchFromThought = null,
      branchId = null,
      needsMoreThoughts = false
    } = req.body;

    const process = thoughtProcesses.get(processId);
    if (!process) {
      throw new Error('Process not found');
    }

    const timestamp = new Date().toISOString();
    const thoughtNumber = process.thoughts.length + 1;

    const newThought = {
      number: thoughtNumber,
      content: thought,
      timestamp,
      type: isRevision ? 'revision' : 'sequential',
      revisesThought,
      branchFromThought,
      branchId
    };

    process.thoughts.push(newThought);
    process.currentStep = thoughtNumber;
    process.updatedAt = timestamp;

    if (needsMoreThoughts) {
      process.estimatedSteps = Math.max(process.estimatedSteps + 3, thoughtNumber + 3);
    }

    if (branchId && branchFromThought) {
      if (!process.branches.find(b => b.id === branchId)) {
        process.branches.push({
          id: branchId,
          fromThought: branchFromThought,
          thoughts: [thoughtNumber]
        });
      } else {
        const branch = process.branches.find(b => b.id === branchId);
        branch.thoughts.push(thoughtNumber);
      }
    }

    await saveProcess(processId, process);
    thoughtProcesses.set(processId, process);

    res.json({
      processId,
      currentStep: thoughtNumber,
      estimatedSteps: process.estimatedSteps,
      thought: newThought,
      needsMoreThoughts
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/complete-process', async (req, res) => {
  try {
    const { 
      processId,
      conclusion,
      success = true
    } = req.body;

    const process = thoughtProcesses.get(processId);
    if (!process) {
      throw new Error('Process not found');
    }

    const timestamp = new Date().toISOString();
    process.status = 'completed';
    process.conclusion = {
      content: conclusion,
      timestamp,
      success
    };
    process.updatedAt = timestamp;

    await saveProcess(processId, process);
    thoughtProcesses.set(processId, process);

    res.json({
      processId,
      status: 'completed',
      totalSteps: process.thoughts.length,
      conclusion: process.conclusion
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/process/:processId', async (req, res) => {
  try {
    const { processId } = req.params;
    let process = thoughtProcesses.get(processId);

    if (!process) {
      process = await loadProcess(processId);
      if (process) {
        thoughtProcesses.set(processId, process);
      } else {
        throw new Error('Process not found');
      }
    }

    res.json(process);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/analyze-process', async (req, res) => {
  try {
    const { processId } = req.body;
    const process = thoughtProcesses.get(processId);
    
    if (!process) {
      throw new Error('Process not found');
    }

    const analysis = {
      totalSteps: process.thoughts.length,
      revisions: process.thoughts.filter(t => t.type === 'revision').length,
      branches: process.branches.length,
      averageTimePerThought: calculateAverageTimePerThought(process.thoughts),
      thoughtTypes: countThoughtTypes(process.thoughts),
      branchAnalysis: analyzeBranches(process),
      timeline: generateTimeline(process)
    };

    res.json(analysis);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Helper functions
async function saveProcess(processId, process) {
  const filePath = path.join(STORAGE_DIR, `${processId}.json`);
  await fs.writeFile(filePath, JSON.stringify(process, null, 2));
}

async function loadProcess(processId) {
  try {
    const filePath = path.join(STORAGE_DIR, `${processId}.json`);
    const data = await fs.readFile(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return null;
  }
}

function calculateAverageTimePerThought(thoughts) {
  if (thoughts.length < 2) return 0;
  
  let totalTime = 0;
  for (let i = 1; i < thoughts.length; i++) {
    const current = new Date(thoughts[i].timestamp);
    const previous = new Date(thoughts[i-1].timestamp);
    totalTime += current - previous;
  }
  
  return totalTime / (thoughts.length - 1);
}

function countThoughtTypes(thoughts) {
  return thoughts.reduce((acc, thought) => {
    acc[thought.type] = (acc[thought.type] || 0) + 1;
    return acc;
  }, {});
}

function analyzeBranches(process) {
  return process.branches.map(branch => ({
    branchId: branch.id,
    thoughtCount: branch.thoughts.length,
    startThought: branch.fromThought,
    thoughts: branch.thoughts
  }));
}

function generateTimeline(process) {
  return process.thoughts.map(thought => ({
    number: thought.number,
    timestamp: thought.timestamp,
    type: thought.type,
    branchId: thought.branchId
  }));
}

app.listen(PORT, () => {
  console.log(`Sequential Thinking server running on port ${PORT}`);
}); 