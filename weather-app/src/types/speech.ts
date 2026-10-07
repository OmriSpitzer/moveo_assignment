export type SpeechResult = {
  readonly 0?: { transcript: string }
}

export type SpeechResultEvent = {
  readonly results: ArrayLike<SpeechResult>
}

export type EnglishRecognizer = {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((event: SpeechResultEvent) => void) | null
  onend: (() => void) | null
  onerror: (() => void) | null
  start: () => void
  stop: () => void
  abort: () => void
}

export type EnglishRecognizerCtor = new () => EnglishRecognizer
