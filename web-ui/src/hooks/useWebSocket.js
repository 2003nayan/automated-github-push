import { useEffect, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

export const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    // Use current origin if no URL provided (works in both dev and production)
    const socketUrl = url || window.location.origin;

    const newSocket = io(socketUrl, {
      transports: ['websocket', 'polling'],
    });

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    newSocket.on('backup_started', (data) => {
      console.log('Backup started:', data);
      setEvents(prev => [...prev, { type: 'backup_started', ...data }]);
    });

    newSocket.on('backup_completed', (data) => {
      console.log('Backup completed:', data);
      setEvents(prev => [...prev, { type: 'backup_completed', ...data }]);
    });

    newSocket.on('project_detected', (data) => {
      console.log('Project detected:', data);
      setEvents(prev => [...prev, { type: 'project_detected', ...data }]);
    });

    newSocket.on('backup_error', (data) => {
      console.log('Backup error:', data);
      setEvents(prev => [...prev, { type: 'backup_error', ...data }]);
    });

    setSocket(newSocket);

    return () => {
      console.log('Cleaning up WebSocket connection');
      newSocket.close();
    };
  }, [url]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return { socket, connected, events, clearEvents };
};
