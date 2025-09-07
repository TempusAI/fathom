'use client'

import { useState } from 'react'
import { Check, ChevronDown, Filter } from 'lucide-react'
import { usePlaygroundStore } from '@/store'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'

const BATCH_OPTIONS = [
  'Overnight DQ',
  'Early Morning DQ', 
  'Late Morning DQ',
  'Afternoon DQ'
]

export function BatchFilter() {
  const { taskFilter, setTaskFilter } = usePlaygroundStore()
  const [isOpen, setIsOpen] = useState(false)

  const selectedBatches = taskFilter.correlationIds || []
  const hasFilter = selectedBatches.length > 0

  const handleBatchToggle = (batch: string) => {
    const currentBatches = selectedBatches
    const newBatches = currentBatches.includes(batch)
      ? currentBatches.filter(b => b !== batch)
      : [...currentBatches, batch]
    
    setTaskFilter({ 
      correlationIds: newBatches.length > 0 ? newBatches : undefined 
    })
  }

  const handleClearAll = () => {
    setTaskFilter({ correlationIds: undefined })
    setIsOpen(false)
  }

  const getDisplayText = () => {
    if (!hasFilter) {
      return 'All batches'
    }
    if (selectedBatches.length === 1) {
      return selectedBatches[0]
    }
    return `${selectedBatches.length} batches`
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            "justify-start text-left font-normal",
            !hasFilter && "text-muted-foreground",
            hasFilter && "text-foreground bg-transparent border-border"
          )}
        >
          <Filter className="mr-2 h-4 w-4" />
          {getDisplayText()}
          <ChevronDown className="ml-2 h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-0 bg-background border" align="start">
        <div className="p-2 space-y-1">
          {BATCH_OPTIONS.map((batch) => (
            <div
              key={batch}
              className={cn(
                "flex items-center space-x-2 rounded-sm px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground",
                selectedBatches.includes(batch) && "bg-accent text-accent-foreground"
              )}
              onClick={() => handleBatchToggle(batch)}
            >
              <div className={cn(
                "flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                selectedBatches.includes(batch) ? "bg-primary text-primary-foreground" : "opacity-50"
              )}>
                {selectedBatches.includes(batch) && (
                  <Check className="h-3 w-3" />
                )}
              </div>
              <span className="flex-1">{batch}</span>
            </div>
          ))}
        </div>
        {hasFilter && (
          <div className="p-2 border-t">
            <Button
              variant="ghost"
              size="sm"
              className="w-full"
              onClick={handleClearAll}
            >
              Clear filter
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}
