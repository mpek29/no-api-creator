# Capture the screen (or a single window) to a PNG.
#   -Out <path>        destination file (required)
#   -Window <hwnd>     capture only this window; default: all screens
#   -Scale <float>     downscale factor, keeps files small for reading (default 1.0)
param(
  [Parameter(Mandatory=$true)][string]$Out,
  [IntPtr]$Window = [IntPtr]::Zero,
  [double]$Scale = 1.0
)
Add-Type -AssemblyName System.Drawing, System.Windows.Forms

Add-Type @'
using System;
using System.Runtime.InteropServices;
public class NativeRect {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@ -ErrorAction SilentlyContinue

[void][NativeRect]::SetProcessDPIAware()

if ($Window -ne [IntPtr]::Zero) {
  $r = New-Object NativeRect+RECT
  [void][NativeRect]::GetWindowRect($Window, [ref]$r)
  $bounds = New-Object System.Drawing.Rectangle $r.Left, $r.Top, ($r.Right - $r.Left), ($r.Bottom - $r.Top)
} else {
  $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
}

$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$g.Dispose()

if ($Scale -ne 1.0) {
  $w = [int]($bounds.Width * $Scale); $h = [int]($bounds.Height * $Scale)
  $small = New-Object System.Drawing.Bitmap $w, $h
  $g2 = [System.Drawing.Graphics]::FromImage($small)
  $g2.InterpolationMode = 'HighQualityBicubic'
  $g2.DrawImage($bmp, 0, 0, $w, $h)
  $g2.Dispose(); $bmp.Dispose(); $bmp = $small
}

$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "$Out $($bounds.Width)x$($bounds.Height) origin=$($bounds.X),$($bounds.Y)"
