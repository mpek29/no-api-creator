<#
Inspect the Windows UI Automation tree.

  uia.ps1 -List                       list top-level windows (title, process, hwnd)
  uia.ps1 -Hwnd <n> [-Depth 6]        dump the control tree under a window
  uia.ps1 -Process notepad [-Depth 6] dump by process name
  uia.ps1 -Foreground                 dump whatever is focused right now

Emits JSON: controlType, name, automationId, className, rect, patterns, value.
Elements carrying an automationId are what flows should address; rect is a
fallback for the ones that don't.
#>
param(
  [switch]$List,
  [switch]$Foreground,
  [int]$Hwnd = 0,
  [string]$Process,
  [int]$Depth = 6,
  [int]$MaxNodes = 1200
)

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win32 {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@ -ErrorAction SilentlyContinue
[void][Win32]::SetProcessDPIAware()

$auto = [System.Windows.Automation.AutomationElement]

if ($List) {
  $root = $auto::RootElement
  $cond = New-Object System.Windows.Automation.PropertyCondition($auto::ControlTypeProperty, [System.Windows.Automation.ControlType]::Window)
  $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
  $out = @()
  foreach ($w in $wins) {
    $name = $w.Current.Name
    if ([string]::IsNullOrWhiteSpace($name)) { continue }
    $p = $null
    try { $p = (Get-Process -Id $w.Current.ProcessId -ErrorAction Stop).ProcessName } catch { $p = "?" }
    $r = $w.Current.BoundingRectangle
    $out += [pscustomobject]@{
      title   = $name
      process = $p
      pid     = $w.Current.ProcessId
      hwnd    = [int]$w.Current.NativeWindowHandle
      rect    = @([int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height)
    }
  }
  $out | ConvertTo-Json -Depth 4
  return
}

# --- resolve the root element to walk -------------------------------------
$target = $null
if ($Foreground) {
  $target = $auto::FromHandle([Win32]::GetForegroundWindow())
} elseif ($Hwnd -ne 0) {
  $target = $auto::FromHandle([IntPtr]$Hwnd)
} elseif ($Process) {
  $procs = @(Get-Process -Name $Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 })
  if ($procs.Count -eq 0) { Write-Error "No window found for process '$Process'"; exit 1 }
  $target = $auto::FromHandle($procs[0].MainWindowHandle)
} else {
  Write-Error "Pass -List, -Foreground, -Hwnd or -Process"; exit 1
}
if ($null -eq $target) { Write-Error "Could not resolve target window"; exit 1 }

$script:count = 0
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker

# Offscreen/virtualised elements report an infinite rect. Collapse those to zeros
# rather than letting the int cast blow up the whole walk.
function ConvertTo-Rect($r) {
  $v = @($r.X, $r.Y, $r.Width, $r.Height)
  $o = @()
  foreach ($n in $v) {
    if ([double]::IsInfinity($n) -or [double]::IsNaN($n)) { $o += 0 } else { $o += [int]$n }
  }
  return ,$o
}

function Read-Node($el, $depth) {
  if ($script:count -ge $MaxNodes) { return $null }
  $script:count++
  $c = $el.Current
  $r = $c.BoundingRectangle

  # which interaction patterns this element supports -> tells a flow what it can do
  $patterns = @()
  foreach ($p in $el.GetSupportedPatterns()) { $patterns += $p.ProgrammaticName -replace 'Identifiers\.|Pattern$','' }

  $value = $null
  try {
    $vp = $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    if ($vp) { $value = $vp.Current.Value }
  } catch {}

  $node = [ordered]@{
    controlType  = $c.ControlType.ProgrammaticName -replace 'ControlType\.',''
    name         = $c.Name
    automationId = $c.AutomationId
    className    = $c.ClassName
    rect         = (ConvertTo-Rect $r)
    enabled      = $c.IsEnabled
    offscreen    = $c.IsOffscreen
  }
  if ($value)            { $node.value = $value }
  if ($patterns.Count)   { $node.patterns = $patterns }

  if ($depth -gt 0) {
    $kids = @()
    $child = $walker.GetFirstChild($el)
    while ($null -ne $child -and $script:count -lt $MaxNodes) {
      $k = Read-Node $child ($depth - 1)
      if ($k) { $kids += $k }
      $child = $walker.GetNextSibling($child)
    }
    if ($kids.Count) { $node.children = $kids }
  }
  return $node
}

(Read-Node $target $Depth) | ConvertTo-Json -Depth 40 -Compress:$false
