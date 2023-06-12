if "%CI%" == "true" (
    set curver=%GITHUB_REF_NAME%
) else (
    if not "%1" == "" (
        set curver=%1
    ) else (
        echo "Provide a valid version number"
        exit
    )
)

python3.11 prepare_build_info.py
python3.11 -m nuitka --standalone --onefile --prefer-source-code --assume-yes-for-downloads --remove-output --lto=yes --company-name=Cyrmax --product-name=Sku_Updater --file-version=%curver% --product-version=%curver% --file-description="A console program to update your installation of Sku for WoW Classic" --copyright="Made by Cyrmax in 2022. MIT license" sku-updater.py
