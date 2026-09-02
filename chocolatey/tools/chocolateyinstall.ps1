$ErrorActionPreference = 'Stop'

# LingoGeek ships an Inno Setup installer. The package downloads it from the GitHub release for the
# matching tag and verifies it against a SHA-256 checksum rather than embedding the binary. Because
# nothing is embedded, this package must NOT contain a tools\VERIFICATION.txt - that file is only
# for packages that ship a binary inside the nupkg.
$packageArgs = @{
  packageName    = 'lingogeek'
  fileType       = 'exe'
  url            = 'https://github.com/techygeekshome/LingoGeek/releases/download/v1.0.0/LingoGeekSetup.exe'
  checksum       = 'b09c7310bde7fe2cc945aa9fc146976fe7cb352e4fded826b24f5d50807c3249'
  checksumType   = 'sha256'
  silentArgs     = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-'
  validExitCodes = @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
