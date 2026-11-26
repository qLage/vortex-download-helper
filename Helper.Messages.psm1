function Get-HelperMessage {
    param([ValidateSet('ru','en')][string]$Language='en', [string]$Key)
    $en = @{
        Title='Vortex download helper'
        Controls='F8: stop. F9: pause/resume. Closing this console also stops the helper.'
        Scope='Only the Download manually button in the Vortex collection dialog is used.'
        Boundary='No screen coordinates, browser clicks, Premium buttons or Skip buttons.'
        Target='Target: {0}'
        Windows='This helper requires Windows.'
        STA='Use Windows PowerShell with -STA. See README.'
        Open='Open exactly one Vortex instance, or specify -VortexPath.'
        Path='Expected a Vortex.exe path.'
        Absent='No eligible Vortex download dialog found.'
        Detected='Detected without clicking: {0} - {1}'
        Duplicate='The helper is already running.'
        Started='Helper started. F8 stops; F9 pauses. Waiting for a NEW mod.'
        Timeout='Idle timeout. Check Vortex for completion or errors; this does not confirm all files downloaded.'
        Paused='Paused (F9 to resume).'
        Resumed='Resumed.'
        Waiting='Waiting for the next Vortex download dialog. F8 stops the helper.'
        Same='Waiting for the mod to change: {0} - {1}'
        Invoke='Vortex does not expose the Invoke pattern for this button. No coordinate fallback is used.'
        Clicked='Clicked #{0}: {1} - {2}'
        Failed='Stopped safely: {0}'
        Stopped='Helper stopped. Download buttons pressed: {0}'
    }
    $ru = @{
        Title='Помощник загрузки Vortex'
        Controls='F8: остановить. F9: пауза/продолжение. Закрытие консоли останавливает помощник.'
        Scope='Используется только кнопка Download manually в окне загрузки коллекции Vortex.'
        Boundary='Координаты экрана, кнопки браузера, Premium и Skip не используются.'
        Target='Программа: {0}'
        Windows='Помощник работает только в Windows.'
        STA='Запустите Windows PowerShell с параметром -STA. См. инструкцию.'
        Open='Откройте ровно один экземпляр Vortex либо укажите -VortexPath.'
        Path='Требуется путь к файлу Vortex.exe.'
        Absent='Подходящее окно загрузки Vortex не найдено.'
        Detected='Найдено без нажатия: {0} - {1}'
        Duplicate='Помощник уже запущен.'
        Started='Помощник запущен. F8: остановить, F9: пауза. Ожидание НОВОГО мода.'
        Timeout='Время ожидания истекло. Проверьте завершение загрузки или ошибки в Vortex. Это не подтверждает, что все файлы скачаны.'
        Paused='Пауза. F9: продолжить.'
        Resumed='Работа продолжена.'
        Waiting='Ожидание следующего окна загрузки Vortex. F8: остановить.'
        Same='Ожидание смены мода: {0} - {1}'
        Invoke='Кнопка Vortex не предоставляет Invoke pattern. Нажатия по координатам не используются.'
        Clicked='Нажатие №{0}: {1} - {2}'
        Failed='Безопасная остановка: {0}'
        Stopped='Помощник остановлен. Нажатий кнопки загрузки: {0}'
    }
    $messages = if ($Language -eq 'ru') { $ru } else { $en }
    if (!$messages.ContainsKey($Key)) { throw ('Unknown message key: '+$Key) }
    return $messages[$Key]
}
Export-ModuleMember -Function Get-HelperMessage
