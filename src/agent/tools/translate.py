from core.models import AgentAnswer
import argostranslate.package
import argostranslate.translate

async def install_package(from_code:str,to_code:str):
    available_packages=argostranslate.package.get_available_packages()
    package_to_install=next(
       (pkg for pkg in available_packages if pkg.from_code==from_code and pkg.to_code==to_code),
        None
    )
    if not package_to_install:
        raise ValueError(f"No package available for {from_code}->{to_code}")

    download_path=package_to_install.download()
    argostranslate.package.install_from_path(download_path)

def translate_payload(ans:AgentAnswer,from_code:str,to_code:str)->str:
    installed_languages=argostranslate.translate.get_installed_languages()
    from_lang=next((lang for lang in installed_languages if lang.code==from_code),None)
    to_lang=next((lang for lang in installed_languages if lang.code==to_code),None)

    if not from_lang or not to_lang:
        raise ValueError(f"Missing language model for {from_code}-> {to_code}")
       

    translation= from_lang.get_translation(to_lang)
    return translation.translate(ans.answer)