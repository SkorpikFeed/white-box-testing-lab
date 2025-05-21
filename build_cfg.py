import ast
import networkx as nx
from matplotlib import pyplot as plt

# Відкриваємо файл із кодом
with open("auth.py", "r") as f:
    code = f.read()

# Розбираємо код в AST
tree = ast.parse(code)
func = tree.body[0]  # перша функція

# Створюємо граф
G = nx.DiGraph()
prev = []
counter = 0

# Проходимо по кожному виразу у функції
for stmt in func.body:
    label = ast.unparse(stmt)
    node = f"n{counter}"
    # Зберігаємо оригінальну мітку як атрибут Python об'єкта, але використовуємо
    # безпечні мітки для DOT-формату
    G.add_node(node)
    G.nodes[node]['label'] = f"Statement {counter}"
    G.nodes[node]['original_label'] = label
    for p in prev:
        G.add_edge(p, node)
    prev = [node]
    counter += 1

# Знаходимо всі шляхи виконання
paths = list(nx.all_simple_paths(G, source="n0", target=prev[0]))
print("Шляхи виконання (all_simple_paths):")
for path in paths:
    print(path)

# Створюємо копію графа з простими атрибутами для dot-формату
G_dot = nx.DiGraph()
for node, data in G.nodes(data=True):
    G_dot.add_node(node, label=data['label'])
for u, v in G.edges():
    G_dot.add_edge(u, v)

# Записуємо спрощений граф у dot-формат
nx.nx_pydot.write_dot(G_dot, "cfg.dot")

# Розраховуємо цикломатичну складність
M = G.number_of_edges() - G.number_of_nodes() + 2
print("Циклматична складність:", M)

# Візуалізуємо граф (опціонально)
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, arrows=True)
# Використовуємо original_label для візуалізації в matplotlib
labels = {node: data.get('original_label', data.get('label', '')) for node, data in G.nodes(data=True)}
nx.draw_networkx_labels(G, pos, labels)
plt.savefig("cfg_vis.png")
plt.close()

print("CFG збережено у файлах cfg.dot та cfg_vis.png")