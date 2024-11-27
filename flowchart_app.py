import streamlit as st
import graphviz
import json
import google.generativeai as genai

def add_instructions():
    st.markdown("""
    ### 🎯 Quick Start Guide
    
    1. **Get Your API Key**
       - Visit https://makersuite.google.com/app/apikey
       - Create a new API key
       - Copy and paste it below
    
    2. **Generate Flowchart**
       - Type your flowchart description
       - Click "Generate Flowchart" button
    
    3. **Edit Your Flowchart**
       - Add/Remove nodes
       - Modify connections
       - Update labels
    
    4. **Save Your Work**
       - Download as PDF
       - Export as JSON
    """)

def load_default_nodes():
    return {
        'A': 'Start',
        'B': 'Initial Assessment',
        'C': 'Decision Point',
        'D': 'End'
    }

def load_default_edges():
    return [
        ('A', 'B', 'Begin Process'),
        ('B', 'C', 'Evaluate'),
        ('C', 'D', 'Complete')
    ]

def generate_flowchart_from_prompt(prompt):
    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    enhanced_prompt = f"""Generate ONLY a JSON response for this flowchart: {prompt}

    The response must be a valid JSON object with this exact structure:
    {{
        "nodes": {{"id": "label"}},
        "edges": [["source_id", "target_id", "label"]]
    }}

    Requirements:
    1. Include 8-10 detailed steps/nodes minimum
    2. Multiple decision points with Yes/No branches
    3. Clear process flows with specific actions
    4. Descriptive edge labels for each connection
    5. Logical sequence from start to end

    Example valid output:
    {{
        "nodes": {{
            "A": "Start Process",
            "B": "Initial Assessment",
            "C": "Evaluate Severity",
            "D": "High Risk Path",
            "E": "Low Risk Path",
            "F": "Implement Actions",
            "G": "Monitor Results",
            "H": "Final Review",
            "I": "End Process"
        }},
        "edges": [
            ["A", "B", "Begin evaluation"],
            ["B", "C", "Assessment complete"],
            ["C", "D", "High risk identified"],
            ["C", "E", "Low risk identified"],
            ["D", "F", "Take immediate action"],
            ["E", "F", "Proceed with standard protocol"],
            ["F", "G", "Actions implemented"],
            ["G", "H", "Monitor outcomes"],
            ["H", "I", "Process complete"]
        ]
    }}"""
    
    response = model.generate_content(enhanced_prompt)
    
    try:
        response_text = response.text.strip()
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
        if response_text.startswith('json'):
            response_text = response_text[4:]
            
        flowchart_data = json.loads(response_text.strip())
        return flowchart_data['nodes'], flowchart_data['edges']
    except Exception as e:
        st.write("Generated response:", response.text)
        return load_default_nodes(), load_default_edges()

def create_flowchart(nodes, edges):
    dot = graphviz.Digraph()
    dot.attr(rankdir='TB')
    
    # Set default node attributes for rectangular boxes
    dot.attr('node', shape='box', style='filled', fillcolor='lightgray')
    
    for node_id, label in nodes.items():
        dot.node(node_id, f"{node_id}: {label}")
    
    for source, target, label in edges:
        dot.edge(source, target, label)
    
    return dot

def edit_nodes_and_edges(nodes, edges):
    st.markdown("### ✏️ Edit Nodes")
    
    # Add new node
    st.markdown("#### Add New Node")
    col1, col2 = st.columns(2)
    with col1:
        new_node_id = st.text_input("New Node ID (e.g., J, K, L...)", "")
    with col2:
        new_node_label = st.text_input("New Node Label", "")
    if st.button("➕ Add Node") and new_node_id and new_node_label:
        nodes[new_node_id] = new_node_label

    # Edit existing nodes
    st.markdown("#### Edit/Remove Nodes")
    updated_nodes = {}
    for node_id, label in nodes.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            new_label = st.text_input(f"Node {node_id}", label, key=f"node_{node_id}")
        with col2:
            keep_node = not st.button(f"🗑️ Remove", key=f"remove_node_{node_id}")
        if keep_node:
            updated_nodes[node_id] = new_label

    st.markdown("### 🔗 Edit Connections")
    
    # Add new edge
    st.markdown("#### Add New Connection")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_source = st.selectbox("From", options=list(updated_nodes.keys()), key="new_edge_source")
    with col2:
        new_target = st.selectbox("To", options=list(updated_nodes.keys()), key="new_edge_target")
    with col3:
        new_edge_label = st.text_input("Label", "")
    if st.button("➕ Add Connection"):
        edges.append((new_source, new_target, new_edge_label))

    # Edit existing edges
    st.markdown("#### Edit/Remove Connections")
    updated_edges = []
    for i, (source, target, label) in enumerate(edges):
        col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
        with col1:
            new_source = st.selectbox(f"From", options=list(updated_nodes.keys()), key=f"source_{i}", index=list(updated_nodes.keys()).index(source))
        with col2:
            new_target = st.selectbox(f"To", options=list(updated_nodes.keys()), key=f"target_{i}", index=list(updated_nodes.keys()).index(target))
        with col3:
            new_label = st.text_input(f"Label", label, key=f"label_{i}")
        with col4:
            keep_edge = not st.button(f"🗑️", key=f"remove_edge_{i}")
        if keep_edge:
            updated_edges.append((new_source, new_target, new_label))

    return updated_nodes, updated_edges

def main():
    st.set_page_config(layout="wide")
    
    left_col, right_col = st.columns([2, 3])
    
    with left_col:
        st.title('🔄 Flowchart Generator')
        add_instructions()
        
        api_key = st.text_input(
            "🔑 Enter Google Gemini API Key",
            type="password",
            value=st.session_state.get('api_key', ''),
            help="Get your API key from https://makersuite.google.com/app/apikey"
        )
        st.session_state.api_key = api_key

        if not api_key:
            st.warning("⚠️ Please enter your API key to start")
            return

        user_prompt = st.text_area(
            "📝 Describe Your Flowchart",
            "Create a detailed flowchart for handling emergency situations",
            height=100
        )
        
        if st.button("🎨 Generate Flowchart"):
            with st.spinner("Generating..."):
                nodes, edges = generate_flowchart_from_prompt(user_prompt)
                st.session_state.nodes = nodes
                st.session_state.edges = edges

        if hasattr(st.session_state, 'nodes'):
            st.divider()
            updated_nodes, updated_edges = edit_nodes_and_edges(
                st.session_state.nodes, 
                st.session_state.edges
            )
            st.session_state.nodes = updated_nodes
            st.session_state.edges = updated_edges

    with right_col:
        if hasattr(st.session_state, 'nodes'):
            st.markdown("### 📊 Current Flowchart")
            dot = create_flowchart(st.session_state.nodes, st.session_state.edges)
            st.graphviz_chart(dot)
            
            col1, col2 = st.columns(2)
            with col1:
                dot.render("flowchart", format="pdf", cleanup=True)
                with open("flowchart.pdf", "rb") as pdf_file:
                    st.download_button(
                        "📥 Download PDF",
                        data=pdf_file.read(),
                        file_name="flowchart.pdf",
                        mime='application/pdf'
                    )
            with col2:
                export_data = {
                    "nodes": st.session_state.nodes,
                    "edges": st.session_state.edges
                }
                st.download_button(
                    "💾 Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name="flowchart_data.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main()
