
import apiClient from './client';

export type ContentType = 'plan' | 'chapter' | 'quiz' | 'simulation';
export type EngagementAction = 'like' | 'dislike' | 'rate';

export interface EngagementData {
  content_type: ContentType;
  content_id: string;
  action: EngagementAction;
  value: number;
  comment?: string;
}

export interface EngagementResponse {
  id: string;
  content_type: ContentType;
  content_id: string;
  action: EngagementAction;
  value: number;
  comment?: string;
}

export const submitEngagement = async (data: EngagementData) => {
  const response = await apiClient.post<EngagementResponse>('/engagement', data);
  return response.data;
};

export const getEngagement = async (
  contentType: ContentType,
  contentId: string,
  action: EngagementAction
) => {
  const response = await apiClient.get<EngagementResponse | null>('/engagement/me', {
    params: {
      content_type: contentType,
      content_id: contentId,
      action
    }
  });
  return response.data;
};
