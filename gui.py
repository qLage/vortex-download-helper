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

from desktop_ui import DesktopApp, benchmark, button, card, capture_window, label, put_text, text_area
from helper_runtime import HelperSession

WORDS = {
 'ru': dict(local='Локальное управление. Без доступа к аккаунту.', workspace='ПОМОЩНИК ЗАГРУЗКИ', light='Светлая тема', dark='Тёмная тема',
    overview='Управление', activity='Журнал', help='Как это работает', title='Vortex Helper',
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
    help_title='Справка',
    help_body='1. Откройте Vortex и начните загрузку коллекции.\n\n2. Нажмите «Проверить без нажатий», чтобы проверить доступность нужного окна.\n\n3. Запустите помощник. Кнопка нажимается только после двух стабильных наблюдений одного мода и повторной проверки прямо перед нажатием.\n\n4. Остановите помощник после завершения. Его остановка по таймауту не означает, что все файлы скачались.\n\nСтраницы браузера, CAPTCHA, вход в аккаунт и ошибки установки требуют отдельного внимания. Помощник не изменяет файлы модов и не управляет учётной записью.\n\nПроверенные элементы интерфейса Vortex имеют английские названия. Переключение языка здесь меняет язык помощника.\n\nЖурнал этого окна хранится в памяти, настройки языка и темы — локально. Консольный помощник также ведёт свой журнал в папке TEMP.',
    demo='Пример работы · вымышленные данные'),
 'en': dict(local='Local controls. No account access.', workspace='DOWNLOAD ASSISTANT', light='Light theme', dark='Dark theme',
    overview='Controls', activity='Activity', help='How it works', title='Vortex Helper',
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
    help_title='Help',
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
        self.demo = False
        super().__init__(root, 'VortexDownloadHelper', WORDS, storage, purple=True)
        self.vortex_path = self.settings.get('vortex_path', '')
        self.render()

    def render(self):
        parent = self.shell('Vortex Helper', '', [self.t('overview'), self.t('activity'), self.t('help')])
        if self.nav == 2:
            label(parent, self.t('help_title'), self.p, 23, True).pack(anchor='w', pady=(0, 20))
            panel=card(parent,self.p); panel.pack(fill='both', expand=True)
            put_text(text_area(panel,self.p,height=20,expand=True), self.t('help_body'))
            return
        label(parent, self.t('title'), self.p, 23, True).pack(anchor='w')
        tk.Frame(parent,bg=self.p['bg'],height=16).pack()
        if self.nav == 0:
            hero=card(parent,self.p,padx=22,pady=14); hero.pack(fill='x',pady=(0,16))
            status=label(hero,'●  '+self.t(self.state_key),self.p,14,True)
            status.configure(fg=self.p['red'] if self.state_key == 'failed' else self.p['accent'])
            status.pack(anchor='w')
            label(hero,self.t('intro'),self.p,10,muted=True).pack(anchor='w',pady=(8,12))
            controls=tk.Frame(hero,bg=self.p['card']); controls.pack(fill='x')
            self.start_button=button(controls,self.t('start'),lambda:self.start(False),self.p,True)
            self.start_button.configure(state='disabled' if self.busy else 'normal'); self.start_button.pack(side='left')
            self.pause_button=button(controls,self.t('resume' if self.state_key=='paused' else 'pause'),self.pause,self.p)
            self.pause_button.configure(state='normal' if self.busy and self.state_key != 'checking' else 'disabled'); self.pause_button.pack(side='left',padx=10)
            self.stop_button=button(controls,self.t('stop'),self.cancel,self.p)
            self.stop_button.configure(state='normal' if self.busy else 'disabled'); self.stop_button.pack(side='left')
            check=button(controls,self.t('check'),lambda:self.start(True),self.p)
            check.configure(state='disabled' if self.busy else 'normal'); check.pack(side='right')
            pathrow=tk.Frame(hero,bg=self.p['card']); pathrow.pack(fill='x',pady=(12,0))
            label(pathrow,self.t('target'),self.p,9,muted=True).pack(side='left')
            choose=button(pathrow,self.t('browse'),self.browse,self.p)
            choose.configure(state='disabled' if self.busy else 'normal',pady=5); choose.pack(side='right')
            self.path_label=label(pathrow,self.vortex_path or self.t('automatic'),self.p,9,muted=True,wraplength=450)
            self.path_label.pack(side='right',padx=12)
            self.metrics(parent,[(self.t('clicks'),self.count,self.t('clicks_hint')),
                                 (self.t('progress'),self.progress_value,self.t('progress_hint'))])
            current=card(parent,self.p,padx=18,pady=10); current.pack(fill='x',pady=(0,16))
            label(current,self.t('current'),self.p,9,muted=True).pack(anchor='w')
            label(current,self.mod or self.t('current_hint'),self.p,12,True,wraplength=810).pack(anchor='w',pady=(5,0))
        foot=self.t('demo') if self.demo else self.t('quiet')
        label(parent,foot,self.p,9,muted=True,wraplength=850).pack(side='bottom',anchor='w',pady=(13,0))
        panel=card(parent,self.p); panel.pack(fill='both',expand=True)
        label(panel,self.t('recent'),self.p,11,True).pack(anchor='w',padx=16,pady=13)
        self.details=text_area(panel,self.p,height=2 if self.nav==0 else 5)
        self.tree=self.table(panel,[('time',self.t('time'),90),('event',self.t('event'),700)],heights=2 if self.nav==0 else 13)
        self.tree.bind('<<TreeviewSelect>>',self.select_activity)
        self.refresh_activity()

    def browse(self):
        selected=filedialog.askopenfilename(parent=self.root,title=self.t('choose'),filetypes=[('Vortex','Vortex.exe')])
        if selected:
            self.vortex_path=selected; self.settings['vortex_path']=selected; self.save_settings(); self.render()

    def start(self, check_only=False):
        if self.busy:
            return
        self.busy=True; self.demo=False; self.state_key='checking' if check_only else 'running'
        if not check_only:
            self.count=0; self.progress_value='—'; self.mod=''
        self.session=self.session_factory(self.events.put, language=self.language, vortex_path=self.vortex_path, check_only=check_only)
        self.render(); self.session.start()

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

    def refresh_activity(self):
        if not hasattr(self,'tree') or not self.tree.winfo_exists():
            return
        self.tree.delete(*self.tree.get_children())
        for index,event in enumerate(reversed(self.activity)):
            self.tree.insert('','end',iid=str(index),values=(event['local_time'],self.event_text(event)))
        put_text(self.details,self.event_text(self.activity[-1]) if self.activity else self.t('none'))

    def select_activity(self,_=None):
        if self.tree.selection():
            event=list(reversed(self.activity))[int(self.tree.selection()[0])]
            put_text(self.details,self.event_text(event))

    def handle_event(self,event):
        kind=event['type']; data=event.get('data') or {}
        event=dict(event,local_time=datetime.now().strftime('%H:%M:%S'))
        self.activity.append(event); self.activity=self.activity[-200:]
        if kind in ('clicked','detected'):
            self.mod=str(data.get('mod','')); self.progress_value=str(data.get('progress','—'))
            if kind=='clicked': self.count=int(data.get('count',self.count))
        if kind in ('running','paused'):
            self.state_key=kind
        elif kind=='error' or kind=='duplicate':
            self.state_key='failed'
        elif kind in ('stopped','timeout'):
            self.state_key='stopped'
        elif kind=='ended':
            self.busy=False
            if self.state_key not in ('failed','idle'): self.state_key='stopped'
        if kind=='absent' and self.state_key=='checking':
            self.state_key='idle'
        if kind=='target':
            self.resolved_path=data.get('path','')
        self.render()

    def close(self):
        self.closed=True
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
        root.geometry('1000x740');root.update()
        for widget in (app.start_button,app.details,app.language_box,app.theme_button):
            assert widget.winfo_ismapped()
            assert widget.winfo_rooty()+widget.winfo_height()<=root.winfo_rooty()+root.winfo_height()
        app.language_box.set('Русский');app.language_box.event_generate('<<ComboboxSelected>>');root.update()
        assert app.language=='ru'
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
