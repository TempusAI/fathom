'use client'

import ChatInput from './ChatInput'
import MessageArea from './MessageArea'
import { usePlaygroundStore } from '@/store'
import Icon from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { useEffect, useState } from 'react'
import { TaskPanel } from '../TaskPanel'
const ChatArea = () => {
  const { isTaskTrayOpen, setIsTaskTrayOpen } = usePlaygroundStore()
  const messages = usePlaygroundStore((s) => s.messages)
  const isTaskPanelVisible = usePlaygroundStore((s) => s.isTaskPanelVisible)
  const tokenCount = usePlaygroundStore((s) => s.tokenCount)
  // Close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsTaskTrayOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [setIsTaskTrayOpen])
  const hideHeaderButton = messages.length === 0 && isTaskPanelVisible
  return (
    <main className="relative m-1.5 flex flex-grow flex-col rounded-xl bg-background max-w-none">
      {/* Header actions */}
      {!hideHeaderButton && (
        <div className="sticky top-0 z-20 mx-auto w-full max-w-5xl px-4 pt-6 md:pt-8">
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => setIsTaskTrayOpen(!isTaskTrayOpen)}
              className={cn(
                'inline-flex items-center gap-2 rounded-md border px-4 py-1.5 text-sm',
                'border-white/10 bg-white/5 hover:bg-white/10 transition-colors backdrop-blur-sm'
              )}
              aria-pressed={isTaskTrayOpen}
            >
              <Icon type="workflow" size="xs" />
              <span>Workflow Tasks</span>
            </button>
          </div>
        </div>
      )}

      {/* Centered tray overlay with backdrop blur (does not shift layout) */}
      {isTaskTrayOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-background/40 backdrop-blur-sm" />
          <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-20 md:pt-34">
            <div
              className={cn(
                'w-full max-w-5xl rounded-xl bg-card shadow-sm overflow-hidden',
                'animate-in fade-in zoom-in-95 duration-150'
              )}
              style={{ height: 400 }}
              role="dialog"
              aria-modal="true"
            >
              <div className="flex items-center justify-between px-3 py-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Icon type="workflow" size="xs" />
                  <span>Workflow Tasks</span>
                </div>
                <button
                  type="button"
                  className="rounded-md px-2 py-1 text-xs hover:bg-accent"
                  onClick={() => setIsTaskTrayOpen(false)}
                >
                  Minimise
                </button>
              </div>
              <div className="h-[calc(360px-10px)] overflow-auto p-2">
                <TaskPanel showHeader={false} visibleOverride className="h-full" />
              </div>
            </div>
          </div>
        </>
      )}

      {/* Base content remains rendered; overlay sits on top to avoid layout jump */}
      <MessageArea />
      <ToolContextViewer />
      {typeof tokenCount === 'number' && (
        <div className="pointer-events-none fixed bottom-3 right-4 z-30 rounded-md bg-white/5 px-2.5 py-1.5 text-xs text-white/80 shadow-sm backdrop-blur-sm">
          <span className="opacity-70">Tokens:</span> <span className="font-mono">{tokenCount.toLocaleString()}</span>
        </div>
      )}
      <div className="sticky bottom-0 ml-9 px-4 pb-2">
        <ChatInput />
      </div>
    </main>
  )
}

export default ChatArea

function ToolContextViewer() {
  const [open, setOpen] = useState(false)
  const messages = usePlaygroundStore((s) => s.messages)
  const compactBlocks = usePlaygroundStore((s) => s.compactToolContexts).map((text, i) => ({ idx: i, text }))

  return (
    <>
      <button
        type="button"
        aria-label="View compact tool context"
        title="View compact tool context"
        onClick={() => setOpen(true)}
        className="fixed bottom-12 right-4 z-30 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-white/10 text-white/80 shadow-sm backdrop-blur-md hover:bg-white/15"
      >
        <Icon type="references" size="sm" />
      </button>
      {open && (
        <div className="fixed inset-0 z-40">
          <div className="absolute inset-0 bg-background/40 backdrop-blur-sm" onClick={() => setOpen(false)} />
          <div className="absolute inset-0 z-50 flex items-start justify-center p-4 pt-16">
            <div className="w-full max-w-3xl rounded-xl bg-card shadow-sm overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                <div className="text-sm font-medium">Tool Context Sent To Model</div>
                <button className="rounded-md px-2 py-1 text-xs hover:bg-accent" onClick={() => setOpen(false)}>Close</button>
              </div>
              <div className="max-h-[70vh] overflow-auto p-4 font-mono text-xs leading-5 whitespace-pre-wrap">
                {compactBlocks.length === 0 ? (
                  <div className="opacity-70">No compacted tool context yet.</div>
                ) : (
                  compactBlocks.map((b) => (
                    <div key={b.idx} className="mb-4">
                      <div className="mb-2 rounded bg-white/5 px-2 py-1 text-[10px] uppercase tracking-wide text-white/70">Tool Call</div>
                      <pre className="whitespace-pre-wrap">{b.text}</pre>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
