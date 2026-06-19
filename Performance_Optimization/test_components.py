import json

with open('AbInitio_Sample_Graph_analysis.json', 'r') as f:
    data = json.load(f)

components = data.get('components', [])
print(f"Number of components: {len(components)}")
print(f"Components list: {components}")

# Made with Bob
