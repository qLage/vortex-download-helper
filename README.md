# Vortex Download Helper

**Русский / English**

[Русская инструкция](README.ru.md) · [English guide](README.en.md) · [Проверки / Verification](VERIFICATION.md)

## Русский

**Нажимает один раз при смене мода, даже если кнопка перемещается.**

[English documentation](README.en.md) · [Главная / Home](README.md) · Windows 10/11 · Windows PowerShell 5.1 · Без дополнительных пакетов

Помощник для кнопки **Download manually** в окне бесплатной загрузки коллекций Vortex. Находит окно и кнопку через Windows UI Automation. Координаты экрана и распознавание картинок не используются.

## Быстрый запуск

1. Скачайте репозиторий и распакуйте в отдельную папку.
2. Откройте Vortex, войдите в Nexus Mods и запустите загрузку коллекции.
3. Дважды нажмите `Start-Vortex-helper.cmd`.
4. Оставьте консоль открытой. **F8 — остановить**, **F9 — пауза/продолжение**. Закрытие консоли тоже останавливает помощник.

В консоли будет указан выбранный исполняемый файл. По умолчанию определяется единственное открытое окно Vortex, и его путь закрепляется на весь запуск. Если установок несколько, укажите нужную:

```powershell
.\Start-Vortex-helper.cmd -VortexPath "D:\Apps\Vortex\Vortex.exe"
```

Нужен существующий файл `Vortex.exe` и ровно одно соответствующее главное окно. Vortex и помощник должны работать с одинаковыми правами; обычно администратор не требуется.

## Язык

Консоль помощника работает на русском и английском. По умолчанию выбран русский; `-Language en` включает английский. Это язык помощника, а не изменение Vortex: проверенные названия его элементов остаются английскими.

```powershell
.\Start-Vortex-helper.cmd -Language ru
.\Start-Vortex-helper.cmd -Language en
```

## Проверка без нажатий

```powershell
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File .\Vortex-download-helper.ps1 -CheckOnly
```

`-CheckOnly` выводит найденный мод и счётчик либо сообщение, что подходящего окна нет. Ничего не нажимает и не запускает цикл. Обход политики выполнения действует только для этого процесса, постоянные настройки Windows не меняются. Проверяйте скрипты перед запуском.

## Как работает

1. Проверяет процесс Vortex и принадлежащее ему главное окно.
2. Находит `free-user-dl-dialog`, затем кнопку `download-mod-button` внутри него.
3. Требует активную кнопку с текстом **Download manually**, название мода и ровно один счётчик `текущий/всего` внутри этого окна.
4. Дважды наблюдает одинаковую комбинацию PID, времени запуска процесса, счётчика и названия.
5. Перед нажатием ещё раз проверяет текущее окно. Помечает мод обработанным **до** вызова кнопки, чтобы неопределённый результат не вызывал повторные нажатия.

Перемещение кнопки не меняет идентификатор. Смена названия мода или счётчика меняет его. Исчезнувшее или неоднозначное окно сбрасывает проверку стабильности. Каждая комбинация нажимается не более одного раза за запуск помощника. Именованный mutex защищает от двух экземпляров, включая исходную версию скрипта.

Опрос — раз в 750 мс. Если 20 минут нет нового успешного нажатия, помощник остановится, в том числе если один мод застрял на экране. Таймаут означает **проверьте Vortex**, а не «всё скачалось». Для другой коллекции или намеренного повтора запустите новую сессию помощника.

```powershell
.\Start-Vortex-helper.cmd -IdleMinutes 40 -PollMilliseconds 1000
powershell.exe -NoProfile -File .\tests\Test-Helper.ps1
```

Журнал: `%TEMP%\Vortex-download-helper.log`. В нём названия модов и время; проверьте перед публикацией. Помощник не обращается в сеть и не читает токены учётной записи.

## Совместимость и ограничения

Основа — англоязычное окно бесплатной загрузки Vortex **2.6.2**. Другие версии, переводы и изменения доступности интерфейса могут потребовать доработки. Если нужные элементы не найдены, нажатий не будет. Если свёрнутое окно не предоставляет элементы доступности, восстановите его.

Скрипт обслуживает только окно Vortex. На сайте ещё могут потребоваться выбор загрузки, ожидание, CAPTCHA, вход или подтверждение открытия ссылки в приложении. Помощник не нажимает Premium, Skip, Cancel и произвольные кнопки браузера, не снимает ограничения скорости, не обходит контроль доступа, не устанавливает и не развёртывает моды. Ошибка `invalid_grant` требует отдельного повторного входа.

## Если что-то не работает

| Симптом | Что сделать |
|---|---|
| Нет окна Vortex | Откройте программу или укажите `-VortexPath` |
| Подходящего диалога нет | Начните бесплатную загрузку коллекции и выполните `-CheckOnly` |
| Кнопка перемещается | Ничего менять не нужно: используется идентификатор элемента |
| Один мод не меняется | Повторные нажатия намеренно запрещены; проверьте ошибку загрузки или сети |
| Уже запущен помощник | Остановите прежнюю консоль клавишей F8 |
| Нет Invoke pattern | Остановитесь и укажите версию Vortex при сообщении о проблеме; координатного обхода нет |
| Бесконечное Installing… | Проверьте журнал Vortex: загрузка и установка — разные этапы |
| inZOI сообщает о разных дисках | Проверьте требования расширения: помощник не переносит данные и не исправляет расширения |

## Тесты и разработка

В `Helper.Core.psm1` — логика определения мода, стабильности и защиты от повторов. `tests/Test-Helper.ps1` проверяет смену названия и счётчика, неоднозначность, исчезновение диалога, перезапуск процесса, повторные события и синтаксис PowerShell. Тесты не нажимают реальные кнопки и ничего не скачивают. GitHub Actions выполняет их в Windows PowerShell 5.1.

Исходная версия использовалась с реальными окнами коллекций. После обновлений Vortex для упакованной версии нужна проверка `-CheckOnly` и одной загрузки под наблюдением: модульные тесты не гарантируют, что сторонний интерфейс не изменился.

Независимый проект, не связан с Nexus Mods. Соблюдайте правила сервиса и разрешения авторов модов. Моды и сторонние исполняемые файлы не включены. Лицензия MIT.

---

## English

**One deliberate click when the mod changes — even when the button moves.**

[Русский](README.ru.md) · [Bilingual home](README.md) · Windows 10/11 · Windows PowerShell 5.1 · No extra packages

A small helper for the **Download manually** button in Vortex's free collection-download dialog. It reads the dialog through Windows UI Automation and invokes the identified button. It does not aim at screen coordinates or rely on image matching.

## Quick start

1. Download and extract this repository into a folder.
2. Start Vortex normally, sign in to Nexus Mods and begin a collection download.
3. Double-click `Start-Vortex-helper.cmd`.
4. Keep the console open. **F8 stops** the helper; **F9 pauses/resumes** it. Closing the console also stops it.

The helper prints the target executable path. By default it discovers the single running Vortex window and pins its executable path. For multiple installations, supply the intended path:

```powershell
.\Start-Vortex-helper.cmd -VortexPath "D:\Apps\Vortex\Vortex.exe"
```

The target must be an existing `Vortex.exe`. Only one matching main window is accepted. Run Vortex and the helper at the same privilege level; administrator access is normally unnecessary.

## Language

The helper console supports Russian and English. The default is Russian; choose English with `-Language en`. This changes helper messages, not Vortex itself. The Vortex control labels remain the verified English labels.

```powershell
.\Start-Vortex-helper.cmd -Language en
.\Start-Vortex-helper.cmd -Language ru
```

## Check without clicking

```powershell
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File .\Vortex-download-helper.ps1 -CheckOnly
```

`-CheckOnly` prints the eligible mod/counter or reports that no eligible dialog is visible. It does not click or start the loop. The execution-policy bypass applies only to this process; it does not permanently change Windows settings. Review scripts before running them.

## How it decides

1. Resolve the target process and its own main window.
2. Find `free-user-dl-dialog`, then `download-mod-button` inside it.
3. Require the enabled button text **Download manually**, a mod title and exactly one `current/total` counter inside that dialog.
4. Compare an identity containing process ID, process start time, counter and mod title across two polls.
5. Read the current dialog again immediately before invoking. Reserve the identity **before** the click so an uncertain result never triggers an automatic retry.

Button movement does not change the identity. A changed mod title or counter does. Missing/ambiguous dialogs reset the stability check. Each identity is clicked at most once per helper run. A named mutex prevents duplicate instances, including the original helper version.

The default polling interval is 750 ms. The helper stops after 20 minutes without a successful new click, including when the same mod remains stuck. A timeout means **check Vortex**, not “all downloads completed.” Start a new helper session for a different collection or an intentional retry.

```powershell
.\Start-Vortex-helper.cmd -IdleMinutes 40 -PollMilliseconds 1000
powershell.exe -NoProfile -File .\tests\Test-Helper.ps1
```

Logs are stored in `%TEMP%\Vortex-download-helper.log`. They include local mod titles and timestamps; review before sharing. The helper performs no network requests and reads no account tokens.

## Compatibility and boundaries

Designed around the English free-download dialog observed in Vortex **2.6.2**. Other versions, translations or accessibility changes may require adjustments. The helper fails closed when required controls are missing. Keep Vortex restored if minimizing it hides its accessibility controls.

It handles only the Vortex dialog. Browser download pages, countdowns, CAPTCHA, account login and external-protocol confirmation may still need your attention. It does not press Premium, Skip, Cancel or arbitrary browser buttons, alter speed limits, bypass access controls, install mods, deploy files or repair collection dependencies. It cannot fix `invalid_grant`; reauthentication is a separate action.

## Troubleshooting

| Symptom | Action |
|---|---|
| No running Vortex window | Open Vortex first or provide `-VortexPath` |
| No eligible dialog | Start a free collection download; inspect `-CheckOnly` |
| Button moves | No change needed; UI Automation follows its control ID |
| Same mod stays visible | The helper intentionally avoids repeated clicks; inspect download/network errors |
| Helper already running | Stop the existing console with F8 before starting another |
| Invoke pattern unavailable | Stop and report the Vortex version; no coordinate fallback is used |
| Forever “Installing…” | Inspect the Vortex log; downloading and installing are separate stages |
| inZOI reports different drives | Review the extension's drive requirements; this helper does not move game data or patch extensions |

## Tests and development

`Helper.Core.psm1` contains deterministic identity/debounce/deduplication logic. `tests/Test-Helper.ps1` exercises title/counter changes, ambiguous counters, disappearance, process restarts, duplicate prevention and PowerShell syntax. These tests perform no live clicks or downloads. GitHub Actions runs them on Windows PowerShell 5.1.

The original helper was used with real collection dialogs; the packaged version's live end-to-end compatibility should be checked with `-CheckOnly` and one supervised download after Vortex updates. Unit tests cannot prove a third-party UI is unchanged.

Independent project, not affiliated with Nexus Mods. Follow Nexus Mods' rules and mod authors' permissions. No mods or third-party binaries are included. MIT license.
