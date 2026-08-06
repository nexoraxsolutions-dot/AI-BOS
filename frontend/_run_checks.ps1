$ErrorActionPreference = "Continue"
Set-Location "c:\Users\HUSSAIN\OneDrive\Desktop\AI Business O.S\frontend"
$out = ".\_results.txt"
"=== ENV CHECK ===" | Out-File -FilePath $out -Encoding utf8
"PWD: $(Get-Location)" | Out-File -FilePath $out -Append -Encoding utf8
node --version *>> $out
npm --version *>> $out
"=== TSC ===" | Out-File -FilePath $out -Append -Encoding utf8
npx tsc --noEmit *>> $out
"=== TSC EXIT: $LASTEXITCODE ===" | Out-File -FilePath $out -Append -Encoding utf8
"=== JEST (LoggingConfiguration) ===" | Out-File -FilePath $out -Append -Encoding utf8
npx jest __tests__/LoggingConfiguration.test.tsx --ci *>> $out
"=== JEST EXIT: $LASTEXITCODE ===" | Out-File -FilePath $out -Append -Encoding utf8
"ALL DONE" | Out-File -FilePath $out -Append -Encoding utf8
