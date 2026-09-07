export type MediaType = 'image' | 'video';

export interface HistoryItem {
  id: string;
  type: MediaType;
  prompt: string;
  objectUrl: string;
  createdAt: number;
}

export type GenerationStatus = 'idle' | 'loading' | 'success' | 'error';
