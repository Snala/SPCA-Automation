$ProjectDirectory = "C:\Users\Ohana\PycharmProjects\SPCA-Automation"
New-Item -ItemType Directory -Force -Path $ProjectDirectory\inst\
Set-Location -Path $ProjectDirectory
venv\Scripts\pyinstaller.exe --noconsole .\SPCACheckout\Checkout.py -y

Start-Process -FilePath "C:\Program Files (x86)\NSIS\makensis.exe" -Wait -Verb "runAs" -WindowStyle "hidden" -ArgumentList "$($ProjectDirectory)\Checkout_installer.nsi"
