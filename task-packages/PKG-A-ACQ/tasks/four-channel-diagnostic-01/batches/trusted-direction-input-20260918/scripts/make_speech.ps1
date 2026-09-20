param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Refusing existing output directory' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $available = @($synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name })
    if ('Microsoft Huihui Desktop' -notin $available) { throw 'Microsoft Huihui Desktop is unavailable' }
    $synth.SelectVoice('Microsoft Huihui Desktop')
    $synth.Rate = 2
    $synth.Volume = 100
    $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(48000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
    $synth.SetOutputToWaveFile((Join-Path $OutputDirectory 'speech-original.wav'), $format)
    $text = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'speech-text.txt') -Raw -Encoding UTF8).Trim()
    $synth.Speak($text)
    $synth.SetOutputToNull()
    [ordered]@{ voice=$synth.Voice.Name; culture=$synth.Voice.Culture.Name; rate=2; volume=100; text=$text; sample_rate_hz=48000; channels=1; bits=16; engine='Windows System.Speech; generated locally, not a microphone recording' } | ConvertTo-Json | Out-File -LiteralPath (Join-Path $OutputDirectory 'speech-generation.json') -Encoding utf8
} finally { $synth.Dispose() }
