"""Native Vortex helper desktop app. No browser engine or remote account access."""
from __future__ import annotations
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import filedialog

from desktop_ui import DesktopApp, benchmark, button, card, capture_window, label, put_text, text_area,round_shape
from helper_runtime import HelperSession

WORDS = {
 'ru': dict(local='Локальное управление. Без доступа к аккаунту.', workspace='ПОМОЩНИК ЗАГРУЗКИ', light='Светлая тема', dark='Тёмная тема',
    overview='Управление', activity='Журнал', help='Схема работы', title='Vortex Helper',
    subtitle='Один точный клик, когда меняется мод. Даже если кнопка перемещается.',
    idle='Готов к запуску', running='Помощник работает', paused='Пауза', checking='Проверка окна Vortex', stopped='Помощник остановлен', failed='Нужно ваше внимание',
    intro='Кнопка: Download manually.',
    start='Запустить', pause='Пауза', resume='Продолжить', stop='Остановить', check='Проверить без нажатий',
    clicks='Нажатий', clicks_hint='за текущий запуск', progress='Позиция в коллекции', progress_hint='по данным окна Vortex',
    current='Текущий мод', current_hint='ожидаем следующее окно', recent='Последние действия', time='Время', event='Событие',
    target='Программа Vortex', automatic='Автоматическое определение', browse='Выбрать…', choose='Выберите Vortex.exe',
    quiet='F8 — остановить · F9 — пауза / продолжение',
    none='Запустите помощник или проверьте окно без нажатий.', waiting='Ожидание следующего окна загрузки',
    clicked='Нажатие №{count} · {progress} · {mod}', detected='Найдено без нажатия · {progress} · {mod}',
    absent='Подходящего окна загрузки сейчас нет. Ничего не нажато.', duplicate='Уже работает другой экземпляр помощника.',
    timeout='Время ожидания истекло. Проверьте результат в Vortex.', target_event='Программа: {path}',
    error='Ошибка: {message}', ended='Сеанс завершён', safe='Нажатий по координатам нет. Premium, Skip и Cancel не используются.',
    help_title='Vortex Helper',flow_one='Vortex',flow_two='Проверка окна',flow_three='Нажатие',
    step_one='Откройте загрузку коллекции в Vortex.',step_two='Проверьте доступ к кнопке без нажатий.',step_three='Запустите помощник. Новый мод — одно нажатие.',
    guide_note='Страницы сайта, CAPTCHA и ошибки установки требуют отдельного действия.',
    help_body='1. Откройте Vortex и начните загрузку коллекции.\n\n2. Нажмите «Проверить без нажатий», чтобы проверить доступность нужного окна.\n\n3. Запустите помощник. Кнопка нажимается только после двух стабильных наблюдений одного мода и повторной проверки прямо перед нажатием.\n\n4. Остановите помощник после завершения. Его остановка по таймауту не означает, что все файлы скачались.\n\nСтраницы браузера, CAPTCHA, вход в аккаунт и ошибки установки требуют отдельного внимания. Помощник не изменяет файлы модов и не управляет учётной записью.\n\nПроверенные элементы интерфейса Vortex имеют английские названия. Переключение языка здесь меняет язык помощника.\n\nЖурнал этого окна хранится в памяти, настройки языка и темы — локально. Консольный помощник также ведёт свой журнал в папке TEMP.',
    demo='Пример работы · вымышленные данные'),
 'en': dict(local='Local controls. No account access.', workspace='DOWNLOAD ASSISTANT', light='Light theme', dark='Dark theme',
    overview='Controls', activity='Activity', help='Workflow', title='Vortex Helper',
    subtitle='One deliberate click when the mod changes. Even when the button moves.',
    idle='Ready when you are', running='Helper is running', paused='Paused', checking='Checking the Vortex window', stopped='Helper stopped', failed='Your attention is needed',
    intro='Target button: Download manually.',
    start='Start helper', pause='Pause', resume='Resume', stop='Stop', check='Check without clicking',
    clicks='Clicks', clicks_hint='in this session', progress='Collection position', progress_hint='reported by the Vortex dialog',
    current='Current mod', current_hint='waiting for the next dialog', recent='Recent activity', time='Time', event='Event',
    target='Vortex application', automatic='Automatic detection', browse='Browse…', choose='Select Vortex.exe',
    quiet='F8 — stop · F9 — pause / resume',
    none='Start the helper or check the window without clicking.', waiting='Waiting for the next download dialog',
    clicked='Click #{count} · {progress} · {mod}', detected='Detected without clicking · {progress} · {mod}',
    absent='No eligible download dialog is currently visible. Nothing was clicked.', duplicate='Another helper instance is already running.',
    timeout='Idle timeout. Check the result in Vortex.', target_event='Application: {path}',
    error='Error: {message}', ended='Session ended', safe='No coordinate clicks. Premium, Skip and Cancel are never used.',
    help_title='Vortex Helper',flow_one='Vortex',flow_two='Read dialog',flow_three='Click',
    step_one='Open a collection download in Vortex.',step_two='Check button access without clicking.',step_three='Start the helper. One click for each new mod.',
    guide_note='Website pages, CAPTCHA and installation errors need separate attention.',
    help_body='1. Open Vortex and start a collection download.\n\n2. Use Check without clicking to check whether the expected dialog is accessible.\n\n3. Start the helper. A button is invoked only after two stable observations of a mod and a fresh check immediately before the click.\n\n4. Stop the helper when finished. An idle timeout does not establish that every file downloaded.\n\nBrowser pages, CAPTCHA, account login and installation errors may still need your attention. The helper does not alter mod files or access your account.\n\nThe verified Vortex controls have English labels. The language selector here changes the helper language.\n\nThis window keeps its activity log in memory and saves language/theme settings locally. The console helper also keeps its own log in TEMP.',
    demo='Sample session · synthetic data'),
}


