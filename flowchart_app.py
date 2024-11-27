import streamlit as st
import graphviz
import json
import google.generativeai as genai

def add_instructions():
    st.sidebar.markdown("""
    ### 🎯 Quick Start Guide
    
    1. **Get Your API Key**
       - Visit https://makersuite.google.com/app/apikey
       - Create a new API key
       - Copy and paste it below
    
    2. **Generate Flowchart**
       - Type your flowchart description
       - Click "Generate Flowchart" button
    
    3. **Edit Your Flowchart**
       - Modify node text directly
       - Adjust connections using dropdowns
       - Add labels to connections
    
    4. **Save Your Work**
       - Use "Export Flowchart" to download PDF
       - Download JSON for future editing
    
    ### 💡 Tips
    - Be specific in your flowchart description
    - Include decision points and outcomes
    - Use clear, concise node labels
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
        st.session_state.nodes = flowchart_data['nodes']
        st.session_state.edges = flowchart_data['edges']
        return flowchart_data['nodes'], flowchart_data['edges']
    except Exception as e:
        st.write("Generated response:", response.text)
        return load_default_nodes(), load_default_edges()

def create_flowchart(nodes, edges):
    dot = graphviz.Digraph()
    dot.attr(rankdir='TB')
    
    for node_id, label in nodes.items():
        dot.node(node_id, f"{node_id}: {label}")
    
    for source, target, label in edges:
        dot.edge(source, target, label)
    
    return dot

def edit_nodes_and_edges(nodes, edges):
    st.markdown("### ✏️ Edit Nodes")
    st.info("Modify the text for each node below")
    updated_nodes = {}
    for node_id, label in nodes.items():
        st.markdown(f"**Node ID: {node_id}** (Current Label: {label})")
        new_label = st.text_input(f"Update Label for Node {node_id}", label, key=f"node_{node_id}")
        updated_nodes[node_id] = new_label

    st.markdown("### 🔗 Edit Connections")
    st.info("Adjust the connections between nodes and their labels")
    updated_edges = []
    for i, (source, target, label) in enumerate(edges):
        st.markdown(f"**Edge {i+1}**: From {source} ({nodes[source]}) → To {target} ({nodes[target]})")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_source = st.selectbox(f"From Node {i}", options=list(nodes.keys()), key=f"source_{i}", index=list(nodes.keys()).index(source))
        with col2:
            new_target = st.selectbox(f"To Node {i}", options=list(nodes.keys()), key=f"target_{i}", index=list(nodes.keys()).index(target))
        with col3:
            new_label = st.text_input(f"Connection Label {i}", label, key=f"label_{i}")
        updated_edges.append((new_source, new_target, new_label))

    return updated_nodes, updated_edges

def main():
    st.title('🔄 AI-Powered Flowchart Generator')
    
    add_instructions()
    
    if 'nodes' not in st.session_state:
        st.session_state.nodes = load_default_nodes()
    if 'edges' not in st.session_state:
        st.session_state.edges = load_default_edges()
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''

    api_key = st.sidebar.text_input(
        "🔑 Enter Google Gemini API Key",
        type="password",
        value=st.session_state.api_key,
        help="Get your API key from https://makersuite.google.com/app/apikey"
    )
    st.session_state.api_key = api_key

    if not api_key:
        st.warning("⚠️ Please enter your Google Gemini API key in the sidebar to start generating flowcharts")
        return

    st.markdown("### 📝 Describe Your Flowchart")
    user_prompt = st.text_area(
        "Be specific about the process or workflow you want to create:",
        "Create a detailed flowchart for handling emergency situations in a school, including assessment, response procedures, and follow-up actions.",
        height=100
    )
    
    if st.button("🎨 Generate Flowchart"):
        with st.spinner("🔄 Generating detailed flowchart..."):
            nodes, edges = generate_flowchart_from_prompt(user_prompt)
            st.session_state.nodes = nodes
            st.session_state.edges = edges
            
            st.markdown("### 📊 Generated Flowchart")
            dot = create_flowchart(nodes, edges)
            st.graphviz_chart(dot)
            
            dot.render("flowchart", format="pdf", cleanup=True)
            with open("flowchart.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()
                st.download_button(
                    label="📥 Download PDF",
                    data=PDFbyte,
                    file_name="flowchart.pdf",
                    mime='application/pdf'
                )
    
    if hasattr(st.session_state, 'nodes') and st.session_state.nodes != load_default_nodes():
        st.divider()
        st.markdown("### ✏️ Edit Generated Flowchart")
        
        updated_nodes, updated_edges = edit_nodes_and_edges(
            st.session_state.nodes, 
            st.session_state.edges
        )
        
        st.session_state.nodes = updated_nodes
        st.session_state.edges = updated_edges
        
        st.markdown("### 📊 Updated Flowchart")
        dot = create_flowchart(updated_nodes, updated_edges)
        st.graphviz_chart(dot)
        
        col1, col2 = st.columns(2)
        with col1:
            dot.render("flowchart_updated", format="pdf", cleanup=True)
            with open("flowchart_updated.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()
                st.download_button(
                    label="📥 Download Updated PDF",
                    data=PDFbyte,
                    file_name="flowchart_updated.pdf",
                    mime='application/pdf'
                )
        with col2:
            export_data = {
                "nodes": updated_nodes,
                "edges": updated_edges
            }
            st.download_button(
                "💾 Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name="flowchart_data.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
