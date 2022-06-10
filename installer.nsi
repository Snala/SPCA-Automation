; Turn off old selected section
; 12 06 2005: Luis Wong
; Template to generate an installer
; Especially for the generation of EasyPlayer installers
; Trimedia Interactive Projects

; -------------------------------
; Start

  !define NAME "SPCANN - ClinicPaperwork"
  !define MUI_FILE "ClinicPaperwork"
  !define VERSION "1.0"
  !define MUI_BRANDINGTEXT "ClinicPaperwork"
  !define SLUG "${NAME} v${VERSION}"
  !define ProjectDir "C:\Users\Ohana\PycharmProjects\SPCA-Automation"
  !define InputDir "${ProjectDir}\dist\ClinicPaperwork"
  CRCCheck On

  ; We should test if we must use an absolute path
  !include "${NSISDIR}\Contrib\Modern UI\System.nsh"


;---------------------------------
;General

  OutFile "${ProjectDir}\inst\Install ClinicPaperwork ${VERSION}.exe"
  ShowInstDetails "hide"
  ShowUninstDetails "hide"
  Name "${NAME}"
  ;SetCompressor "bzip2"

  ;!define MUI_ICON "icon.ico"
  ;!define MUI_UNICON "icon.ico"
  ;!define MUI_SPECIALBITMAP "Bitmap.bmp"


;--------------------------------
;Folder selection page

  InstallDir "$PROGRAMFILES\${NAME}"


;--------------------------------
;Modern UI Configuration

  !define MUI_WELCOMEPAGE
  ;!define MUI_LICENSEPAGE
  !define MUI_DIRECTORYPAGE
  !define MUI_ABORTWARNING
  !define MUI_UNINSTALLER
  !define MUI_UNCONFIRMPAGE
  !define MUI_FINISHPAGE


;--------------------------------
;Language

  !insertmacro MUI_LANGUAGE "English"


;--------------------------------
;Modern UI System

  ;!insertmacro MUI_SYSTEM


;--------------------------------
;Data

  ;LicenseData "Read_me.txt"


;--------------------------------
;Installer Sections
Section "install"

;Add files
  SetOutPath "$INSTDIR"

  File "${ProjectDir}\README.md"
  File "${InputDir}\${MUI_FILE}.exe"
  file /r ${InputDir}\*

;create desktop shortcut
  CreateShortCut "$DESKTOP\${NAME}.lnk" "$INSTDIR\${MUI_FILE}.exe" ""

;create start-menu items
  CreateDirectory "$SMPROGRAMS\${NAME}"
  CreateShortCut "$SMPROGRAMS\${NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\${NAME}\${NAME}.lnk" "$INSTDIR\${MUI_FILE}.exe" "" "$INSTDIR\${MUI_FILE}.exe" 0

;write uninstall information to the registry
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "DisplayName" "${NAME} (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd


;--------------------------------
;Uninstaller Section
Section "Uninstall"

;Delete Files
  RMDir /r "$INSTDIR\*.*"

;Remove the installation directory
  RMDir "$INSTDIR"

;Delete Start Menu Shortcuts
  Delete "$DESKTOP\${NAME}.lnk"
  Delete "$SMPROGRAMS\${NAME}\*.*"
  RmDir  "$SMPROGRAMS\${NAME}"

;Delete Uninstaller And Unistall Registry Entries
  DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\${NAME}"
  DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}"

SectionEnd


;--------------------------------
;MessageBox Section


;Function that calls a messagebox when installation finished correctly
Function .onInstSuccess
  MessageBox MB_OK "You have successfully installed ${NAME}."
FunctionEnd

Function un.onUninstSuccess
  MessageBox MB_OK "You have successfully uninstalled ${NAME}."
FunctionEnd


;eof