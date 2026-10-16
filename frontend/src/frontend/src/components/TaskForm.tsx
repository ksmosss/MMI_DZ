import {useEffect,useState} from 'react';
import type {Task} from '../types';

type TaskValues = {title:string;completed:boolean};
export function TaskForm({task,onSave,onClose,busy,error}:{task?:Task|null;onSave:(values:TaskValues)=>Promise<void>;onClose:()=>void;busy:boolean;error:string}){
 const [title,setTitle]=useState(task?.title??'');
 const [completed,setCompleted]=useState(task?.completed??false);
 const [invalid,setInvalid]=useState(false);
 useEffect(()=>{const onKey=(e:KeyboardEvent)=>{if(e.key==='Escape'&&!busy)onClose()};window.addEventListener('keydown',onKey);return ()=>window.removeEventListener('keydown',onKey)},[busy,onClose]);
 return <div className="overlay" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget&&!busy)onClose()}}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="form-heading"><h2 id="form-heading">{task?'Редактировать задачу':'Новая задача'}</h2><form onSubmit={e=>{e.preventDefault();if(!title.trim()){setInvalid(true);return}void onSave({title:title.trim(),completed})}} noValidate><label htmlFor="task-title">Название задачи</label><input id="task-title" autoFocus maxLength={200} value={title} aria-invalid={invalid} onChange={e=>{setTitle(e.target.value);setInvalid(false)}} placeholder="Что нужно сделать?"/>{invalid&&<p className="field-error" role="alert">Введите название задачи</p>}{task&&<label htmlFor="task-completed" className="status-field">Статус задачи<select id="task-completed" value={completed?'completed':'active'} onChange={e=>setCompleted(e.target.value==='completed')}><option value="active">В работе</option><option value="completed">Выполнена</option></select></label>}{error&&<p className="field-error" role="alert">{error}</p>}<div className="modal-actions"><button type="button" className="secondary" onClick={onClose} disabled={busy}>Отмена</button><button type="submit" disabled={busy}>{busy?'Сохранение…':'Сохранить'}</button></div></form></section></div>
}
