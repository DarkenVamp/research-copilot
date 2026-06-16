import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "../lib/api";

export const sessionKeys = {
  all: ["sessions"] as const,
  detail: (id: string) => ["session", id] as const,
  messages: (id: string) => ["messages", id] as const,
};

export function useSessions() {
  return useQuery({
    queryKey: sessionKeys.all,
    queryFn: api.listSessions,
  });
}

export function useSession(id: string) {
  return useQuery({
    queryKey: sessionKeys.detail(id),
    queryFn: () => api.getSession(id),
    enabled: !!id,
  });
}

export function useCreateSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: sessionKeys.all }),
  });
}

export function useRunWorkflow(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.runWorkflow(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: sessionKeys.detail(id) });
      qc.invalidateQueries({ queryKey: sessionKeys.all });
    },
  });
}

export function useResumeWorkflow(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.resumeWorkflow(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: sessionKeys.detail(id) }),
  });
}

export function useMessages(id: string, enabled: boolean) {
  return useQuery({
    queryKey: sessionKeys.messages(id),
    queryFn: () => api.getMessages(id),
    enabled: enabled && !!id,
  });
}
