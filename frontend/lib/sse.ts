import { API_URL } from "./api";

export interface StepState {
  node: string;
  label: string;
  status: "pending" | "in_progress" | "done" | "error";
}

export interface StreamEvent {
  run_id: string;
  status: string;
  current_node: string;
  steps: StepState[];
}

/**
 * Subscribe to the backend's Server-Sent Events stream for a run.
 * Returns an unsubscribe function.
 */
export function subscribeToRun(
  runId: string,
  onUpdate: (evt: StreamEvent) => void,
  onDone: (status: string) => void,
): () => void {
  const source = new EventSource(`${API_URL}/api/run-stream/${runId}`);

  source.onmessage = (e) => {
    try {
      onUpdate(JSON.parse(e.data));
    } catch {
      /* ignore malformed frame */
    }
  };

  source.addEventListener("done", (e) => {
    let status = "completed";
    try {
      status = JSON.parse((e as MessageEvent).data).status;
    } catch {
      /* keep default */
    }
    onDone(status);
    source.close();
  });

  source.onerror = () => {
    source.close();
  };

  return () => source.close();
}
