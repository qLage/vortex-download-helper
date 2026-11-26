# Проверка / Verification

## Русский

Проверены русский, английский и общий README: кодировка UTF-8, ссылки на локальные документы и команды запуска. Автоматические тесты проверяют обе версии всех сообщений помощника, подстановку параметров, русские названия модов, определение нового мода, стабильность, защиту от повторов и синтаксис PowerShell.

```powershell
powershell.exe -NoProfile -File .\tests\Test-Helper.ps1
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File .\Vortex-download-helper.ps1 -CheckOnly -Language ru
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File .\Vortex-download-helper.ps1 -CheckOnly -Language en
```

`-CheckOnly` не нажимает кнопки. Для этой проверки должен быть открыт Vortex. Если окна загрузки нет, ожидается сообщение о его отсутствии на выбранном языке. Язык помощника и язык Vortex — разные настройки: поддержка русских сообщений помощника не означает подтверждённую совместимость с переведёнными элементами Vortex. Проверенные названия элементов Vortex остаются английскими. Обновления интерфейса требуют повторной проверки под наблюдением.

## English

The Russian, English and combined README files are checked for UTF-8 integrity, local links and launch commands. Automated tests exercise both versions of every helper message, placeholder formatting, Russian mod titles, identity detection, debounce, deduplication and PowerShell syntax.

Run the commands above. `-CheckOnly` performs no clicks and requires a running Vortex window. With no download dialog, the expected result is a localized message reporting its absence. The helper language is independent of the Vortex UI language: Russian helper messages do not establish compatibility with translated Vortex controls. The verified Vortex control labels remain English. UI updates require another supervised compatibility check.
