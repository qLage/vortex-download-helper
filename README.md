# Vortex Download Helper

**One deliberate click when the mod changes — even when the button moves.**

[Русская документация](README.ru.md) · Windows 10/11 · Windows PowerShell 5.1 · No extra packages

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
