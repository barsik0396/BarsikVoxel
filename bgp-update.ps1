$wc = New-Object System.Net.WebClient

$url = "https://raw.githubusercontent.com/barsik0396/BGP/main/lastversion.txt?ts=$(Get-Date -UFormat %s)"


$wc.CachePolicy = New-Object System.Net.Cache.RequestCachePolicy `
    ([System.Net.Cache.RequestCacheLevel]::NoCacheNoStore)

$wc.DownloadFile($url, "bgp_lastversion.txt")





Get-Content 'bgp_lastversion.txt' -Encoding UTF8 | Set-Content 'bgp_lastversion_2.txt' -Encoding UTF8