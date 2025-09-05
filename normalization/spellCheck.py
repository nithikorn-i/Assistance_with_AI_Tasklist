import language_tool_python
from thaispellcheck import check as th_spellChecker

import re

en_tool = language_tool_python.LanguageTool('en-US')

def has_thai(text):
    return bool(re.search(r'[\u0E00-\u0E7F]', text))

def has_english(text):
    return bool(re.search(r'[a-zA-Z]', text))

def spell_Check(text):
    print("============================<Start Check spelling>==============================")

    if has_english(text):
        matches = en_tool.check(text)
        text = language_tool_python.utils.correct(text, matches)
        print("Check English spelling -> ", text)

    if has_thai(text):
        text = th_spellChecker(text, autocorrect=True)
        print("Check Thai spelling -> ", text)

    print("=============================<END Check spelling>===============================")
    
    return text
