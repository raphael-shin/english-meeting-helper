export interface AudioCaptureOptions {
  sampleRate: number;
  chunkIntervalMs: number;
}

const AUDIO_BUFFER_SIZES = [256, 512, 1024, 2048, 4096, 8192, 16384];

export class AudioCapture {
  private stream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private onAudioChunk: ((chunk: ArrayBuffer) => void) | null = null;

  async start(
    options: AudioCaptureOptions,
    onChunk: (chunk: ArrayBuffer) => void
  ): Promise<void> {
    this.onAudioChunk = onChunk;

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: options.sampleRate,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    this.audioContext = new AudioContext({ sampleRate: options.sampleRate });
    const source = this.audioContext.createMediaStreamSource(this.stream);
    const targetBufferSize = Math.floor(
      (options.sampleRate * options.chunkIntervalMs) / 1000
    );
    const bufferSize = this.resolveBufferSize(targetBufferSize);
    this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

    this.processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      const pcmData = this.float32ToPcm16(inputData);
      this.onAudioChunk?.(pcmData.buffer);
    };

    source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
  }

  stop(): void {
    this.processor?.disconnect();
    this.audioContext?.close();
    this.stream?.getTracks().forEach((track) => track.stop());
    this.processor = null;
    this.audioContext = null;
    this.stream = null;
    this.onAudioChunk = null;
  }

  private float32ToPcm16(float32Array: Float32Array): Int16Array {
    const pcm16 = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const sample = Math.max(-1, Math.min(1, float32Array[i]));
      pcm16[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }
    return pcm16;
  }

  private resolveBufferSize(targetSize: number): number {
    if (targetSize <= 0) {
      return 0;
    }
    let closest = AUDIO_BUFFER_SIZES[0];
    for (const size of AUDIO_BUFFER_SIZES) {
      if (Math.abs(size - targetSize) < Math.abs(closest - targetSize)) {
        closest = size;
      }
    }
    return closest;
  }
}
