'use client'
import { useState } from 'react'
import { toast } from 'sonner'
import { TextArea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { usePlaygroundStore } from '@/store'
import useAIChatStreamHandler from '@/hooks/useAIStreamHandler'
import { useQueryState } from 'nuqs'
import { TaskChips } from '../../TaskPanel/TaskChips'
import { useAutoResizeTextarea } from '@/hooks/use-auto-resize-textarea'
import { ArrowRight, ChevronDown, Paperclip, Check, Bot } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { motion, AnimatePresence } from 'framer-motion'

// Model icons for the dropdown
const OPENAI_SVG = (
  <div>
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      preserveAspectRatio="xMidYMid"
      viewBox="0 0 256 260"
      aria-label="OpenAI icon"
      className="dark:hidden block"
    >
      <path d="M239.184 106.203a64.716 64.716 0 0 0-5.576-53.103C219.452 28.459 191 15.784 163.213 21.74A65.586 65.586 0 0 0 52.096 45.22a64.716 64.716 0 0 0-43.23 31.36c-14.31 24.602-11.061 55.634 8.033 76.74a64.665 64.665 0 0 0 5.525 53.102c14.174 24.65 42.644 37.324 70.446 31.36a64.72 64.72 0 0 0 48.754 21.744c28.481.025 53.714-18.361 62.414-45.481a64.767 64.767 0 0 0 43.229-31.36c14.137-24.558 10.875-55.423-8.083-76.483Zm-97.56 136.338a48.397 48.397 0 0 1-31.105-11.255l1.535-.87 51.67-29.825a8.595 8.595 0 0 0 4.247-7.367v-72.85l21.845 12.636c.218.111.37.32.409.563v60.367c-.056 26.818-21.783 48.545-48.601 48.601Zm-104.466-44.61a48.345 48.345 0 0 1-5.781-32.589l1.534.921 51.722 29.826a8.339 8.339 0 0 0 8.441 0l63.181-36.425v25.221a.87.87 0 0 1-.358.665l-52.335 30.184c-23.257 13.398-52.97 5.431-66.404-17.803ZM23.549 85.38a48.499 48.499 0 0 1 25.58-21.333v61.39a8.288 8.288 0 0 0 4.195 7.316l62.874 36.272-21.845 12.636a.819.819 0 0 1-.767 0L41.353 151.53c-23.211-13.454-31.171-43.144-17.804-66.405v.256Zm179.466 41.695-63.08-36.63L161.73 77.86a.819.819 0 0 1 .768 0l52.233 30.184a48.6 48.6 0 0 1-7.316 87.635v-61.391a8.544 8.544 0 0 0-4.4-7.213Zm21.742-32.69-1.535-.922-51.619-30.081a8.39 8.39 0 0 0-8.492 0L99.98 99.808V74.587a.716.716 0 0 1 .307-.665l52.233-30.133a48.652 48.652 0 0 1 72.236 50.391v.205ZM88.061 139.097l-21.845-12.585a.87.87 0 0 1-.41-.614V65.685a48.652 48.652 0 0 1 79.757-37.346l-1.535.87-51.67 29.825a8.595 8.595 0 0 0-4.246 7.367l-.051 72.697Zm11.868-25.58 28.138-16.217 28.188 16.218v32.434l-28.086 16.218-28.188-16.218-.052-32.434Z" />
    </svg>
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      preserveAspectRatio="xMidYMid"
      viewBox="0 0 256 260"
      aria-label="OpenAI icon"
      className="hidden dark:block"
    >
      <path
        fill="#fff"
        d="M239.184 106.203a64.716 64.716 0 0 0-5.576-53.103C219.452 28.459 191 15.784 163.213 21.74A65.586 65.586 0 0 0 52.096 45.22a64.716 64.716 0 0 0-43.23 31.36c-14.31 24.602-11.061 55.634 8.033 76.74a64.665 64.665 0 0 0 5.525 53.102c14.174 24.65 42.644 37.324 70.446 31.36a64.72 64.72 0 0 0 48.754 21.744c28.481.025 53.714-18.361 62.414-45.481a64.767 64.767 0 0 0 43.229-31.36c14.137-24.558 10.875-55.423-8.083-76.483Zm-97.56 136.338a48.397 48.397 0 0 1-31.105-11.255l1.535-.87 51.67-29.825a8.595 8.595 0 0 0 4.247-7.367v-72.85l21.845 12.636c.218.111.37.32.409.563v60.367c-.056 26.818-21.783 48.545-48.601 48.601Zm-104.466-44.61a48.345 48.345 0 0 1-5.781-32.589l1.534.921 51.722 29.826a8.339 8.339 0 0 0 8.441 0l63.181-36.425v25.221a.87.87 0 0 1-.358.665l-52.335 30.184c-23.257 13.398-52.97 5.431-66.404-17.803ZM23.549 85.38a48.499 48.499 0 0 1 25.58-21.333v61.39a8.288 8.288 0 0 0 4.195 7.316l62.874 36.272-21.845 12.636a.819.819 0 0 1-.767 0L41.353 151.53c-23.211-13.454-31.171-43.144-17.804-66.405v.256Zm179.466 41.695-63.08-36.63L161.73 77.86a.819.819 0 0 1 .768 0l52.233 30.184a48.6 48.6 0 0 1-7.316 87.635v-61.391a8.544 8.544 0 0 0-4.4-7.213Zm21.742-32.69-1.535-.922-51.619-30.081a8.39 8.39 0 0 0-8.492 0L99.98 99.808V74.587a.716.716 0 0 1 .307-.665l52.233-30.133a48.652 48.652 0 0 1 72.236 50.391v.205ZM88.061 139.097l-21.845-12.585a.87.87 0 0 1-.41-.614V65.685a48.652 48.652 0 0 1 79.757-37.346l-1.535.87-51.67 29.825a8.595 8.595 0 0 0-4.246 7.367l-.051 72.697Zm11.868-25.58 28.138-16.217 28.188 16.218v32.434l-28.086 16.218-28.188-16.218-.052-32.434Z"
      />
    </svg>
  </div>
)

const CLAUDE_SVG = (
  <div>
    <svg
      fill="#000"
      fillRule="evenodd"
      style={{ flex: "none", lineHeight: "1" }}
      viewBox="0 0 24 24"
      width="16"
      height="16"
      xmlns="http://www.w3.org/2000/svg"
      className="dark:hidden block"
    >
      <path d="M13.827 3.52h3.603L24 20h-3.603l-6.57-16.48zm-7.258 0h3.767L16.906 20h-3.674l-1.343-3.461H5.017l-1.344 3.46H0L6.57 3.522zm4.132 9.959L8.453 7.687 6.205 13.48H10.7z" />
    </svg>
    <svg
      fill="#fff"
      fillRule="evenodd"
      style={{ flex: "none", lineHeight: "1" }}
      viewBox="0 0 24 24"
      width="16"
      height="16"
      xmlns="http://www.w3.org/2000/svg"
      className="hidden dark:block"
    >
      <path d="M13.827 3.52h3.603L24 20h-3.603l-6.57-16.48zm-7.258 0h3.767L16.906 20h-3.674l-1.343-3.461H5.017l-1.344 3.46H0L6.57 3.522zm4.132 9.959L8.453 7.687 6.205 13.48H10.7z" />
    </svg>
  </div>
)

const ChatInput = () => {
  const { setTaskPanelVisible, selectedModel, agents, teams, mode, setIsTaskTrayOpen } = usePlaygroundStore()
  const { handleStreamResponse } = useAIChatStreamHandler()
  const [selectedAgent] = useQueryState('agent')
  const [teamId] = useQueryState('team')
  const [inputMessage, setInputMessage] = useState('')
  const isStreaming = usePlaygroundStore((state) => state.isStreaming)
  
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 72,
    maxHeight: 300,
  })

  // Get current model display name
  const getCurrentModel = () => {
    if (mode === 'agent' && selectedAgent) {
      const agent = agents.find(a => a.value === selectedAgent)
      return agent?.model.provider || 'Unknown Model'
    }
    if (mode === 'team' && teamId) {
      const team = teams.find(t => t.value === teamId)
      return team?.model.provider || 'Unknown Model'
    }
    return 'No Model Selected'
  }

  // Model icons mapping
  const MODEL_ICONS: Record<string, React.ReactNode> = {
    'gpt-4o': OPENAI_SVG,
    'gpt-4o-mini': OPENAI_SVG,
    'gpt-4': OPENAI_SVG,
    'claude-3-5-sonnet': CLAUDE_SVG,
    'claude-3-haiku': CLAUDE_SVG,
    'claude-3-opus': CLAUDE_SVG,
  }

  const getModelIcon = (modelName: string) => {
    const lowerModel = modelName.toLowerCase()
    for (const [key, icon] of Object.entries(MODEL_ICONS)) {
      if (lowerModel.includes(key.replace(/-/g, '')) || lowerModel.includes(key)) {
        return icon
      }
    }
    return <Bot className="w-4 h-4 opacity-50" />
  }

  const handleSubmit = async () => {
    if (!inputMessage.trim()) return

    const currentMessage = inputMessage
    setInputMessage('')
    adjustHeight(true)
    
    // Hide task panel when user starts chatting
    setTaskPanelVisible(false)

    try {
      // Auto-minimise tray when sending
      setIsTaskTrayOpen(false)
      await handleStreamResponse(currentMessage)
    } catch (error) {
      toast.error(
        `Error in handleSubmit: ${
          error instanceof Error ? error.message : String(error)
        }`
      )
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isStreaming) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const isDisabled = !(selectedAgent || teamId) || isStreaming
  const currentModel = getCurrentModel()

  return (
    <div className="w-full max-w-4xl mx-auto py-4">
      <div className="bg-zinc-800 rounded-2xl p-1.5 pt-4">
        {/* Task Chips Area */}
        <div className="px-2 pb-2">
          <TaskChips />
        </div>
        
        <div className="relative">
          <div className="relative flex flex-col bg-zinc-900 rounded-xl">
            <div
              className="overflow-y-auto"
              style={{ maxHeight: "400px" }}
            >
              <TextArea
                value={inputMessage}
                placeholder="What can I do for you?"
                className={cn(
                  "w-full rounded-none px-4 py-3 bg-transparent border-none text-foreground placeholder:text-muted-foreground resize-none focus-visible:ring-0 focus-visible:ring-offset-0",
                  "min-h-[72px]"
                )}
                ref={textareaRef}
                onKeyDown={handleKeyDown}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                  setInputMessage(e.target.value)
                  adjustHeight()
                }}
                disabled={false}
              />
            </div>

            <div className="h-14 bg-transparent flex items-center">
              <div className="absolute left-3 right-3 bottom-3 flex items-center justify-between w-[calc(100%-24px)]">
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 h-8 pl-1 pr-2 text-xs rounded-md">
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={currentModel}
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 5 }}
                        transition={{ duration: 0.15 }}
                        className="flex items-center gap-1"
                      >
                        {getModelIcon(currentModel)}
                        <span className="text-foreground">{currentModel}</span>
                      </motion.div>
                    </AnimatePresence>
                  </div>
                  
                  <div className="h-4 w-px bg-black/10 dark:bg-white/10 mx-0.5" />
                  
                  <button
                    className={cn(
                      "rounded-lg p-2 bg-black/5 dark:bg-white/5 cursor-not-allowed opacity-50",
                      "text-black/40 dark:text-white/40"
                    )}
                    aria-label="Attach file (disabled)"
                    disabled
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>
                </div>
                
                <button
                  type="button"
                  className={cn(
                    "rounded-lg p-2 bg-black/5 dark:bg-white/5",
                    "hover:bg-black/10 dark:hover:bg-white/10 focus-visible:ring-1 focus-visible:ring-offset-0 focus-visible:ring-blue-500",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                  aria-label="Send message"
                  disabled={isDisabled || !inputMessage.trim()}
                  onClick={handleSubmit}
                >
                  <ArrowRight
                    className={cn(
                      "w-4 h-4 dark:text-white transition-opacity duration-200",
                      inputMessage.trim() && !isDisabled ? "opacity-100" : "opacity-30"
                    )}
                  />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInput
