# Проверка / Verification

## Русский

Версия 0.2.1 проверена из исходников и как portable EXE: русский/английский, тёмная/светлая тема, минимальный размер, переключатели языка/темы, кнопки запуска, паузы, продолжения и остановки, журнал. Самопроверка GUI использует имитацию сеанса и не нажимает реальные кнопки Vortex.

Отдельный интеграционный тест создаёт собственное WPF-окно `Vortex.exe` с заданными AutomationId. Проверенный путь привязан только к временному тестовому файлу. Настоящий PowerShell-движок вызывает его кнопки. Проверены первый клик, перемещение без дубля, пауза, следующий мод после продолжения, отсутствие нажатий после остановки и режим без нажатий. Настоящие моды не скачиваются, пользовательский Vortex не изменяется.

```powershell
powershell.exe -NoProfile -File .\tests\Test-Helper.ps1
python -m unittest discover -s tests -v
python gui.py --self-test --artifacts gui-artifacts
python gui.py --benchmark gui-artifacts/idle.json
$env:VORTEX_UI_TEST='1'
python tests/test_windows_integration.py
```

Интеграционный тест требует интерактивной Windows-сессии, стандартного .NET Framework и свободного mutex помощника. Без `VORTEX_UI_TEST=1` он пропускается. После обновления Vortex повторно проверьте реальное окно через «Проверить без нажатий»: тестовый интерфейс не доказывает неизменность сторонней программы. Проверенные элементы Vortex 2.6.2 имеют английские названия.

## English

Version 0.2.1 was checked from source and as a portable EXE: Russian/English, dark/light themes, minimum window size, actual language/theme controls, start/pause/resume/stop buttons and the activity log. GUI self-test uses a simulated session.

The separate integration test creates its own temporary WPF `Vortex.exe` fixture with explicit AutomationIds. The executable path is pinned to that fixture. The real PowerShell engine invokes only the fixture's buttons. It verifies the first click, movement without duplication, pause, advancing after resume, no clicks after stop and check-only behavior. No real mods are downloaded and the user's Vortex is not modified.

Run the commands above. The native integration test requires an interactive Windows session, standard .NET Framework and an available helper mutex. Without explicit `VORTEX_UI_TEST=1` it is skipped. Recheck real Vortex after UI updates: a fixture cannot establish third-party compatibility. Verified Vortex 2.6.2 controls have English labels.
