export type Task = { id: number; title: string; completed: boolean };
export type Status = 'all' | 'active' | 'completed';
export interface TaskStore {
  list(search: string, status: Status): Promise<Task[]>;
  create(title: string): Promise<void>;
  update(id: number, patch: Partial<Pick<Task,'title'|'completed'>>): Promise<void>;
  remove(id: number): Promise<void>;
}
