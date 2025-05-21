import ast
import networkx as nx
from matplotlib import pyplot as plt

# Відкриваємо файл із кодом
with open("auth.py", "r") as f:
    code = f.read()

# Розбираємо код в AST
tree = ast.parse(code)
func = tree.body[0]  # перша функція

# Клас-відвідувач для побудови CFG
class CFGBuilder(ast.NodeVisitor):
    def __init__(self):
        self.G = nx.DiGraph()
        self.counter = 0
        self.current_node = None
        self.edges_to_add = []
        self.exit_nodes = []
        
    def new_node(self, label):
        node_id = f"n{self.counter}"
        self.counter += 1
        self.G.add_node(node_id)
        self.G.nodes[node_id]['label'] = f"Statement {self.counter - 1}"
        self.G.nodes[node_id]['original_label'] = label
        return node_id
    
    def add_edge(self, from_node, to_node):
        if from_node and to_node:
            self.edges_to_add.append((from_node, to_node))
            
    def visit_FunctionDef(self, node):
        self.current_node = self.new_node(f"def {node.name}(...)")
        entry_node = self.current_node
        
        # Відвідуємо всі дочірні вузли
        for stmt in node.body:
            self.visit(stmt)
            
        # Додаємо всі краї після відвідування
        for from_node, to_node in self.edges_to_add:
            self.G.add_edge(from_node, to_node)
            
        # Встановлюємо вихідні вузли
        if not self.exit_nodes:
            self.exit_nodes = [self.current_node]
            
        return entry_node
    
    def visit_If(self, node):
        # Вузол умови
        condition_node = self.new_node(f"if {ast.unparse(node.test)}:")
        prev_node = self.current_node
        self.add_edge(prev_node, condition_node)
        
        # Гілка True
        self.current_node = condition_node
        true_entry = None
        true_exits = []
        
        for stmt in node.body:
            if true_entry is None:
                true_entry = self.new_node(ast.unparse(stmt))
                self.add_edge(condition_node, true_entry)
                self.current_node = true_entry
            else:
                self.visit(stmt)
                
        if not true_entry:  # якщо тіло порожнє
            true_entry = self.new_node("pass")
            self.add_edge(condition_node, true_entry)
            
        true_exits.append(self.current_node)
        
        # Гілка False
        false_entry = None
        false_exits = []
        
        if node.orelse:
            for stmt in node.orelse:
                if false_entry is None:
                    false_entry = self.new_node(ast.unparse(stmt))
                    self.add_edge(condition_node, false_entry)
                    self.current_node = false_entry
                else:
                    self.visit(stmt)
            false_exits.append(self.current_node)
        else:
            false_entry = None
            
        # Створюємо після-if вузол, якщо потрібно
        if true_exits or false_exits:
            after_if_node = self.new_node("after_if")
            
            for exit_node in true_exits:
                self.add_edge(exit_node, after_if_node)
                
            if false_entry:
                for exit_node in false_exits:
                    self.add_edge(exit_node, after_if_node)
            else:
                self.add_edge(condition_node, after_if_node)
                
            self.current_node = after_if_node
    
    def visit_Return(self, node):
        return_node = self.new_node(f"return {ast.unparse(node.value)}")
        self.add_edge(self.current_node, return_node)
        self.current_node = return_node
        self.exit_nodes.append(return_node)
        
    def generic_visit(self, node):
        if isinstance(node, ast.stmt):
            if not isinstance(node, ast.FunctionDef) and not isinstance(node, ast.If):
                stmt_node = self.new_node(ast.unparse(node))
                self.add_edge(self.current_node, stmt_node)
                self.current_node = stmt_node
        
        super().generic_visit(node)

# Створюємо CFG
cfg_builder = CFGBuilder()
cfg_builder.visit(func)
G = cfg_builder.G

# Знаходимо всі шляхи виконання
# Шукаємо шляхи від початку до всіх кінцевих вузлів (return)
start_node = next(iter(G.nodes()))  # Беремо перший вузол як початковий
paths = []
for end_node in cfg_builder.exit_nodes:
    try:
        paths.extend(list(nx.all_simple_paths(G, source=start_node, target=end_node)))
    except nx.NetworkXNoPath:
        continue

print("Шляхи виконання (all_simple_paths):")
for i, path in enumerate(paths, 1):
    print(f"Шлях {i}: {path}")

# Створюємо копію графа з простими атрибутами для dot-формату
G_dot = nx.DiGraph()
for node, data in G.nodes(data=True):
    original_label = data.get('original_label', data['label'])
    if isinstance(original_label, str):
        safe_label = original_label.replace('"', '\\"').replace(':', '_')
        G_dot.add_node(node, label=safe_label)
for u, v in G.edges():
    G_dot.add_edge(u, v)

# Записуємо спрощений граф у dot-формат
nx.nx_pydot.write_dot(G_dot, "cfg.dot")

# Розраховуємо цикломатичну складність за формулою McCabe
# M = E - N + 2P, де E - кількість ребер, N - кількість вузлів, P - кількість компонент зв'язності (для однієї функції P=1)
M = G.number_of_edges() - G.number_of_nodes() + 2
print("Цикломатична складність:", M)

# Візуалізуємо граф
plt.figure(figsize=(16, 12))  # Більший розмір графа
pos = nx.spring_layout(G, k=0.5)  # Збільшуємо відстань між вузлами

# Малюємо вузли без міток
nx.draw(G, pos, 
        with_labels=False,  # Відключаємо автоматичні мітки
        node_color='lightblue', 
        node_size=3000,  # Збільшуємо розмір вузлів
        arrows=True, 
        arrowsize=20,  # Збільшуємо розмір стрілок
        edge_color='gray')

# Додаємо номери вузлів (ідентифікатори)
node_ids = {node: node for node in G.nodes()}
nx.draw_networkx_labels(G, pos, node_ids, font_size=12, font_color='black', 
                        font_weight='bold', font_family='sans-serif')

# Додаємо мітки вузлів (оригінальний код) як окремий текст нижче вузлів
label_pos = {node: (coords[0], coords[1]-0.06) for node, coords in pos.items()}  # Зсув міток вниз
labels = {}
for node, data in G.nodes(data=True):
    label = data.get('original_label', data.get('label', ''))
    if len(label) > 20:
        label = label[:20] + "..."
    labels[node] = label

nx.draw_networkx_labels(G, label_pos, labels, font_size=8, font_color='navy')

plt.axis('off')  # Вимикаємо осі
plt.tight_layout()  # Оптимізуємо розташування
plt.savefig("cfg_vis.png", dpi=300)  # Збільшуємо роздільну здатність
plt.close()

print("CFG збережено у файлах cfg.dot та cfg_vis.png")