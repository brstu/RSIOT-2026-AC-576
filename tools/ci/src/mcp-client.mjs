import https from 'node:https';

export async function askMCP({ serverUrl, apiKey, payload }) {
  if (!serverUrl || !apiKey) return { ok: false, reason: 'MCP not configured' };
  const data = JSON.stringify(payload);
  const url = new URL('/v1/analyze', serverUrl);
  const opts = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
      'Content-Length': Buffer.byteLength(data)
    }
  };
  return new Promise((resolve, reject) => {
    const req = https.request(url, opts, (res) => {
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => {
        try {
          const json = JSON.parse(body || '{}');
          resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, data: json, status: res.statusCode });
        } catch (e) {
          resolve({ ok: false, reason: 'Bad JSON from MCP', body });
        }
      });
    });
    req.on('error', (e) => resolve({ ok: false, reason: e.message }));
    req.write(data);
    req.end();
  });
}
