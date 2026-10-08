# Hinnat: the organisation key window on Windows (scripts/common.py ask_key).
#
# Fed to "powershell -NoProfile -NonInteractive -STA -Command -" on stdin, as
# plain readable text: no -EncodedCommand (an anti-virus red flag) and no
# -File (a company's execution policy would block an unsigned script file).
# Every text comes from an environment variable, so this file stays ASCII
# and no quoting of the message can break it:
#   HINNAT_DLG_TITLE, HINNAT_DLG_MSG, HINNAT_DLG_LATER  window texts
#   HINNAT_DLG_WAIT   seconds before it gives up, as "Myohemmin" would
#   HINNAT_DLG_TEST   release smoke test only: type this and press OK
# It prints the key to stdout and nothing else. One statement per line:
# "-Command -" runs stdin line by line.
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$f = New-Object Windows.Forms.Form
$f.Text = $env:HINNAT_DLG_TITLE
$f.Size = New-Object Drawing.Size(470, 200)
$f.StartPosition = 'CenterScreen'
$f.TopMost = $true
$f.FormBorderStyle = 'FixedDialog'
$f.MaximizeBox = $false
$l = New-Object Windows.Forms.Label
$l.Text = $env:HINNAT_DLG_MSG
$l.Location = New-Object Drawing.Point(14, 14)
$l.Size = New-Object Drawing.Size(430, 44)
$t = New-Object Windows.Forms.TextBox
$t.Location = New-Object Drawing.Point(14, 64)
$t.Size = New-Object Drawing.Size(430, 24)
$t.UseSystemPasswordChar = $true
$b = New-Object Windows.Forms.Button
$b.Text = 'OK'
$b.Location = New-Object Drawing.Point(354, 104)
$b.DialogResult = 'OK'
$c = New-Object Windows.Forms.Button
$c.Text = $env:HINNAT_DLG_LATER
$c.Location = New-Object Drawing.Point(260, 104)
$c.DialogResult = 'Cancel'
$f.AcceptButton = $b
$f.CancelButton = $c
$f.Controls.AddRange(@($l, $t, $b, $c))
$tm = New-Object Windows.Forms.Timer
$tm.Interval = 1000 * [Math]::Max(1, [int]$env:HINNAT_DLG_WAIT)
if ($env:HINNAT_DLG_TEST) { $tm.Interval = 1500 }
$tm.Add_Tick({ $tm.Stop(); if ($env:HINNAT_DLG_TEST) { $t.Text = $env:HINNAT_DLG_TEST; $f.DialogResult = 'OK' } else { $f.DialogResult = 'Cancel' }; $f.Close() })
$f.Add_Shown({ $f.Activate(); [void]$t.Focus(); $tm.Start() })
if ($f.ShowDialog() -eq 'OK') { [Console]::Out.Write($t.Text.Trim()) }
