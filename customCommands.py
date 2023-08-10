import deepl

async def translate(input: str) -> str:
    translator = deepl.Translator('c572d657-76eb-d396-4294-af47e48d2926:fx')
    result = translator.translate_text(input, target_lang='en-us')
    translated_text = result.text
    return str(translated_text)