$studentsPath = Join-Path (Get-Location) 'students'
Get-ChildItem -Path $studentsPath -Directory | ForEach-Object {
    $dir = $_.FullName
    $files = Get-ChildItem -Path $dir -File -Recurse -ErrorAction SilentlyContinue
    if (-not $files) {
        $readme = Join-Path $dir 'README.md'
        if (-not (Test-Path $readme)) {
            'Student directory placeholder' | Out-File -FilePath $readme -Encoding utf8
        }
    }
}
Write-Output 'Done creating README files.'