class HelperApp(DesktopApp):
    def __init__(self, root, storage=None, session_factory=HelperSession):
        self.session_factory = session_factory
        self.session = None
        self.state_key = 'idle'
        self.count = 0
        self.progress_value = '—'
        self.mod = ''
        self.activity = []
        self.event_sequence = 0
        self.resolved_path = ''
        self.demo = False
        super().__init__(root, 'VortexDownloadHelper', WORDS, storage, purple=True)
        self.vortex_path = self.settings.get('vortex_path', '')
        self.render()

    def render(self):
        parent = self.shell('Vortex Helper', '', [self.t('overview'), self.t('activity'), self.t('help')])
        if self.nav == 2:
            self.render_guide(parent)
            return
        if self.nav == 0:
            hero=card(parent,self.p,padx=22,pady=14); hero.pack(fill='x',pady=(0,16))
            self.status_label=label(hero,'',self.p,14,True)
            self.status_label.pack(anchor='w')
            label(hero,self.t('intro'),self.p,10,muted=True).pack(anchor='w',pady=(8,12))
            controls=tk.Frame(hero,bg=self.p['card']); controls.pack(fill='x')
            self.start_button=button(controls,self.t('start'),lambda:self.start(False),self.p,True)
            self.start_button.configure(state='disabled' if self.busy else 'normal'); self.start_button.pack(side='left')
            self.pause_button=button(controls,self.t('resume' if self.state_key=='paused' else 'pause'),self.pause,self.p)
            self.pause_button.configure(state='normal' if self.busy and self.state_key != 'checking' else 'disabled'); self.pause_button.pack(side='left',padx=10)
            self.stop_button=button(controls,self.t('stop'),self.cancel,self.p)
            self.stop_button.configure(state='normal' if self.busy else 'disabled'); self.stop_button.pack(side='left')
            self.check_button=button(controls,self.t('check'),lambda:self.start(True),self.p)
            self.check_button.pack(side='right')
            pathrow=tk.Frame(hero,bg=self.p['card']); pathrow.pack(fill='x',pady=(12,0))
            label(pathrow,self.t('target'),self.p,9,muted=True).pack(side='left')
            self.choose_button=button(pathrow,self.t('browse'),self.browse,self.p)
            self.choose_button.configure(pady=5); self.choose_button.pack(side='right')
            self.path_label=label(pathrow,self.vortex_path or self.t('automatic'),self.p,9,muted=True,wraplength=450)
            self.path_label.pack(side='right',padx=12)
            self.metric_labels=self.metrics(parent,[(self.t('clicks'),self.count,self.t('clicks_hint')),
                                 (self.t('progress'),self.progress_value,self.t('progress_hint'))])
            current=card(parent,self.p,padx=18,pady=10); current.pack(fill='x',pady=(0,16))
            label(current,self.t('current'),self.p,9,muted=True).pack(anchor='w')
            self.mod_label=label(current,'',self.p,12,True,wraplength=740)
            self.mod_label.pack(anchor='w',pady=(5,0))
        foot=self.t('demo') if self.demo else self.t('quiet')
        label(parent,foot,self.p,9,muted=True,wraplength=850).pack(side='bottom',anchor='w',pady=(13,0))
        panel=card(parent,self.p); panel.pack(fill='both',expand=True)
        label(panel,self.t('recent'),self.p,11,True).pack(anchor='w',padx=16,pady=13)
        self.details=text_area(panel,self.p,height=2 if self.nav==0 else 5)
        self.tree=self.table(panel,[('time',self.t('time'),90),('event',self.t('event'),700)],heights=2 if self.nav==0 else 13)
        self.tree.bind('<<TreeviewSelect>>',self.select_activity)
        for event in reversed(self.activity):
            self.tree.insert('', 'end', iid=event['id'], values=(event['local_time'], self.event_text(event)))
        self.update_controls()
        self.select_activity()

    def render_guide(self,parent):
        p=self.p
        label(parent,self.t('help'),p,12,True).pack(anchor='w',pady=(0,18))
        panel=card(parent,p,padx=22,pady=22);panel.pack(fill='x')
        diagram=tk.Canvas(panel,height=135,bg=p['card'],highlightthickness=0);diagram.pack(fill='x');self.flow_diagram=diagram
        def draw(_=None):
            diagram.delete('all');width=diagram.winfo_width();cell=(width-48)/3
            for index,key in enumerate(('flow_one','flow_two','flow_three')):
                x=8+index*(cell+16)
                round_shape(diagram,x,22,x+cell,110,16,fill=p['field'],outline='')
                diagram.create_oval(x+16,38,x+44,66,fill=p['accent'],outline='')
                diagram.create_text(x+30,52,text=str(index+1),fill=p['ink'],font=('Segoe UI',10,'bold'))
                diagram.create_text(x+16,88,text=self.t(key),fill=p['text'],anchor='w',font=('Segoe UI',11,'bold'))
                if index<2:diagram.create_line(x+cell+3,66,x+cell+13,66,fill=p['muted'],width=2,arrow='last')
        diagram.bind('<Configure>',draw)
        for index,key in enumerate(('step_one','step_two','step_three')):
            row=tk.Frame(panel,bg=p['card']);row.pack(fill='x',pady=12)
            label(row,str(index+1).zfill(2),p,12,True,muted=True).pack(side='left',padx=(0,18))
            label(row,self.t(key),p,11,wraplength=680).pack(side='left')
        controls=tk.Frame(panel,bg=p['card']);controls.pack(fill='x',pady=(18,0))
        self.check_button=button(controls,self.t('check'),lambda:self.start(True),p,True)
        self.check_button.pack(side='left')
        self.guide_status=label(panel,'',p,10,muted=True,wraplength=740)
        self.guide_status.pack(anchor='w',pady=(18,0))
        self.update_controls()
        label(parent,self.t('guide_note'),p,10,muted=True,wraplength=840).pack(anchor='w',pady=20)
        shortcuts=card(parent,p,padx=20,pady=16);shortcuts.pack(fill='x')
        label(shortcuts,self.t('quiet'),p,11,True).pack(anchor='w')

    def browse(self):
        selected=filedialog.askopenfilename(parent=self.root,title=self.t('choose'),filetypes=[('Vortex','Vortex.exe')])
        if selected:
            self.vortex_path=selected
            self.resolved_path=''
            self.settings['vortex_path']=selected
            self.save_settings()
            self.update_controls()

    def start(self, check_only=False):
        if self.busy:
            return
        self.busy=True; self.demo=False; self.state_key='checking' if check_only else 'running'
        if not check_only:
            self.count=0; self.progress_value='—'; self.mod=''
        self.session=self.session_factory(self.events.put, language=self.language, vortex_path=self.vortex_path, check_only=check_only)
        self.update_controls()
        self.session.start()

    def pause(self):
        if self.session and self.busy:
            self.session.control('resume' if self.state_key=='paused' else 'pause')

    def cancel(self):
        if self.session:
            self.session.stop()

    def event_text(self, event):
        kind=event['type']; data=event.get('data') or {}
        key={'target':'target_event','running':'running','paused':'paused','stopped':'stopped','ended':'ended',
             'waiting':'waiting','clicked':'clicked','detected':'detected','absent':'absent','duplicate':'duplicate',
             'timeout':'timeout','error':'error'}.get(kind)
        return self.t(key,**data) if key else kind

    def update_controls(self):
        ready = 'disabled' if self.busy else 'normal'
        latest = self.event_text(self.activity[-1]) if self.activity else self.t('none')
        if self.nav == 2:
            self.check_button.configure(state=ready)
            self.guide_status.configure(text=latest)
        elif self.nav == 0:
            self.status_label.configure(text='●  '+self.t(self.state_key),
                fg=self.p['red'] if self.state_key == 'failed' else self.p['accent'])
            self.start_button.configure(state=ready)
            self.check_button.configure(state=ready)
            self.choose_button.configure(state=ready)
            can_pause = self.busy and self.state_key in ('running','paused')
            self.pause_button.configure(text=self.t('resume' if self.state_key=='paused' else 'pause'),
                                        state='normal' if can_pause else 'disabled')
            self.stop_button.configure(state='normal' if self.busy else 'disabled')
            self.path_label.configure(text=self.vortex_path or self.resolved_path or self.t('automatic'))
            self.metric_labels[0].configure(text=str(self.count))
            self.metric_labels[1].configure(text=self.progress_value)
            self.mod_label.configure(text=self.mod or self.t('current_hint'))

    def select_activity(self,_=None):
        selected = self.tree.selection()
        event = next((event for event in self.activity if selected and event['id'] == selected[0]), None)
        if event is None and self.activity:
            event = self.activity[-1]
        put_text(self.details, self.event_text(event) if event else self.t('none'))

    def handle_event(self,event):
        kind=event['type']; data=event.get('data') or {}
        if kind != 'ended':
            self.event_sequence += 1
            event = dict(event, id=str(self.event_sequence), local_time=datetime.now().strftime('%H:%M:%S'))
            self.activity.append(event)
            expired = self.activity.pop(0) if len(self.activity) > 200 else None
        if kind in ('clicked','detected'):
            self.mod=str(data.get('mod','')); self.progress_value=str(data.get('progress','—'))
            if kind=='clicked': self.count=int(data.get('count',self.count))
        if kind in ('running','paused'):
            self.state_key=kind
        elif kind=='error' or kind=='duplicate':
            self.state_key='failed'
        elif kind in ('stopped','timeout') and self.state_key != 'failed':
            self.state_key='stopped'
        elif kind=='ended':
            self.busy=False
            if self.state_key not in ('failed','idle'): self.state_key='stopped'
        if kind=='absent' and self.state_key=='checking':
            self.state_key='idle'
        if kind=='target':
            self.resolved_path=data.get('path','')
        self.update_controls()
        if self.nav != 2 and kind != 'ended':
            position = self.tree.yview()[0]
            rows = self.tree.get_children()
            first_visible = rows[min(round(position * len(rows)), len(rows) - 1)] if position and rows else None
            self.tree.insert('', 0, iid=event['id'], values=(event['local_time'], self.event_text(event)))
            if expired:
                self.tree.delete(expired['id'])
            if position == 0:
                self.tree.yview_moveto(0)
            elif first_visible and self.tree.exists(first_visible):
                self.tree.yview_moveto(self.tree.index(first_visible)/len(self.activity))
            if not self.tree.selection():
                self.select_activity()

    def close(self):
        self.closed=True
        self.root.withdraw()
        if self.session:
            self.session.stop(wait=True)
        self.root.destroy()


