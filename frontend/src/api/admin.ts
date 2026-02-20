
import apiClient from './client';

import type { Engagement } from '../types';

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  created_at: string;
}

export const fetchUsers = async () => {
  const response = await apiClient.get<User[]>('/admin/users');
  return response.data;
};

export const deleteUser = async (userId: string) => {
  const response = await apiClient.delete<User>(`/admin/users/${userId}`);
  return response.data;
};

export const fetchEngagements = async () => {
  const response = await apiClient.get<Engagement[]>('/engagement/all');
  return response.data;
};
