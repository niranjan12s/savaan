// Transcriber for Cloudflare: Workers AI Whisper.
// Mirrors providers/transcriber.py (Transcriber.transcribe).

export interface Transcriber {
  transcribe(audio: ArrayBuffer): Promise<string>;
}

function toBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

export class WorkersAITranscriber implements Transcriber {
  constructor(
    private ai: Ai,
    private model = "@cf/openai/whisper-large-v3-turbo"
  ) {}

  async transcribe(audio: ArrayBuffer): Promise<string> {
    const result = (await this.ai.run(this.model, {
      audio: toBase64(audio),
    })) as { text?: string };
    return (result.text ?? "").trim();
  }
}
