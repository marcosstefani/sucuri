from lark import Tree, Token
import re
import os
from sucuri.parser import parse_sucuri

class SucuriCompiler:
    def __init__(self, context=None, base_dir=".", filters=None):
        self.context = context or {}
        self.base_dir = base_dir
        self.filters = filters or {}
        self.indent_level = 0
        self.output = []
        self.styles = []
        self.scripts = []
        self.macros = {}

    def compile(self, tree):
        self.output = []
        self.styles = []
        self.scripts = []
        self.macros = {}
        self.blocks = {}
        self.extends_path = None
        self.indent_level = 0
        
        # HTML usually has a head/styles section injected before the body
        # Let's make an initial pass to load macros, if necessary.
        self._visit(tree)

        if self.extends_path:
            # Re-compile but from parent template
            parent_path = os.path.join(self.base_dir, self.extends_path)
            if not parent_path.endswith('.suc'):
                parent_path += '.suc'
            with open(parent_path, 'r', encoding='utf-8') as f:
                parent_text = f.read()
            from sucuri.parser import parse_sucuri
            parent_tree = parse_sucuri(parent_text)
            
            # Save child blocks to inject into parent
            child_blocks = self.blocks
            self.blocks = {}
            self.extends_path = None
            self.output = []
            
            # Assign collected blocks to the parent
            self.blocks = child_blocks
            self._visit(parent_tree)

        html = "\n".join(self.output)
        
        # Glue everything together in HTML style
        extras = []
        if self.styles:
            for style in self.styles:
                extras.append(f"    <style>{style}</style>")
        if self.scripts:
            for script in self.scripts:
                # The README.md describes inline scripts within style tags (injected along with the final HTML, no external SRCs)
                extras.append(f"    <script>{script}</script>")
                
        if extras:
            html = html.replace("</body>", "\n".join(extras) + "\n    </body>")
            if "</body>" not in html:
                html += "\n" + "\n".join(extras)
            
        return html

    def _get_indent(self):
        return "    " * self.indent_level

    def _get_var(self, var_name, default=None):
        if not var_name:
            return default
        parts = var_name.split('.')
        val = self.context.get(parts[0], default)
        for part in parts[1:]:
            if isinstance(val, dict):
                val = val.get(part, default)
            else:
                return default
        return val

    def _render_text(self, text):
        import html
        # Replace variables {var | filter} or {var.sub} with values from context
        def repl(match):
            raw = match.group(1)
            parts = raw.split('|')
            var_name = parts[0].strip()
            
            val = self._get_var(var_name, f"{{{var_name}}}")
            
            # evaluate filters
            is_safe = False
            for f in parts[1:]:
                f_name = f.strip()
                if f_name == 'safe':
                    is_safe = True
                elif f_name == 'upper':
                    val = str(val).upper()
                elif f_name == 'lower':
                    val = str(val).lower()
                elif f_name == 'title':
                    val = str(val).title()
                elif f_name in self.filters:
                    val = self.filters[f_name](val)
            
            if not is_safe:
                return html.escape(str(val))
            return str(val)
        
        # Also replace #loop_var and #loop_var.nested
        def repl_hash(match):
            raw = match.group(1)
            parts = raw.split('|')
            var_name = parts[0].strip()
            
            val = self._get_var(var_name, f"#{var_name}")
            
            is_safe = False
            for f in parts[1:]:
                f_name = f.strip()
                if f_name == 'safe':
                    is_safe = True
                elif f_name == 'upper':
                    val = str(val).upper()
                elif f_name == 'lower':
                    val = str(val).lower()
                elif f_name == 'title':
                    val = str(val).title()
                elif f_name in self.filters:
                    val = self.filters[f_name](val)

            if not is_safe:
                return html.escape(str(val))
            return str(val)

        text = re.sub(r'\{([a-zA-Z0-9_\.\s\|]+)\}', repl, text)
        text = re.sub(r'#([a-zA-Z0-9_\.\s\|]+)', repl_hash, text)
        return text.strip()

    def _visit(self, node):
        if isinstance(node, Token):
            return

        method_name = f'visit_{node.data}'
        if hasattr(self, method_name):
            getattr(self, method_name)(node)
        else:
            for child in node.children:
                if child is not None:
                    self._visit(child)

    def visit_block(self, node):
        for child in node.children:
            if child is not None:
                self._visit(child)

    def _process_list(self, inner_text):
        # Format in inner_text: "(items class=\"ul-squares\")" -> remove parens
        args_str = inner_text.strip("()")
        parts = args_str.split(' ', 1)
        if not parts or not parts[0]:
            return

        items_var = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        items = self._get_var(items_var, [])
        checked_list = self._get_var("checked", [])

        is_checkbox = False
        attrs = []
        
        for match in re.finditer(r'([a-zA-Z0-9_-]+(?:="[^"]*")?)', rest):
            token = match.group(1)
            if token == "checked":
                is_checkbox = True
            else:
                attrs.append(token)

        attr_str = (" " + " ".join(attrs)) if attrs else ""
        indent = self._get_indent()

        if is_checkbox:
            for item in items:
                chk = ' checked="checked"' if item in checked_list else ""
                self.output.append(f'{indent}<input type="checkbox" id="ck-{item}"{chk}>{item}')
        else:
            self.output.append(f'{indent}<ul{attr_str}>')
            self.indent_level += 1
            inner_indent = self._get_indent()
            for item in items:
                self.output.append(f'{inner_indent}<li> {item} </li>')
            self.indent_level -= 1
            self.output.append(f'{indent}</ul>')

    def visit_tag_stmt(self, node):
        tag_name = ""
        attributes = ""
        inline_text = ""
        block = None
        attr_list = []
        css_classes = []
        css_id = ""

        for child in node.children:
            if child is None:
                continue
            if isinstance(child, Token):
                if child.type == "TEXT":
                    inline_text = child.value.strip()
            elif getattr(child, "data", None) == "tag_def":
                tag_token = child.children[0]
                if tag_token.type == "TAG_NAME":
                    tag_name = tag_token.value
                elif tag_token.type == "CSS_TAG":
                    raw_val = tag_token.value
                    if raw_val[0] in ['#', '.']:
                        tag_name = "div"
                    else:
                        match = re.match(r'^([a-zA-Z0-9\-]+)', raw_val)
                        if match:
                            tag_name = match.group(1)
                            raw_val = raw_val[len(tag_name):]
                    
                    for match in re.finditer(r'(#[a-zA-Z0-9\-]+|\.[a-zA-Z0-9\-]+)', raw_val):
                        token = match.group(1)
                        if token.startswith('#'):
                            css_id = token[1:]
                        elif token.startswith('.'):
                            css_classes.append(token[1:])

            elif isinstance(child, Tree):
                if child.data == "attributes":
                    # Collect attr dict
                    for attr_node in child.children:
                        if attr_node is None or not isinstance(attr_node, Tree):
                            continue
                        name = ""
                        val = None
                        for grant in attr_node.children:
                            if grant is None:
                                continue
                            if grant.type == "ATTR_NAME":
                                name = grant.value
                            elif grant.type == "ATTR_VALUE":
                                val = grant.value
                        attr_list.append((name, val))
                        if val:
                            attributes += f'{name}={val} '
                        else:
                            attributes += f'{name} '
                                
                    attributes = attributes.strip()
                elif child.data == "block":
                    block = child

        if tag_name == "list":
            # the original attributes parsed
            # it might be item=None, class="ul"
            if attr_list:
                items_var = attr_list[0][0]
                is_checkbox = False
                checked_var = "checked"
                attrs = []
                
                for k, v in attr_list[1:]:
                    if v:
                        attrs.append(f"{k}={v}")
                    else:
                        # treat the first positional argument without value as the checked variable
                        if not is_checkbox:
                            checked_var = k
                            is_checkbox = True
                        else:
                            attrs.append(k)

                items = self._get_var(items_var, [])
                checked_list = self._get_var(checked_var, [])
                attr_str = (" " + " ".join(attrs)) if attrs else ""
                indent = self._get_indent()

                if is_checkbox:
                    for item in items:
                        chk = ' checked="checked"' if item in checked_list else ""
                        self.output.append(f'{indent}<input type="checkbox" id="ck-{item}"{chk}>{item}')
                else:
                    self.output.append(f'{indent}<ul{attr_str}>')
                    self.indent_level += 1
                    inner_indent = self._get_indent()
                    for item in items:
                        self.output.append(f'{inner_indent}<li> {item} </li>')
                    self.indent_level -= 1
                    self.output.append(f'{indent}</ul>')
            return

        elif tag_name == "table":
            if attr_list:
                headers_var = None
                data_var = None
                foot_var = None
                attrs = []
                
                positional = []
                for k, v in attr_list:
                    if v:
                        attrs.append(f"{k}={v}")
                    else:
                        positional.append(k)
                        
                if len(positional) >= 1:
                    headers_var = positional[0]
                if len(positional) >= 2:
                    data_var = positional[1]
                if len(positional) >= 3:
                    foot_var = positional[2]

                headers = self._get_var(headers_var, []) if headers_var else []
                data = self._get_var(data_var, []) if data_var else []
                foot = self._get_var(foot_var, []) if foot_var else []
                
                attr_str = (" " + " ".join(attrs)) if attrs else ""
                indent = self._get_indent()
                self.output.append(f'{indent}<table{attr_str}>')
                self.indent_level += 1
                inner_indent = self._get_indent()
                
                if headers:
                    self.output.append(f'{inner_indent}<thead>')
                    self.indent_level += 1
                    thead_indent = self._get_indent()
                    self.output.append(f'{thead_indent}<tr>')
                    self.indent_level += 1
                    th_indent = self._get_indent()
                    for th in headers:
                        self.output.append(f'{th_indent}<th>{th}</th>')
                    self.indent_level -= 1
                    self.output.append(f'{thead_indent}</tr>')
                    self.indent_level -= 1
                    self.output.append(f'{inner_indent}</thead>')
                    
                if data:
                    self.output.append(f'{inner_indent}<tbody>')
                    self.indent_level += 1
                    tbody_indent = self._get_indent()
                    for row in data:
                        self.output.append(f'{tbody_indent}<tr>')
                        self.indent_level += 1
                        td_indent = self._get_indent()
                        for cell in row:
                            self.output.append(f'{td_indent}<td>{cell}</td>')
                        self.indent_level -= 1
                        self.output.append(f'{tbody_indent}</tr>')
                    self.indent_level -= 1
                    self.output.append(f'{inner_indent}</tbody>')

                if foot:
                    self.output.append(f'{inner_indent}<tfoot>')
                    self.indent_level += 1
                    tfoot_indent = self._get_indent()
                    self.output.append(f'{tfoot_indent}<tr>')
                    self.indent_level += 1
                    tf_indent = self._get_indent()
                    for tf in foot:
                        self.output.append(f'{tf_indent}<td>{tf}</td>')
                    self.indent_level -= 1
                    self.output.append(f'{tfoot_indent}</tr>')
                    self.indent_level -= 1
                    self.output.append(f'{inner_indent}</tfoot>')

                self.indent_level -= 1
                self.output.append(f'{indent}</table>')
            return

        inline_text = self._render_text(inline_text)

        indent = self._get_indent()
        
        # Merge CSS shortcut classes/id into attributes string
        class_str = ""
        id_str = ""
        
        if css_classes:
            class_str = f'class="{" ".join(css_classes)}"'
        if css_id:
            id_str = f'id="{css_id}"'
            
        ext_attrs = []
        if id_str: ext_attrs.append(id_str)
        if class_str: ext_attrs.append(class_str)
        if attributes: ext_attrs.append(attributes)

        final_attrs = " ".join(ext_attrs)

        # Start tag
        open_tag = f"<{tag_name}"
        if final_attrs:
            open_tag += f" {final_attrs}"
        open_tag += ">"
        
        if inline_text:
            open_tag += inline_text

        self.output.append(f"{indent}{open_tag}")
        
        # Render children inside block
        if block:
            self.indent_level += 1
            self._visit(block)
            self.indent_level -= 1

        # Self-closing tags rule can be added later, assuming standard closing for now
        close_tag = f"{indent}</{tag_name}>" if block else f"</{tag_name}>"

        if not block:
            self.output[-1] += f"</{tag_name}>"
        else:
            self.output.append(close_tag)

    def visit_text_inline(self, node):
        indent = self._get_indent()
        text = node.children[0].value
        self.output.append(f"{indent}{self._render_text(text)}")

    def visit_if_stmt(self, node):
        condition = ""
        block_node = None
        for child in node.children:
            if isinstance(child, Token) and child.type == "CONDITION":
                condition = child.value.strip()
            elif isinstance(child, Tree) and child.data == "block":
                block_node = child

        try:
            is_true = eval(condition, {}, self.context)
        except Exception as e:
            is_true = False

        if is_true and block_node:
            self._visit(block_node)

    def visit_for_stmt(self, node):
        expr = ""
        block_node = None
        for child in node.children:
            if isinstance(child, Token) and child.type == "FOR_EXPR":
                expr = child.value.strip()
            elif isinstance(child, Tree) and child.data == "block":
                block_node = child

        match = re.match(r'([a-zA-Z0-9_]+)\s+in\s+([a-zA-Z0-9_\.]+)', expr)
        if match and block_node:
            item_var = match.group(1)
            list_var = match.group(2)
            
            iterable = self._get_var(list_var, [])
            for item in iterable:
                self.context[item_var] = item
                self._visit(block_node)
                
    def visit_include_stmt(self, node):
        path = ""
        for child in node.children:
            if isinstance(child, Token) and child.type == "PATH":
                path = child.value

        # For includes, we assume a .suc extension if none is provided
        if not path.endswith('.suc'):
            path += '.suc'
            
        full_path = os.path.join(self.base_dir, path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Parse the include and dynamically insert its tree into the current tree
            include_tree = parse_sucuri(content)
            
            # Here we should register it as a Macro, since in original Sucuri using "+macro" injects it
            # Based on the README, 'include inc/link' makes it accessible via '+link'
            macro_name = os.path.splitext(os.path.basename(path))[0]
            self.macros[macro_name] = include_tree

    def visit_macro_stmt(self, node):
        macro_name = ""
        attr_dict = {}
        for child in node.children:
            if child is None:
                continue
            if isinstance(child, Token):
                if child.type == "PATH":
                    macro_name = child.value
            elif isinstance(child, Tree) and getattr(child, "data", None) == "attributes":
                for attr_node in child.children:
                    if attr_node is None or not isinstance(attr_node, Tree):
                        continue
                    name = ""
                    val = None
                    for grant in attr_node.children:
                        if grant is None:
                            continue
                        if grant.type == "ATTR_NAME":
                            name = grant.value
                        elif grant.type == "ATTR_VALUE":
                            val = grant.value.strip("\"'")
                    if name:
                        attr_dict[name] = val
                
        if macro_name in self.macros:
            # Inject parameters into context
            old_context = {}
            for k, v in attr_dict.items():
                old_context[k] = self.context.get(k)
                self.context[k] = v

            self._visit(self.macros[macro_name])

            # Restore parameters
            for k, v in old_context.items():
                if v is None:
                    del self.context[k]
                else:
                    self.context[k] = v

    def visit_list_stmt(self, node):
        if not node.children:
            return

        items_var = None
        is_checkbox = False
        attrs = []

        for child in node.children:
            if child is None:
                continue
            if isinstance(child, Token):
                if child.type == "PATH":
                    if items_var is None:
                        items_var = child.value
                    elif child.value == "checked":
                        is_checkbox = True
                    else:
                        attrs.append(child.value)
            elif getattr(child, "data", None) == "attr":
                attr_name = ""
                attr_val = ""
                for grant in child.children:
                    if grant.type == "ATTR_NAME":
                        attr_name = grant.value
                    elif grant.type == "ATTR_VALUE":
                        attr_val = grant.value
                
                if attr_val:
                    attrs.append(f"{attr_name}={attr_val}")
                else:
                    if attr_name == "checked":
                        is_checkbox = True
                    else:
                        attrs.append(attr_name)

        if not items_var:
            return

        items = self._get_var(items_var, [])
        checked_list = self._get_var("checked", [])

        attr_str = (" " + " ".join(attrs)) if attrs else ""
        indent = self._get_indent()

        if is_checkbox:
            for item in items:
                chk = ' checked="checked"' if item in checked_list else ""
                self.output.append(f'{indent}<input type="checkbox" id="ck-{item}"{chk}>{item}')
        else:
            self.output.append(f'{indent}<ul{attr_str}>')
            self.indent_level += 1
            inner_indent = self._get_indent()
            for item in items:
                self.output.append(f'{inner_indent}<li> {item} </li>')
            self.indent_level -= 1
            self.output.append(f'{indent}</ul>')
            
    def visit_style_stmt(self, node):
        path = ""
        for child in node.children:
            if isinstance(child, Token) and child.type == "PATH":
                path = child.value
        if not path: return

        if not path.endswith('.css'):
            path += '.css'
        full_path = os.path.join(self.base_dir, path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.styles.append(content)

    def visit_script_stmt(self, node):
        path = ""
        for child in node.children:
            if isinstance(child, Token) and child.type == "PATH":
                path = child.value
        if not path: return

        if not path.endswith('.js'):
            path += '.js'
        full_path = os.path.join(self.base_dir, path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.scripts.append(content)

    def visit_extends_stmt(self, node):
        for child in node.children:
            if isinstance(child, Token) and child.type == "PATH":
                self.extends_path = child.value

    def visit_define_block_stmt(self, node):
        block_name = ""
        block_node = None
        for child in node.children:
            if isinstance(child, Token) and child.type == "BLOCK_NAME":
                block_name = child.value
            elif isinstance(child, Tree) and child.data == "block":
                block_node = child

        if not block_name:
            return

        # If a child overriding block is available in self.blocks, we render the child block instead
        if block_name in self.blocks:
            self._visit(self.blocks[block_name])
        else:
            # We are currently parsing a block definition. Save it to self.blocks
            # Or if it's the base template and no override exists, render the default block_node
            if self.extends_path:
                # Inside child template: store it to inject into parent
                self.blocks[block_name] = block_node
            else:
                # Inside parent template or no-extends template: render the default body
                if block_node:
                    self._visit(block_node)

