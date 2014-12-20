import bpy
from script_auto_complete.text_editor_utils import *
from script_auto_complete.expression_utils import *
        
        
class ExtendWordOperator:
    def __init__(self, target_word, additional_data = None):
        self.target_word = target_word
        self.display_name = target_word
        self.additional_data = additional_data
        self.align = "LEFT"
        
    def execute(self, text_block):
        text_block.replace_current_word(self.target_word)


class InsertTextOperator:
    def __init__(self, name, text):
        self.display_name = name
        self.insert_text = text
        self.align = "CENTER"
        
    def execute(self, text_block):
        text_block.insert(self.insert_text)
        
        
class DynamicSnippetOperator:
    def __init__(self, name, insert_snippet_function):
        self.display_name = name
        self.insert_snippet_function = insert_snippet_function
        self.align = "CENTER"
        
    def execute(self, text_block):
        self.insert_snippet_function(text_block)       