'use client'

import { Search, X } from 'lucide-react'
import { usePlaygroundStore } from '@/store'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export function SearchFilter() {
  const { taskFilter, setTaskFilter } = usePlaygroundStore()

  const handleSearchChange = (value: string) => {
    setTaskFilter({ searchQuery: value || undefined })
  }

  const clearSearch = () => {
    setTaskFilter({ searchQuery: undefined })
  }

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        placeholder="Search tasks, states, portfolios..."
        value={taskFilter.searchQuery || ''}
        onChange={(e) => handleSearchChange(e.target.value)}
        className="pl-10 pr-10 h-8"
      />
      {taskFilter.searchQuery && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2 p-0"
          onClick={clearSearch}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}
