import deepl
import secrets


async def translate(input):
    translator = deepl.Translator(secrets.tokenTranslate)
    result = translator.translate_text(str(input), target_lang='en-us')
    translated_text = result.text
    return str(translated_text)