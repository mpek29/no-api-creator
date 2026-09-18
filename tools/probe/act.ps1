<#
Act on a window through UI Automation, and read values back out.

  act.ps1 -Hwnd <n> -Find <automationId>            locate an element, print its state
  act.ps1 -Hwnd <n> -Invoke <automationId>          press a button WITHOUT moving the mouse
  act.ps1 -Hwnd <n> -SetValue <id> -Text "abc"      fill a field directly
  act.ps1 -Hwnd <n> -Get <automationId>             read an element's text/value
  act.ps1 -Click <x> <y>                            physical mouse click (last resort)
  act.ps1 -SendKeys "^s"                            keystrokes to the focused window

Invoke/SetValue are preferred: they drive the app through its own accessibility
layer, so the physical cursor never moves and the machine stays usable.
#>
param(
  [int]$Hwnd = 0,
  [string]$Find, [string]$Invoke, [string]$SetValue, [string]$Get,
  [string]$Text,
  [int[]]$Click,
  [string]$SendKeys,
  [switch]$ByName
)

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Input {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, int e);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public static void LeftClick(int x, int y) {
    SetCursorPos(x, y);
    System.Threading.Thread.Sleep(40);
    mouse_event(0x02, 0, 0, 0, 0);  // LEFTDOWN
    mouse_event(0x04, 0, 0, 0, 0);  // LEFTUP
  }
}
'@ -ErrorAction SilentlyContinue
[void][Input]::SetProcessDPIAware()

if ($Click) { [Input]::LeftClick($Click[0], $Click[1]); Write-Output "clicked $($Click[0]),$($Click[1])"; return }
if ($SendKeys) { [System.Windows.Forms.SendKeys]::SendWait($SendKeys); Write-Output "sent"; return }

$auto = [System.Windows.Automation.AutomationElement]
if ($Hwnd -eq 0) { Write-Error "-Hwnd required"; exit 1 }
$root = $auto::FromHandle([IntPtr]$Hwnd)
if ($null -eq $root) { Write-Error "bad hwnd"; exit 1 }

$id = if ($Find) { $Find } elseif ($Invoke) { $Invoke } elseif ($SetValue) { $SetValue } else { $Get }
if (-not $id) { Write-Error "Pass -Find/-Invoke/-SetValue/-Get"; exit 1 }

$prop = if ($ByName) { $auto::NameProperty } else { $auto::AutomationIdProperty }
$cond = New-Object System.Windows.Automation.PropertyCondition($prop, $id)
$el = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
if ($null -eq $el) { Write-Error "element '$id' not found"; exit 1 }

function Read-Value($e) {
  try { $vp = $e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
        if ($vp) { return $vp.Current.Value } } catch {}
  try { $tp = $e.GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern)
        if ($tp) { return $tp.DocumentRange.GetText(4096) } } catch {}
  return $e.Current.Name
}

if ($Invoke) {
  $ip = $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
  $ip.Invoke(); Write-Output "invoked $id"; return
}
if ($SetValue) {
  $vp = $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
  $vp.SetValue($Text); Write-Output "set $id = $Text"; return
}
if ($Get) { Write-Output (Read-Value $el); return }

$r = $el.Current.BoundingRectangle
[pscustomobject]@{
  name = $el.Current.Name; automationId = $el.Current.AutomationId
  controlType = $el.Current.ControlType.ProgrammaticName -replace 'ControlType\.',''
  rect = @([int]$r.X,[int]$r.Y,[int]$r.Width,[int]$r.Height)
  value = (Read-Value $el)
} | ConvertTo-Json -Depth 3
