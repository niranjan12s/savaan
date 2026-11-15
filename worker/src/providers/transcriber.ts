// Transcriber for Cloudflare: Workers AI Whisper.
// Mirrors providers/transcriber.py (Transcriber.transcribe).

export interface Transcriber {
  transcribe(audio: ArrayBuffer): Promise<string>;
}

export class WorkersAITranscriber implements Transcriber {
  constructor(
    private ai: Ai,
    private model = "@cf/openai/whisper-large-v3-turbo"
  ) {}

  async transcribe(audio: ArrayBuffer): Promise<string> {
    const result = (await this.ai.run(this.model, {
      audio: [...new Uint8Array(audio)],
    })) as { text?: string };
    return (result.text ?? "").trim();
  }
}
