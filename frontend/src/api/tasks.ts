import type {Task, TaskStore, Status} from '../types';
const DEMO: Task[] = [
  {id:1,title:'Подготовить техническое задание',completed:true},
  {id:2,title:'Реализовать страницу задач',completed:false},
  {id:3,title:'Добавить автоматические тесты',completed:false},
  {id:4,title:'Проверить адаптивную верстку',completed:false},
  {id:5,title:'Оформить README и отчет',completed:true}
];
const sleep = () => new Promise<void>(r => setTimeout(r, 130));
let tasks:Task[] = DEMO.map(t=>({...t})); let nextId=6;
const apiBase=(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/,'');
const updateMethod=(import.meta.env.VITE_API_UPDATE_METHOD ?? 'patch').toUpperCase();

async function request<T>(path:string, init:RequestInit = {}):Promise<T>{
  const controller=new AbortController(); const timeout=setTimeout(()=>controller.abort(),10000);
  try {
    const response=await fetch(`${apiBase}${path}`,{...init,signal:controller.signal,headers:{'Content-Type':'application/json',...(localStorage.getItem('taskflow_token') ? {'Authorization':`Bearer ${localStorage.getItem('taskflow_token')}`} : {}),...init.headers}});
    if(response.status===401){localStorage.removeItem('taskflow_token');window.dispatchEvent(new Event('taskflow-unauthorized'))} if(!response.ok){throw new Error(response.status===401||response.status===403?'Нет доступа':response.status===404?'Задача не найдена':response.status===422?'Проверьте корректность данных':`Ошибка сервера (${response.status})`)}
    return response.status===204?undefined as T:await response.json() as T;
  } catch(e) {if ((e as Error).name==='AbortError') throw new Error('Превышено время ожидания'); throw e;} finally {clearTimeout(timeout)}
}
export const store:TaskStore = apiBase? {
  async list(search,status){const q=new URLSearchParams();if(search.trim())q.set('search',search.trim());if(status!=='all')q.set('completed',String(status==='completed'));return request<Task[]>(`/tasks${q.size?'?'+q:''}`)},
  async create(title){await request('/tasks',{method:'POST',body:JSON.stringify({title})})},
  async update(id,patch){await request(`/tasks/${id}`,{method:updateMethod,body:JSON.stringify(patch)})},
  async remove(id){await request(`/tasks/${id}`,{method:'DELETE'})}
}:{
  async list(search,status){await sleep();return tasks.filter(t=>(!search.trim()||t.title.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()))&&(status==='all'||t.completed===(status==='completed'))).map(t=>({...t}))},
  async create(title){await sleep();tasks=[{id:nextId++,title,completed:false},...tasks]},
  async update(id,patch){await sleep();const task=tasks.find(t=>t.id===id);if(!task)throw new Error('Задача не найдена');Object.assign(task,patch)},
  async remove(id){await sleep();tasks=tasks.filter(t=>t.id!==id)}
};
export function isDemo(){return !apiBase}
export function resetDemo(){tasks=DEMO.map(t=>({...t}));nextId=6}

export const isBackendEnabled=()=>Boolean(apiBase);
export const isSignedIn=()=>Boolean(localStorage.getItem('taskflow_token'));
export function logout(){localStorage.removeItem('taskflow_token')}
export async function signIn(email:string,password:string, register=false){
  const response=await fetch(`${apiBase}/auth/${register?'register':'login'}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
  if(!response.ok){throw new Error(response.status===409?'Пользователь уже существует':response.status===401?'Неверный email или пароль':response.status===422?'Проверьте email и пароль':`Ошибка сервера (${response.status})`)}
  const data=await response.json() as {access_token:string};
  localStorage.setItem('taskflow_token',data.access_token);
}

export function googleAuthUrl(){return `${apiBase}/auth/google/login`}
export async function exchangeGoogleTicket(ticket:string){
 const r=await fetch(`${apiBase}/auth/google/exchange`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticket})});
 if(!r.ok)throw new Error('Не удалось завершить вход через Google');
 const data=await r.json() as {access_token:string};localStorage.setItem('taskflow_token',data.access_token);
}
