import {describe,it,expect,vi} from 'vitest';
import {render,screen,fireEvent} from '@testing-library/react';
import {TaskForm} from '../components/TaskForm';
import {TaskList} from '../components/TaskList';
import React from 'react';
describe('TaskFlow components',()=>{
it('показывает задачи и статус',()=>{render(<TaskList tasks={[{id:1,title:'Проверить UI',completed:false}]} busyId={null} onToggle={()=>{}} onEdit={()=>{}} onDelete={()=>{}}/>);expect(screen.getAllByText('Проверить UI').length).toBeGreaterThan(0);expect(screen.getAllByText('В работе').length).toBeGreaterThan(0)});
it('не отправляет пустое название',()=>{const save=vi.fn();render(<TaskForm onSave={save} onClose={()=>{}} busy={false} error=""/>);fireEvent.click(screen.getByRole('button',{name:'Сохранить'}));expect(screen.getByRole('alert')).toHaveTextContent('Введите название');expect(save).not.toHaveBeenCalled()});
it('отправляет название без пробелов по краям',()=>{const save=vi.fn().mockResolvedValue(undefined);render(<TaskForm onSave={save} onClose={()=>{}} busy={false} error=""/>);fireEvent.change(screen.getByLabelText('Название задачи'),{target:{value:'  Новый пункт  '}});fireEvent.click(screen.getByRole('button',{name:'Сохранить'}));expect(save).toHaveBeenCalledWith({title:'Новый пункт',completed:false})});
it('позволяет изменить название и статус',()=>{const save=vi.fn().mockResolvedValue(undefined);render(<TaskForm task={{id:5,title:'Старая',completed:false}} onSave={save} onClose={()=>{}} busy={false} error=""/>);fireEvent.change(screen.getByLabelText('Название задачи'),{target:{value:'Новая'}});fireEvent.change(screen.getByLabelText('Статус задачи'),{target:{value:'completed'}});fireEvent.click(screen.getByRole('button',{name:'Сохранить'}));expect(save).toHaveBeenCalledWith({title:'Новая',completed:true})});
it('подтверждает переключение статуса',()=>{const onToggle=vi.fn();render(<TaskList tasks={[{id:2,title:'Выполнить задачу',completed:false}]} busyId={null} onToggle={onToggle} onEdit={()=>{}} onDelete={()=>{}}/>);fireEvent.click(screen.getAllByRole('checkbox')[0]);expect(onToggle).toHaveBeenCalledWith({id:2,title:'Выполнить задачу',completed:false})});
it('показывает ошибку сохранения',()=>{render(<TaskForm onSave={vi.fn()} onClose={()=>{}} busy={false} error="Ошибка сервера (500)"/>);expect(screen.getByRole('alert')).toHaveTextContent('Ошибка сервера')});
});
