'use client'

import { useState, useEffect } from 'react'
import { getApiBaseUrl } from '@/lib/api'
import { Clock, CheckCircle2, XCircle, Loader2, FileAudio, TrendingUp } from 'lucide-react'

interface Task {
  job_id: string
  filename: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  stage: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  error: string | null
  results: any | null
}

interface TasksByStatus {
  queued: Task[]
  processing: Task[]
  completed: Task[]
  failed: Task[]
}

export default function MissionControl() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [tasksByStatus, setTasksByStatus] = useState<TasksByStatus>({
    queued: [],
    processing: [],
    completed: [],
    failed: []
  })
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchTasks = async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/tasks?limit=50`)
      if (!response.ok) throw new Error('Failed to fetch tasks')
      
      const data = await response.json()
      setTasks(data.tasks || [])
      setTasksByStatus(data.by_status || {
        queued: [],
        processing: [],
        completed: [],
        failed: []
      })
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
    // Poll every 2 seconds for real-time updates
    const interval = setInterval(fetchTasks, 2000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'queued':
        return 'bg-slate-700/50 border-slate-600'
      case 'processing':
        return 'bg-cyan-900/30 border-cyan-600'
      case 'completed':
        return 'bg-green-900/30 border-green-600'
      case 'failed':
        return 'bg-red-900/30 border-red-600'
      default:
        return 'bg-slate-700/50 border-slate-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'queued':
        return <Clock className="w-4 h-4 text-slate-400" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />
      default:
        return <Clock className="w-4 h-4 text-slate-400" />
    }
  }

  const formatTime = (isoString: string | null) => {
    if (!isoString) return 'N/A'
    const date = new Date(isoString)
    return date.toLocaleTimeString()
  }

  const formatDuration = (start: string | null, end: string | null) => {
    if (!start) return 'N/A'
    const startTime = new Date(start)
    const endTime = end ? new Date(end) : new Date()
    const diff = Math.round((endTime.getTime() - startTime.getTime()) / 1000)
    if (diff < 60) return `${diff}s`
    return `${Math.floor(diff / 60)}m ${diff % 60}s`
  }

  const TaskCard = ({ task }: { task: Task }) => (
    <div className={`p-4 rounded-lg border ${getStatusColor(task.status)} backdrop-blur-sm hover:border-opacity-100 transition-all`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <FileAudio className="w-4 h-4 text-purple-400 flex-shrink-0" />
          <span className="text-sm font-medium text-white truncate">{task.filename}</span>
        </div>
        {getStatusIcon(task.status)}
      </div>
      
      {task.stage && (
        <div className="text-xs text-slate-400 mb-2">
          {task.stage}
        </div>
      )}
      
      {task.status === 'processing' && (
        <div className="mb-2">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Progress</span>
            <span>{task.progress}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5">
            <div 
              className="bg-gradient-to-r from-cyan-500 to-purple-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      )}
      
      {task.status === 'completed' && task.results && (
        <div className="flex items-center gap-1 text-xs text-green-400 mb-2">
          <TrendingUp className="w-3 h-3" />
          <span>{task.results.matches?.length || 0} matches found</span>
        </div>
      )}
      
      {task.error && (
        <div className="text-xs text-red-400 mb-2">
          Error: {task.error}
        </div>
      )}
      
      <div className="flex items-center justify-between text-xs text-slate-500 mt-2">
        <span>{formatTime(task.created_at)}</span>
        {task.started_at && (
          <span>{formatDuration(task.started_at, task.completed_at)}</span>
        )}
      </div>
    </div>
  )

  const Column = ({ title, tasks, status }: { title: string; tasks: Task[]; status: string }) => {
    const getColumnColor = () => {
      switch (status) {
        case 'queued':
          return 'border-slate-700'
        case 'processing':
          return 'border-cyan-700'
        case 'completed':
          return 'border-green-700'
        case 'failed':
          return 'border-red-700'
        default:
          return 'border-slate-700'
      }
    }

    return (
      <div className="flex-1 min-w-0">
        <div className={`mb-4 pb-3 border-b ${getColumnColor()}`}>
          <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
          <div className="text-sm text-slate-400">{tasks.length} tasks</div>
        </div>
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm bg-slate-900/30 rounded-lg border border-slate-800/50">
              No tasks in {title.toLowerCase()}
            </div>
          ) : (
            tasks.map((task) => (
              <TaskCard key={task.job_id} task={task} />
            ))
          )}
        </div>
      </div>
    )
  }

  if (loading && tasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
      </div>
    )
  }

  return (
    <div className="w-full bg-gradient-to-br from-slate-900/50 to-slate-950/50 rounded-xl p-6 border border-slate-800/50 backdrop-blur-sm">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent mb-1">
            Mission Control
          </h2>
          <p className="text-sm text-slate-400">
            Real-time task monitoring and progress tracking
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-400">Last updated</div>
          <div className="text-sm text-cyan-400 font-mono">
            {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Column 
          title="Queued" 
          tasks={tasksByStatus.queued} 
          status="queued"
        />
        <Column 
          title="Processing" 
          tasks={tasksByStatus.processing} 
          status="processing"
        />
        <Column 
          title="Completed" 
          tasks={tasksByStatus.completed} 
          status="completed"
        />
        <Column 
          title="Failed" 
          tasks={tasksByStatus.failed} 
          status="failed"
        />
      </div>

      {/* Stats Footer */}
      <div className="mt-6 pt-6 border-t border-slate-800">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-white">{tasks.length}</div>
            <div className="text-xs text-slate-400">Total Tasks</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-cyan-400">{tasksByStatus.processing.length}</div>
            <div className="text-xs text-slate-400">Active</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">{tasksByStatus.completed.length}</div>
            <div className="text-xs text-slate-400">Completed</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-400">{tasksByStatus.failed.length}</div>
            <div className="text-xs text-slate-400">Failed</div>
          </div>
        </div>
      </div>
    </div>
  )
}