def self_test(artifacts):
    artifacts=Path(artifacts); artifacts.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as storage:
        root=tk.Tk(); app=HelperApp(root,storage)
        app.handle_event(dict(type='running',data={}))
        app.handle_event(dict(type='clicked',data={'count':12,'progress':'12/44','mod':'Modern Architecture Collection'}))
        app.handle_event(dict(type='waiting',data={}))
        app.busy=True
        app.demo=True
        checked=[]
        for language in ('ru','en'):
            for theme in ('dark','light'):
                app.language=language; app.theme=theme; app.render(); root.update()
                assert app.start_button.winfo_ismapped()
                assert app.details.winfo_ismapped()
                assert app.count==12 and app.progress_value=='12/44'
                capture_window(root,artifacts/f'vortex-{language}-{theme}.png')
                checked.append(f'{language}/{theme}')
        for nav in (1,2,0):
            app.select_nav(nav); root.update()
            if nav==2:
                assert len(app.flow_diagram.find_all())>=14
                capture_window(root,artifacts/'vortex-workflow.png')
        root.geometry('1000x740');root.update()
        for widget in (app.start_button,app.details,app.language_switch,app.theme_button):
            assert widget.winfo_ismapped()
            assert widget.winfo_rooty()+widget.winfo_height()<=root.winfo_rooty()+root.winfo_height()
        app.language_buttons['ru'].invoke();root.update()
        assert app.language=='ru'
        assert app.language_buttons['ru'].primary and not app.language_buttons['en'].primary
        old=app.theme;app.theme_button.invoke();root.update();assert app.theme!=old
        class FakeSession:
            def __init__(self,notify,**kwargs):self.notify=notify
            def start(self):self.notify(dict(type='running',data={}))
            def control(self,action):self.notify(dict(type='paused' if action=='pause' else 'running',data={}))
            def stop(self,wait=False):self.notify(dict(type='stopped',data={}));self.notify(dict(type='ended',data={}))
        def flush():
            while not app.events.empty():app.handle_event(app.events.get_nowait())
            root.update()
        app.session_factory=FakeSession;app.busy=False;app.render()
        app.start_button.invoke();flush();assert app.busy and app.state_key=='running'
        tree, start_button = app.tree, app.start_button
        selected = tree.get_children()[0]
        tree.selection_set(selected)
        for _ in range(30):
            app.handle_event(dict(type='waiting',data={}))
        root.update()
        assert app.tree is tree and app.start_button is start_button and tree.selection() == (selected,)
        app.pause_button.invoke();flush();assert app.state_key=='paused'
        app.pause_button.invoke();flush();assert app.state_key=='running'
        app.stop_button.invoke();flush();assert not app.busy and app.state_key=='stopped'
        app.close()
    return dict(ok=True,views=checked,languages=2,themes=2,minimum_layout=True,start_pause_resume_stop=True,language_theme_controls=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--artifacts',type=Path,default=Path('gui-artifacts'))
    parser.add_argument('--benchmark',type=Path)
    args=parser.parse_args()
    if args.self_test:
        result=self_test(args.artifacts)
        (args.artifacts/'self-test.json').write_text(json.dumps(result),encoding='utf-8')
        if __import__('sys').stdout is not None:print(json.dumps(result))
        return
    root=tk.Tk();app=HelperApp(root)
    if args.benchmark:benchmark(app,args.benchmark)
    else:root.mainloop()


if __name__=='__main__':
    main()
