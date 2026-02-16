# Create Desktop Shortcut for BudgetTracker with Custom Icon
# Run this once: Right-click > Run with PowerShell

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\BudgetTracker.lnk")
$Shortcut.TargetPath = "code"
$Shortcut.Arguments = $ProjectDir
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Open BudgetTracker in VS Code"
$Shortcut.IconLocation = "$ProjectDir\BudgetTracker.ico,0"
$Shortcut.Save()

Write-Host ""
Write-Host "  BudgetTracker shortcut created on Desktop!" -ForegroundColor Green
Write-Host ""
Write-Host "  Features:" -ForegroundColor Cyan
Write-Host "    - Custom app icon (bar chart with dollar sign)"
Write-Host "    - Opens VS Code directly in BudgetTracker folder"
Write-Host ""
Write-Host "  Tip: Right-click the shortcut > 'Pin to taskbar' for quick access" -ForegroundColor Yellow
Write-Host ""
pause
