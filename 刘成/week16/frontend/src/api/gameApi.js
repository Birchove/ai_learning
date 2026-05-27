import axios from 'axios';

const API_BASE = '/api/games';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 minutes for auto run
});

// 创建游戏
export const createGame = async (config) => {
  const response = await api.post('', config);
  return response.data;
};

// 列出所有游戏
export const listGames = async () => {
  const response = await api.get('');
  return response.data;
};

// 获取游戏详情
export const getGame = async (gameId) => {
  const response = await api.get(`/${gameId}`);
  return response.data;
};

// 删除游戏
export const deleteGame = async (gameId) => {
  const response = await api.delete(`/${gameId}`);
  return response.data;
};

// 开始游戏
export const startGame = async (gameId) => {
  const response = await api.post(`/${gameId}/start`);
  return response.data;
};

// 获取游戏状态（玩家视角）
export const getGameState = async (gameId, playerId) => {
  const response = await api.get(`/${gameId}/state`, { params: { player_id: playerId } });
  return response.data;
};

// 提交行动
export const submitAction = async (gameId, action) => {
  const response = await api.post(`/${gameId}/action`, action);
  return response.data;
};

// 推进阶段
export const advancePhase = async (gameId) => {
  const response = await api.post(`/${gameId}/next_phase`);
  return response.data;
};

// AI自动对战
export const autoRunGame = async (gameId, rounds = 20) => {
  const response = await api.post(`/${gameId}/auto_run`, null, { params: { rounds } });
  return response.data;
};

// 获取游戏日志
export const getGameLog = async (gameId) => {
  const response = await api.get(`/${gameId}/log`);
  return response.data;
};

// 获取发言记录
export const getSpeeches = async (gameId) => {
  const response = await api.get(`/${gameId}/speeches`);
  return response.data;
};

export default api;