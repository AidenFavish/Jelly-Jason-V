import deepl
import secrets


async def translate(input: str) -> str:
    translator = deepl.Translator(secrets.tokenTranslate)
    result = translator.translate_text(input, target_lang='en-us')
    translated_text = result.text
    return str(translated_text)