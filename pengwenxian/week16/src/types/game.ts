export type Camp = 'werewolf' | 'villager' | 'god'
export type Visibility = 'public' | 'private'
export type GameStatus = 'pending' | 'running' | 'summarizing' | 'completed' | 'failed' | 'stopped'

export interface GameSummary {
  id: string
  title: string
  description: string
  current_phase: string
  day: number
  winner: string | null
  status: GameStatus
}

export interface PlayerSummary {
  id: string
  seat: number
  name: string
  role: string
  camp: Camp
  alive: boolean
  tags: string[]
}

export interface TimelineEvent {
  id: string
  day: number
  phase: string
  title: string
  summary: string
  visibility: Visibility
}

export interface GameDetail extends GameSummary {
  players: PlayerSummary[]
  timeline: TimelineEvent[]
  decision_traces: DecisionTrace[]
  camps_status: Record<string, number>
  created_at: string
  progress_message: string
  replay_ready: boolean
  error_message: string | null
}

export interface DecisionTrace {
  id: string
  day: number
  phase: string
  seat: number
  player_name: string
  role: string
  camp: Camp
  action_type: string
  thought: string
  choice: string
  target_seat: number | null
  public_message: string | null
  raw_reason: string | null
}

export interface ReplayReport {
  game_id: string
  summary: string
  key_turning_points: string[]
  attribution: {
    winning_reason: string
    losing_reason: string
    collaboration_note: string
  }
  metrics: Record<string, string | number>
}
