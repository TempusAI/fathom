import Icon from '@/components/ui/icon'
import MarkdownRenderer from '@/components/ui/typography/MarkdownRenderer'
import { usePlaygroundStore } from '@/store'
import type { PlaygroundChatMessage } from '@/types/playground'
import Videos from './Multimedia/Videos'
import Images from './Multimedia/Images'
import Audios from './Multimedia/Audios'
import { memo } from 'react'
import AgentThinkingLoader from './AgentThinkingLoader'
import { Badge } from '@/components/ui/badge'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Database, TrendingUp } from 'lucide-react'

interface MessageProps {
  message: PlaygroundChatMessage
}

const AgentMessage = ({ message }: MessageProps) => {
  const { streamingErrorMessage } = usePlaygroundStore()
  let messageContent
  if (message.streamingError) {
    messageContent = (
      <p className="text-destructive">
        Oops! Something went wrong while streaming.{' '}
        {streamingErrorMessage ? (
          <>{streamingErrorMessage}</>
        ) : (
          'Please try refreshing the page or try again later.'
        )}
      </p>
    )
  } else if (message.content) {
    messageContent = (
      <div className="flex w-full flex-col gap-4">
        <MarkdownRenderer>{message.content}</MarkdownRenderer>
        {message.videos && message.videos.length > 0 && (
          <Videos videos={message.videos} />
        )}
        {message.images && message.images.length > 0 && (
          <Images images={message.images} />
        )}
        {message.audio && message.audio.length > 0 && (
          <Audios audio={message.audio} />
        )}
      </div>
    )
  } else if (message.response_audio) {
    if (!message.response_audio.transcript) {
      messageContent = (
        <div className="mt-2 flex items-start">
          <AgentThinkingLoader />
        </div>
      )
    } else {
      messageContent = (
        <div className="flex w-full flex-col gap-4">
          <MarkdownRenderer>
            {message.response_audio.transcript}
          </MarkdownRenderer>
          {message.response_audio.content && message.response_audio && (
            <Audios audio={[message.response_audio]} />
          )}
        </div>
      )
    }
  } else {
    messageContent = (
      <div className="mt-2">
        <AgentThinkingLoader />
      </div>
    )
  }

  return (
    <div className="flex flex-row items-start gap-4 font-geist">
      <div className="flex-shrink-0">
        <Icon type="agent" size="sm" />
      </div>
      {messageContent}
    </div>
  )
}

const UserMessage = memo(({ message }: MessageProps) => {
  return (
    <div className="flex items-start pt-4 text-start max-md:break-words">
      <div className="flex flex-row gap-x-3">
        <p className="flex items-center gap-x-2 text-sm font-medium text-muted">
          <Icon type="user" size="sm" />
        </p>
        <div className="text-md rounded-lg py-1 font-geist text-secondary">
          {/* Task chip above the message */}
          {message.attached_tasks && message.attached_tasks.length > 0 && (
            <div className="mb-1 flex flex-wrap gap-2">
              {(() => {
                // Group attached tasks by their ultimate parent id
                const groupsMap: Record<string, typeof message.attached_tasks> = {}
                for (const t of message.attached_tasks!) {
                  const pid = (t.ultimateParentTask?.id ?? t.id) as string
                  groupsMap[pid] = groupsMap[pid] ? [...groupsMap[pid]!, t] : [t]
                }
                const groups = Object.entries(groupsMap)
                return groups.map(([pid, tasks]) => {
                  const parent = tasks.find((x) => x.id === pid) ?? tasks[0]
                  const isGroup = tasks.length > 1
                  const portfolio = parent?.fields?.find((f: any) => f.name === 'PortfolioCode')?.value
                  const ticker = parent?.fields?.find((f: any) => f.name === 'Ticker')?.value
                  return (
                    <Popover key={pid}>
                      <PopoverTrigger asChild>
                        <div className="inline-flex items-center gap-2 text-xs rounded-md border border-primary/30 bg-primary/5 px-2 py-1 cursor-pointer">
                          {isGroup ? (
                            <>
                              <span className="truncate max-w-[200px]">{parent?.taskDefinitionDisplayName}</span>
                              <span className="px-1.5 py-0.5 bg-primary/20 rounded text-[10px]">{tasks.length} tasks</span>
                            </>
                          ) : (
                            <div className="flex items-center gap-2">
                              {portfolio && (
                                <span className="flex items-center gap-1">
                                  <Database className="h-3 w-3 text-muted-foreground" />
                                  <span>{String(portfolio)}</span>
                                </span>
                              )}
                              {ticker && (
                                <span className="flex items-center gap-1">
                                  <TrendingUp className="h-3 w-3 text-muted-foreground" />
                                  <span className="font-medium">{String(ticker)}</span>
                                </span>
                              )}
                              {!portfolio && !ticker && (
                                <span>{parent?.taskDefinitionDisplayName ?? 'Task attached'}</span>
                              )}
                            </div>
                          )}
                        </div>
                      </PopoverTrigger>
                      <PopoverContent className="w-96 text-xs bg-background shadow-md">
                        <p className="mb-2 text-muted-foreground">{isGroup ? 'Tasks in this group:' : 'Task details:'}</p>
                        <div className="space-y-2 max-h-80 overflow-auto">
                          {tasks.map((t) => {
                            const p = t.fields?.find((f: any) => f.name === 'PortfolioCode')?.value
                            const tk = t.fields?.find((f: any) => f.name === 'Ticker')?.value
                            return (
                              <div key={t.id} className="rounded border border-border/30 p-2">
                                <div className="flex items-center gap-2 text-xs">
                                  {p && (
                                    <span className="flex items-center gap-1">
                                      <Database className="h-3 w-3" />
                                      <span>{String(p)}</span>
                                    </span>
                                  )}
                                  {tk && (
                                    <span className="flex items-center gap-1">
                                      <TrendingUp className="h-3 w-3" />
                                      <span className="font-medium">{String(tk)}</span>
                                    </span>
                                  )}
                                </div>
                                <div className="mt-1 text-[11px] text-muted-foreground">{t.taskDefinitionDisplayName}</div>
                              </div>
                            )
                          })}
                        </div>
                      </PopoverContent>
                    </Popover>
                  )
                })
              })()}
            </div>
          )}
          {message.content}
        </div>
      </div>
    </div>
  )
})

AgentMessage.displayName = 'AgentMessage'
UserMessage.displayName = 'UserMessage'
export { AgentMessage, UserMessage }
