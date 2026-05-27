import { useState, useEffect } from 'react';
import GameList from './pages/GameList';
import GameRoom from './pages/GameRoom';
import useGameStore from './hooks/useGameStore';

export default function App() {
  const { gameId, reset } = useGameStore();

  return (
    <div className="min-h-screen">
      {gameId ? <GameRoom /> : <GameList />}
    </div>
  );
}