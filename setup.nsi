;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"
  !define MUI_ICON "cacao_accounting_desktop\assets\icon.ico"
  !define MUI_HEADERIMAGE
  !define MUI_HEADERIMAGE_BITMAP "cacao_accounting_desktop\assets\CacaoAccounting.bmp"
  !define MUI_HEADERIMAGE_RIGHT
  !define MUI_WELCOMEFINISHPAGE_BITMAP "cacao_accounting_desktop\assets\CacaoAccountingRotate.bmp"
  !define MUI_UNWELCOMEFINISHPAGE_BITMAP "cacao_accounting_desktop\assets\CacaoAccountingRotate.bmp"

;--------------------------------
;General

  ;Name and file
  Name "Cacao Accounting Desktop"
  OutFile "CacaoAccountingSetup.exe"
  Unicode True

  ;Default installation folder
  InstallDir "$LOCALAPPDATA\CacaoAccountingDesktop"

  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\CacaoAccountingDesktop" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH
  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Cacao Accounting" SecDummy

  SetOutPath "$INSTDIR"

  ;ADD YOUR OWN FILES HERE
  File cacaoaccounting.exe
  File cacaoaccounting.pyw
  File LICENSE
  File README.md
  File /r pydist
  File /r cacao_accounting_desktop

  ;Store installation folder
  WriteRegStr HKCU "Software\CacaoAccountingDesktop" "" $INSTDIR

  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateShortcut "$DESKTOP\Cacao Accounting.lnk" "$INSTDIR\cacaoaccounting.exe"

  CreateDirectory "$SMPROGRAMS\Cacao Accounting"
  CreateShortcut "$SMPROGRAMS\Cacao Accounting\Cacao Accounting.lnk" "$INSTDIR\cacaoaccounting.exe"
  CreateShortcut "$SMPROGRAMS\Cacao Accounting\Uninstall.lnk" "$INSTDIR\Uninstall.exe"


SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...
  Delete "$INSTDIR\cacaoaccounting.exe"
  Delete "$INSTDIR\cacaoaccounting.pyw"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\README.md"
  Delete "$DESKTOP\Cacao Accounting.lnk"
  RMDir /r "$INSTDIR\pydist"

  Delete "$SMPROGRAMS\Cacao Accounting\Cacao Accounting.lnk"
  Delete "$SMPROGRAMS\Cacao Accounting\uninstall.lnk"
  RMDir /r "$SMPROGRAMS\Cacao Accounting"

  Delete "$INSTDIR\Uninstall.exe"

  RMDir /r "$INSTDIR"

  DeleteRegKey HKCU "Software\CacaoAccountingDesktop"

SectionEnd
