'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { Calendar as CalendarIcon } from 'lucide-react'
import { usePlaygroundStore } from '@/store'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'

export function DateFilter() {
  const { taskFilter, setTaskFilter } = usePlaygroundStore()
  const [isOpen, setIsOpen] = useState(false)

  const handleDateSelect = (date: Date | undefined) => {
    if (date) {
      const dateString = format(date, 'yyyy-MM-dd')
      setTaskFilter({ 
        dateFrom: dateString,
        dateTo: dateString 
      })
    } else {
      setTaskFilter({ 
        dateFrom: undefined,
        dateTo: undefined 
      })
    }
    setIsOpen(false)
  }

  const selectedDate = taskFilter.dateFrom ? new Date(taskFilter.dateFrom) : undefined
  const hasFilter = !!taskFilter.dateFrom

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            "w-full justify-start text-left font-normal",
            !selectedDate && "text-muted-foreground",
            hasFilter && "text-foreground bg-transparent border-border"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {selectedDate ? (
            format(selectedDate, "MMM d")
          ) : (
            <span>Filter by date</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 bg-background border" align="start">
        <Calendar
          mode="single"
          selected={selectedDate}
          onSelect={handleDateSelect}
          disabled={(date) =>
            date > new Date() || date < new Date("2020-01-01")
          }
          initialFocus
        />
        {hasFilter && (
          <div className="p-3 border-t">
            <Button
              variant="ghost"
              size="sm"
              className="w-full"
              onClick={() => handleDateSelect(undefined)}
            >
              Clear filter
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}
