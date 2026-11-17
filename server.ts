import 'dotenv/config';
import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT) || 3000;
const DIFY_ENDPOINT = 'https://api.dify.ai/v1/chat-messages';

function extractAnswerJson(rawAnswer: unknown): unknown {
  if (typeof rawAnswer === 'object' && rawAnswer !== null) {
    return rawAnswer;
  }
  if (typeof rawAnswer !== 'string') {
    throw new Error('Dify response "answer" field is missing or not a string.');
  }

  const cleaned = rawAnswer
    .trim()
    .replace(/^```json\s*/i, '')
    .replace(/^```\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim();

  return JSON.parse(cleaned);
}

async function startServer() {
  const app = express();
  app.use(express.json({ limit: '1mb' }));

  app.post('/api/dify', async (req, res) => {
    const { query, conversation_id } = (req.body || {}) as {
      query?: string;
      conversation_id?: string;
    };

    if (!query || typeof query !== 'string') {
      res.status(400).json({ error: 'Missing required "query" string.' });
      return;
    }

    const apiKey = process.env.DIFY_API_KEY?.trim();
    if (!apiKey || apiKey === 'MY_DIFY_API_KEY') {
      res.status(500).json({ error: 'DIFY_API_KEY is not configured on the server.' });
      return;
    }

    try {
      const difyResponse = await fetch(DIFY_ENDPOINT, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          inputs: {},
          query,
          response_mode: 'blocking',
          conversation_id: conversation_id || '',
          user: 'demo-tablet',
        }),
      });

      const rawText = await difyResponse.text();
      let parsedBody: Record<string, unknown>;

      try {
        parsedBody = JSON.parse(rawText) as Record<string, unknown>;
      } catch {
        res.status(difyResponse.ok ? 502 : difyResponse.status).json({
          error: `Dify API returned non-JSON response (HTTP ${difyResponse.status}).`,
        });
        return;
      }

      if (!difyResponse.ok) {
        const message =
          (typeof parsedBody.message === 'string' && parsedBody.message) ||
          (typeof parsedBody.error === 'string' && parsedBody.error) ||
          `Dify API error (HTTP ${difyResponse.status})`;
        res.status(difyResponse.status).json({ error: message });
        return;
      }

      let data: unknown;
      try {
        data = extractAnswerJson(parsedBody.answer);
      } catch (parseErr) {
        const msg =
          parseErr instanceof Error ? parseErr.message : 'Failed to parse Dify answer JSON.';
        res.status(502).json({ error: `Invalid JSON in Dify answer: ${msg}` });
        return;
      }

      res.json({
        conversation_id: parsedBody.conversation_id || conversation_id || '',
        data,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to connect to Dify API.';
      res.status(502).json({ error: message });
    }
  });

  if (process.env.NODE_ENV !== 'production') {
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distDir = path.resolve(__dirname, 'dist');
    app.use(express.static(distDir));
    app.get('*all', (_req, res) => {
      const indexPath = path.join(distDir, 'index.html');
      if (fs.existsSync(indexPath)) {
        res.sendFile(indexPath);
      } else {
        res.status(404).send('Build output not found. Run npm run build first.');
      }
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`FryWise thin-client server listening on http://0.0.0.0:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error('Failed to start FryWise server:', err);
  process.exit(1);
});
