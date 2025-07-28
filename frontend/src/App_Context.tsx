import React, { createContext, useContext, useState } from 'react';
import { Task } from './types';

interface AppContextType {
  tasks: Task[];
  activeTaskId: string | null;
  setTasks: React.Dispatch<React.SetStateAction<Task[]>>;
  setActiveTaskId: React.Dispatch<React.SetStateAction<string | null>>;
  getActiveTask: () => Task | null;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';

  const getActiveTask = (): Task | null => {
    return tasks.find(task => task.id === activeTaskId) || null;
  };

  const value: AppContextType = {
    tasks,
    activeTaskId,
    setTasks,
    setActiveTaskId,
    getActiveTask,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};