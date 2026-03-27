$ErrorActionPreference = "Stop"

param(
    [string]$StartAt = "2026-03-23T12:00:00+09:00",
    [int]$Count = 7,
    [switch]$UseCurrentVideoFirst
)

Set-Location (Join-Path $PSScriptRoot "..")
$env:YOUTUBE_PRIVACY_STATUS = "private"

$results = @()
$start = [datetimeoffset]$StartAt

for ($i = 0; $i -lt $Count; $i++) {
    $publishAt = $start.AddDays($i).ToString("yyyy-MM-ddTHH:mm:sszzz")
    $env:YOUTUBE_PUBLISH_AT = $publishAt

    if ($i -eq 0 -and $UseCurrentVideoFirst) {
        Write-Host "[$($i + 1)/$Count] using current generated video for $publishAt"
    } else {
        Write-Host "[$($i + 1)/$Count] generating for $publishAt"
        python scripts/make_video.py
        if ($LASTEXITCODE -ne 0) {
            throw "make_video failed at item $($i + 1)"
        }
    }

    $meta = Get-Content .\out\metadata.json -Raw -Encoding utf8 | ConvertFrom-Json
    Write-Host "[$($i + 1)/$Count] uploading $($meta.source_title)"

    python scripts/upload_youtube.py
    if ($LASTEXITCODE -ne 0) {
        throw "upload_youtube failed at item $($i + 1)"
    }

    $status = Get-Content .\out\upload_status.json -Raw -Encoding utf8 | ConvertFrom-Json
    if ($status.status -eq "blocked") {
        throw "uploadLimitExceeded at item $($i + 1)"
    }
    if ($status.status -ne "uploaded") {
        throw "upload status was $($status.status) at item $($i + 1)"
    }

    python scripts/mark_posted.py
    if ($LASTEXITCODE -ne 0) {
        throw "mark_posted failed at item $($i + 1)"
    }

    $results += [pscustomobject]@{
        index = $i + 1
        publish_at = $publishAt
        source_title = $meta.source_title
        youtube_title = $meta.title
        video_id = $status.video_id
        url = "https://www.youtube.com/watch?v=$($status.video_id)"
    }
}

$results | ConvertTo-Json -Depth 3 | Set-Content .\out\scheduled_uploads_resume.json -Encoding utf8
$results | Format-Table -AutoSize
