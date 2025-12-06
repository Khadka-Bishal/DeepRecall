import { Message } from '../types';
import { generateId, MESSAGE_ROLES } from '../utils';

export const createUserMessage = (content: string): Message => {
  return {
    id: generateId(),
    role: MESSAGE_ROLES.USER as 'user',
    content,
    timestamp: new Date(),
  };
};

export const createAssistantMessage = (content: string, retrievedChunks?: any[]): Message => {
  return {
    id: generateId(),
    role: MESSAGE_ROLES.ASSISTANT as 'assistant',
    content,
    timestamp: new Date(),
    retrievedChunks,
  };
};

export const createErrorMessage = (errorMessage: string): Message => {
  return createAssistantMessage(errorMessage);
};
