import bpy, re
from operator import attrgetter
from .. import expression_utils as exp
from .. text_operators import *
from .. text_editor_utils import *

def get_dynamic_snippets_operators(text_block):
    operators = []
    for snippet in snippets:
        match = text_block.search_pattern_in_current_line(snippet.expression)
        if match:
            for name in snippet.get_snippet_names(match):
                operators.append(DynamicSnippetOperator(name, insert_dynamic_snippet, (snippet, name)))
    return operators
    
def insert_dynamic_snippet(text_block, snippet_and_name):
    snippet, name = snippet_and_name
    match = text_block.search_pattern_in_current_line(snippet.expression)
    if match:
        snippet.insert_snippet(text_block, match, name)
    
def replace_match(text_block, match, text):
    text_block.select_match_in_current_line(match)
    text_block.insert(text)
    
def create_snippet_objects():
    global snippets
    snippets = [
        NewClassSnippet(),
        NewPropertySnippet(),
        SetupKeymapsSnippet(),
        KeymapItemSnippet() ]

class NewClassSnippet:
    expression = "=(p|o|m)\|(\w+)"
    
    def insert_snippet(self, text_block, match, name):
        replace_match(text_block, match, self.get_snippet_text(match))
    
    def get_snippet_names(self, match):
        return ["New " + self.get_type(match) + " '" + self.get_name(match) + "'"]
        
    def get_snippet_text(self, match):
        return "class " + self.get_name(match) + "(bpy.types." + self.get_type(match) + ")"
    
    def get_name(self, match):
        return match.group(2)
    def get_type(self, match):
        t = match.group(1)
        if t == "p": return "Panel"
        if t == "o": return "Operator"
        if t == "m": return "Menu"
        
class NewPropertySnippet:
    expression = "=([A-Z]\w+)\|(\w+)\|(.*)"
    
    def insert_snippet(self, text_block, match, name):
        property_type = self.get_property_type(match)
        if property_type is None: return
        property_definition = self.get_property_definition(match)
        replace_match(text_block, match, property_definition)
    
    def get_snippet_names(self, match):
        property_type = self.get_property_type(match)
        if property_type is not None:
            return ["New " + property_type]
        return ["Property Definition ..."]
        
    def get_property_definition(self, match):
        bpy_type = self.get_bpy_type(match)
        name = self.get_property_name(match)
        property_type = self.get_property_type(match)
        default = self.get_default(match)
        
        return "bpy.types." + bpy_type + "." + name + " = bpy.props." + property_type + "(name = \"" + name + "\", default = " + default + ")"
    
    def get_property_type(self, match):
        default = self.get_default(match)
        tests = [
            ("[0-9]+\.[0-9]+", "FloatProperty"),
            ("[0-9]+", "IntProperty"),
            ("(\"|\').*(\"|\')", "StringProperty") ]
            
        for exp, property_type in tests:
            if re.match(exp, default):
                return property_type
        return None
    
    def get_bpy_type(self, match):
        return match.group(1)
        
    def get_property_name(self, match):
        return match.group(2)
        
    def get_default(self, match):
        return match.group(3)
        
        
class SetupKeymapsSnippet:
    expression = "=keymaps"
    
    keymap_registration_code = '''addon_keymaps = []
def register_keymaps():
    global addon_keymaps
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name = "3D View", space_type = "VIEW_3D")
    
    addon_keymaps.append(km)
    
def unregister_keymaps():
    global addon_keymaps
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()
'''
    
    def insert_snippet(self, text_block, match, name):
        text_block.select_match_in_current_line(match)
        text_block.delete_selection()
        text_block.insert(self.keymap_registration_code)
    
    def get_snippet_names(self, match):
        return ["Setup Keymap Registration"]
        
                
class KeymapItemSnippet:
    expression = "=key\|(\w+)((\|shift|\|(strg|ctrl)|\|alt)*)"
    
    # keep order
    types = ["Normal", "Menu", "Pie"]
    type_names = ["Key for Operator", "Key for Menu", "Key for Pie Menu"]
                
    def insert_snippet(self, text_block, match, name):
        item_type = self.get_type(name)
        
        text = "kmi = " + self.get_new_item_string(match, item_type)
        replace_match(text_block, match, text)
        
        if item_type == "Normal":
            text_block.select_text_in_current_line("transform.translate")
        elif item_type in ["Menu", "Pie"]:
            text_block.line_break()
            text_block.insert(self.get_property_set_string(match, item_type))
            
    def get_new_item_string(self, match, t):
        operator_name = self.get_default_operator_name(match, t)
        key = self.get_key(match)
        extra_keys = self.get_optional_key_string(match)
        return "km.keymap_items.new(\""+operator_name+"\", type = \""+key+"\", value = \"PRESS\""+extra_keys+")"
          
    def get_snippet_names(self, match):
        return self.type_names
        
    def get_key(self, match):
        return match.group(1).upper()
        
    def get_optional_key_string(self, match):
        text = ""
        if self.use_strg(match): text += ", ctrl = True"
        if self.use_shift(match): text += ", shift = True"
        if self.use_alt(match): text += ", alt = True"
        return text
        
    def get_default_operator_name(self, match, t):
        if t == "Menu": return "wm.call_menu"
        if t == "Pie": return "wm.call_menu_pie"   
        return "transform.translate"
        
    def get_property_set_string(self, match, t):
        if t in ["Menu", "Pie"]: return "kmi.properties.name = "
        return ""
        
    def get_type(self, name):
        return self.types[self.type_names.index(name)]
        
    def use_strg(self, match):
        return "|strg" in match.group(2) or "|ctrl" in match.group(2)
        
    def use_shift(self, match):
        return "|shift" in match.group(2)
        
    def use_alt(self, match):
        return "|alt" in match.group(2)
        
create_snippet_objects()  