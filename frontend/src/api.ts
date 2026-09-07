// API configuration — empty string = same origin, proxied to backend by Vite in dev
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

export interface GenerateImageResult {
  blob: Blob;
  objectUrl: string;
}

export interface GenerateVideoResult {
  blob: Blob;
  objectUrl: string;
}

export async function generateImage(prompt: string): Promise<GenerateImageResult> {
  const response = await fetch(`${API_BASE}/api/content/text-to-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: prompt }),
  });

  if (!response.ok) {
    let errorMsg = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) errorMsg = data.detail;
    } catch {
      // ignore parse error
    }
    throw new Error(errorMsg);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  return { blob, objectUrl };
}

export async function generateVideo(prompt: string): Promise<GenerateVideoResult> {
  const response = await fetch(`${API_BASE}/api/content/text-to-video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: prompt }),
  });

  if (!response.ok) {
    let errorMsg = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) errorMsg = data.detail;
    } catch {
      // ignore parse error
    }
    throw new Error(errorMsg);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  return { blob, objectUrl };
}
