import { useEffect, useRef, useState } from 'react'
import type { EnglishRecognizer, EnglishRecognizerCtor } from '../types/speech'

const PAUSE_MS = 10000

function englishRecognizer(): EnglishRecognizerCtor | null {
  const root = window as Window & {
    SpeechRecognition?: EnglishRecognizerCtor
    webkitSpeechRecognition?: EnglishRecognizerCtor
  }
  return root.SpeechRecognition ?? root.webkitSpeechRecognition ?? null
}

/**
 * Voice input component
 *
 * @description Opens the microphone, listens in English, and returns the transcript after a short pause
 */
export const VoiceInput = ({
  disabled,
  onBegin,
  onPartial,
  onTranscript,
}: {
  disabled: boolean
  onBegin: () => void
  onPartial: (text: string) => void
  onTranscript: (text: string) => void
}) => {
  const [listening, setListening] = useState(false)
  const [unsupported, setUnsupported] = useState(false)
  const recognitionRef = useRef<EnglishRecognizer | null>(null)
  const pauseRef = useRef<number | null>(null)
  const transcriptRef = useRef('')
  const onBeginRef = useRef(onBegin)
  const onPartialRef = useRef(onPartial)
  const onTranscriptRef = useRef(onTranscript)
  const aliveRef = useRef(true)
  onBeginRef.current = onBegin
  onPartialRef.current = onPartial
  onTranscriptRef.current = onTranscript

  useEffect(() => {
    aliveRef.current = true
    setUnsupported(englishRecognizer() === null)
    return () => {
      aliveRef.current = false
      if (pauseRef.current !== null) window.clearTimeout(pauseRef.current)
      recognitionRef.current?.abort()
    }
  }, [])

  useEffect(() => {
    if (!disabled) return
    if (pauseRef.current !== null) window.clearTimeout(pauseRef.current)
    recognitionRef.current?.stop()
  }, [disabled])

  const start = () => {
    const Ctor = englishRecognizer()
    if (!Ctor) return
    const recognition = new Ctor()
    recognition.lang = 'en-US'
    recognition.interimResults = true
    recognition.continuous = true
    transcriptRef.current = ''
    onBeginRef.current()
    recognition.onresult = (event) => {
      transcriptRef.current = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? '')
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim()
      if (aliveRef.current) onPartialRef.current(transcriptRef.current)
      if (pauseRef.current !== null) window.clearTimeout(pauseRef.current)
      pauseRef.current = window.setTimeout(() => recognition.stop(), PAUSE_MS)
    }
    recognition.onerror = () => {
      recognition.stop()
    }
    recognition.onend = () => {
      if (pauseRef.current !== null) window.clearTimeout(pauseRef.current)
      pauseRef.current = null
      setListening(false)
      recognitionRef.current = null
      const spoken = transcriptRef.current.trim()
      transcriptRef.current = ''
      if (aliveRef.current) onTranscriptRef.current(spoken)
    }
    recognitionRef.current = recognition
    setListening(true)
    recognition.start()
  }

  const stop = () => {
    if (pauseRef.current !== null) window.clearTimeout(pauseRef.current)
    recognitionRef.current?.stop()
  }

  return (
    <button
      type="button"
      onClick={() => (listening ? stop() : start())}
      disabled={disabled || unsupported}
      title={unsupported ? 'Voice input is not available in this browser' : 'Speak in English'}
      className={`rounded-xl border px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-white ${
        listening
          ? 'border-rose-300 bg-rose-50 text-rose-700'
          : 'border-slate-300 bg-white text-slate-700 hover:border-sky-300'
      }`}
    >
      {listening ? 'Listening…' : 'Mic'}
    </button>
  )
}
