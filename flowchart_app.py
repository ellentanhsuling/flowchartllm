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
        'B': 'Process',
        'C': 'Decision',
        'D': 'End'
    }

def load_default_edges():
    return [
        ('A', 'B', ''),
        ('B', 'C', ''),
        ('C', 'D', '')
    ]

def generate_flowchart_from_prompt(prompt):
    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    enhanced_prompt = f"""Create a detailed flowchart structure for: {prompt}
    The flowchart should capture all decision points and processes mentioned.
    Output a valid JSON with this structure:
    {{
        "nodes": {{"id": "label"}},
        "edges": [["source_id", "target_id", "label"]]
    }}
    
    For the nodes:
    - Include all decision points with clear yes/no outcomes
    - Break down major processes into steps
    - Use descriptive labels
    - Ensure logical flow between steps
    
    For the edges:
    - Label decision paths clearly (e.g., "Yes", "No")
    - Include action descriptions where relevant
    
    Example node structure:
    {{
        "A": "Initial Assessment",
        "B": "Evaluate Threat Level",
        "C": "De-escalation Process",
        "D": "Emergency Response"
    }}
    
    Example edge structure:
    [
        ["A", "B", "Proceed to evaluation"],
        ["B", "C", "Low threat"],
        ["B", "D", "High threat"]
    ]
    """
    
    response = model.generate_content(enhanced_prompt)
    
    try:
        flowchart_data = json.loads(response.text)
        return flowchart_data['nodes'], flowchart_data['edges']
    except:
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
        new_label = st.text_input(f"Update Label for Node {node_id}", label)
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
    
    # Initialize session state
    if 'nodes' not in st.session_state:
        st.session_state.nodes = load_default_nodes()
    if 'edges' not in st.session_state:
        st.session_state.edges = load_default_edges()
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''

    # API Key input in sidebar
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
        "Create a flowchart for project planning",
        help="Example: Create a detailed flowchart for handling customer complaints, including initial assessment, escalation criteria, and resolution steps"
    )
    
    if st.button("🎨 Generate Flowchart"):
        with st.spinner("🔄 Generating flowchart..."):
            nodes, edges = generate_flowchart_from_prompt(user_prompt)
            st.session_state.nodes = nodes
            st.session_state.edges = edges
            
            st.markdown("### 📊 Generated Flowchart")
            dot = create_flowchart(nodes, edges)
            st.graphviz_chart(dot)
            
            # Save flowchart as PDF
            dot.render("flowchart", format="pdf", cleanup=True)
            with open("flowchart.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()
                st.download_button(
                    label="📥 Download PDF",
                    data=PDFbyte,
                    file_name="flowchart.pdf",
                    mime='application/pdf'
                )
    
    if st.session_state.nodes != load_default_nodes():
        st.divider()
        st.markdown("### ✏️ Edit Generated Flowchart")
        st.session_state.nodes, st.session_state.edges = edit_nodes_and_edges(
            st.session_state.nodes, 
            st.session_state.edges
        )
        
        st.markdown("### 📊 Updated Flowchart")
        dot = create_flowchart(st.session_state.nodes, st.session_state.edges)
        st.graphviz_chart(dot)
        
        # Export functionality
        col1, col2 = st.columns(2)
        with col1:
            # Save updated flowchart as PDF
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
