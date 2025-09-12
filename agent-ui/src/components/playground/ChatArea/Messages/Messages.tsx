import type { PlaygroundChatMessage } from '@/types/playground'

import { AgentMessage, UserMessage } from './MessageItem'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { memo, useMemo, useState } from 'react'
import {
  ToolCallProps,
  ReasoningStepProps,
  ReasoningProps,
  ReferenceData,
  Reference
} from '@/types/playground'
import React, { type FC } from 'react'
import ChatBlankState from './ChatBlankState'
import { TaskPanel } from '../../TaskPanel'
import { usePlaygroundStore } from '@/store'
import Icon from '@/components/ui/icon'
import { Badge } from '@/components/ui/badge'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'
import { toast } from 'sonner'

interface MessageListProps {
  messages: PlaygroundChatMessage[]
}

interface MessageWrapperProps {
  message: PlaygroundChatMessage
  isLastMessage: boolean
}

interface ReferenceProps {
  references: ReferenceData[]
}

interface ReferenceItemProps {
  reference: Reference
}

const ReferenceItem: FC<ReferenceItemProps> = ({ reference }) => (
  <div className="relative flex h-[63px] w-[190px] cursor-default flex-col justify-between overflow-hidden rounded-md bg-background-secondary p-3 transition-colors hover:bg-background-secondary/80">
    <p className="text-sm font-medium text-primary">{reference.name}</p>
    <p className="truncate text-xs text-primary/40">{reference.content}</p>
  </div>
)

const References: FC<ReferenceProps> = ({ references }) => (
  <div className="flex flex-col gap-4">
    {references.map((referenceData, index) => (
      <div
        key={`${referenceData.query}-${index}`}
        className="flex flex-col gap-3"
      >
        <div className="flex flex-wrap gap-3">
          {referenceData.references.map((reference, refIndex) => (
            <ReferenceItem
              key={`${reference.name}-${reference.meta_data.chunk}-${refIndex}`}
              reference={reference}
            />
          ))}
        </div>
      </div>
    ))}
  </div>
)

const AgentMessageWrapper = ({ message }: MessageWrapperProps) => {
  return (
    <div className="flex flex-col gap-y-9">
      {message.extra_data?.reasoning_steps &&
        message.extra_data.reasoning_steps.length > 0 && (
          <div className="flex items-start gap-4">
            <Tooltip>
              <TooltipTrigger asChild>
                <Icon type="reasoning" size="sm" />
              </TooltipTrigger>
              <TooltipContent side="top">
                <p className="text-accent">Reasoning</p>
              </TooltipContent>
            </Tooltip>
            <div className="flex flex-col gap-3">
              <p className="text-xs uppercase">Reasoning</p>
              <Reasonings reasoning={message.extra_data.reasoning_steps} />
            </div>
          </div>
        )}
      {message.extra_data?.references &&
        message.extra_data.references.length > 0 && (
          <div className="flex items-start gap-4">
            <Tooltip>
              <TooltipTrigger asChild>
                <Icon type="references" size="sm" />
              </TooltipTrigger>
              <TooltipContent side="top">
                <p className="text-accent">References</p>
              </TooltipContent>
            </Tooltip>
            <div className="flex flex-col gap-3">
              <References references={message.extra_data.references} />
            </div>
          </div>
        )}
      {message.tool_calls && message.tool_calls.length > 0 && (
        <div className="flex items-start gap-3">
          <Tooltip>
            <TooltipTrigger asChild>
              <Icon
                type="hammer"
                className="rounded-lg bg-background-secondary p-1"
                size="sm"
                color="secondary"
              />
            </TooltipTrigger>
            <TooltipContent side="top">
              <p className="text-accent">Tool Calls</p>
            </TooltipContent>
          </Tooltip>

          <div className="flex flex-wrap gap-2">
            {message.tool_calls.map((toolCall, index) => (
              <ToolCallBadge
                key={
                  toolCall.tool_call_id ||
                  `${toolCall.tool_name}-${toolCall.created_at}-${index}`
                }
                tools={toolCall}
              />
            ))}
          </div>
        </div>
      )}
      <AgentMessage message={message} />
    </div>
  )
}
const Reasoning: FC<ReasoningStepProps> = ({ index, stepTitle }) => (
  <div className="flex items-center gap-2 text-secondary">
    <div className="flex h-[20px] items-center rounded-md bg-background-secondary p-2">
      <p className="text-xs">STEP {index + 1}</p>
    </div>
    <p className="text-xs">{stepTitle}</p>
  </div>
)
const Reasonings: FC<ReasoningProps> = ({ reasoning }) => (
  <div className="flex flex-col items-start justify-center gap-2">
    {reasoning.map((title, index) => (
      <Reasoning
        key={`${title.title}-${title.action}-${index}`}
        stepTitle={title.title}
        index={index}
      />
    ))}
  </div>
)

const colorMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  sql_execute: 'outline',
  catalog_get_fields: 'outline',
}

const colorClasses: Record<string, string> = {
  catalog_get_fields: 'bg-blue-600 text-white hover:bg-blue-600/80 border-transparent',
  sql_execute: 'bg-violet-600 text-white hover:bg-violet-600/80 border-transparent',
}

function prettyJson(input: unknown): string {
  try {
    if (typeof input === 'string') {
      return JSON.stringify(JSON.parse(input), null, 2)
    }
    return JSON.stringify(input, null, 2)
  } catch {
    return typeof input === 'string' ? input : String(input)
  }
}

const ToolCallBadge = memo(({ tools }: ToolCallProps) => {
  const [open, setOpen] = useState(false)
  const variant = useMemo(() => {
    const key = (tools.tool_name || '').toLowerCase()
    return colorMap[key] ?? 'outline'
  }, [tools.tool_name])
  const extraClass = useMemo(() => {
    const key = (tools.tool_name || '').toLowerCase()
    return colorClasses[key] ?? ''
  }, [tools.tool_name])

  const argsPretty = useMemo(() => prettyJson(tools.tool_args || {}), [tools.tool_args])
  const resultPretty = useMemo(() => prettyJson(tools.content || ''), [tools.content])

  const onCopy = (label: string, text: string) => {
    try {
      void navigator.clipboard.writeText(text)
      toast.success(`${label} copied`)
    } catch {
      toast.error(`Failed to copy ${label}`)
    }
  }

  return (
    <HoverCard open={open} onOpenChange={setOpen}>
      <HoverCardTrigger asChild>
        <button type="button" onClick={() => setOpen((v) => !v)} className="focus:outline-none">
          <Badge variant={variant} className={`uppercase cursor-pointer select-none ${extraClass}`}>
            {tools.tool_name}
          </Badge>
        </button>
      </HoverCardTrigger>
      <HoverCardContent align="start" className="w-[560px] max-w-[80vw] p-3 bg-zinc-900 text-foreground border border-white/10">
        <div className={tools.tool_call_error ? 'border-l-2 border-destructive pl-3' : 'border-l-2 border-emerald-600 pl-3'}>
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant={variant} className={`uppercase ${extraClass}`}>{tools.tool_name}</Badge>
              <span className="text-xs text-muted">{new Date((tools.created_at ?? 0) * 1000).toLocaleTimeString()}</span>
            </div>
            <div className="text-xs text-muted">
              {typeof tools.metrics?.time === 'number' ? `${tools.metrics.time}ms` : ''}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-secondary">Arguments</p>
              <button type="button" onClick={() => onCopy('arguments', argsPretty)} className="text-xs hover:underline">Copy</button>
            </div>
            <pre className="max-h-56 overflow-auto rounded-md bg-muted p-2 text-xs whitespace-pre-wrap break-words">
              <code>{argsPretty}</code>
            </pre>

            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-secondary">Result</p>
              <button type="button" onClick={() => onCopy('result', resultPretty)} className="text-xs hover:underline">Copy</button>
            </div>
            <pre className="max-h-64 overflow-auto rounded-md bg-muted p-2 text-xs whitespace-pre-wrap break-words">
              <code>{resultPretty.length > 16384 ? resultPretty.slice(0, 16384) + '\n... (truncated)' : resultPretty}</code>
            </pre>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  )
})
ToolCallBadge.displayName = 'ToolCallBadge'
const Messages = ({ messages }: MessageListProps) => {
  const { isTaskPanelVisible } = usePlaygroundStore()
  
  if (messages.length === 0 && isTaskPanelVisible) {
    return (
      <div
        className="mx-auto w-full max-w-5xl px-4 flex items-center justify-center pt-10 md:pt-16"
        style={{ minHeight: 'calc(100vh - 380px)' }}
      >
        <div className="mx-auto w-full" style={{ height: 380 }}>
          <TaskPanel showHeader={false} className="h-full" />
        </div>
      </div>
    )
  }
  
  if (messages.length === 0) {
    return <ChatBlankState />
  }

  return (
    <>
      {messages.map((message, index) => {
        const key = `${message.role}-${message.created_at}-${index}`
        const isLastMessage = index === messages.length - 1

        if (message.role === 'agent') {
          return (
            <AgentMessageWrapper
              key={key}
              message={message}
              isLastMessage={isLastMessage}
            />
          )
        }
        return <UserMessage key={key} message={message} />
      })}
    </>
  )
}

export default Messages
