import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))  
import streamlit as st
import asyncio
from utils.graph_vis import render_kg_graph
from utils.forecast_chart import render_forecast_chart
from agents.planner_agent import PlannerAgent
from agents.tool_agent import ToolSelectorAgent
from agents.forecaster_agent import ForecasterAgent
from kg_interface import KGInterface
import sys
from utils.gantt_chart import render_gantt_chart


# Set up page configuration with a custom theme
st.set_page_config(
    page_title="Autonomous NDT Planner",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Autonomous NDT Planning with LLM + Knowledge Graph\nAn intelligent system for non-destructive testing planning"
    }
)

# CSS to enhance the UI
st.markdown("""
<style>
    /* Main styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Header styling */
    .main h1 {
        color: #2c3e50;
        margin-bottom: 30px;
        padding-bottom: 10px;
        border-bottom: 2px solid #3498db;
    }
    
    /* Subheader styling */
    .main h2, .main h3 {
        color: #34495e;
        margin-top: 20px;
    }
    
    /* Card-like styling for sections */
    .stExpander {
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        margin-bottom: 20px !important;
        background-color: white !important;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 5px 15px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #2980b9;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    /* Success/Info message styling */
    .stSuccess, .stInfo, .stWarning {
        border-radius: 5px !important;
        border: none !important;
        padding: 20px !important;
    }
    
    /* Input styling */
    .stTextInput>div>div>input {
        border-radius: 5px;
        border: 1px solid #e0e0e0;
        padding: 10px;
    }
    
    /* Selectbox styling */
    .stSelectbox>div>div>div {
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
    
    /* Make agent sections stand out */
    .agent-section {
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Custom agent colors */
    .planner-agent {
        background-color: #e8f4fd;
        border-left: 4px solid #3498db;
    }
    
    .tool-agent {
        background-color: #ebf5ec;
        border-left: 4px solid #2ecc71;
    }
    
    .forecaster-agent {
        background-color: #fef5e7;
        border-left: 4px solid #f39c12;
    }
    
    /* Dashboard cards */
    .dashboard-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Icons */
    .icon-text {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Badge styling for counts */
    .badge {
        background-color: #3498db;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header with logo and title
col1, col2 = st.columns([1, 5])
with col1:
    st.markdown("# 🧠")
with col2:
    st.markdown("# Autonomous NDT Planning")
    st.markdown("#### Intelligent Non-Destructive Testing with LLM + Knowledge Graph")

def seed_knowledge_graph():
    kg = KGInterface()
    seed_query = """
    MERGE (m:Material {name: "Concrete"})
    MERGE (m2:Material {name: "Steel"})
    MERGE (m3:Material {name: "Wood"})

    MERGE (d1:Deterioration {name: "Cracking"})
    MERGE (d2:Deterioration {name: "Corrosion"})
    MERGE (d3:Deterioration {name: "Delamination"})

    MERGE (e1:Environment {name: "Humid"})
    MERGE (e2:Environment {name: "Dry"})
    MERGE (e3:Environment {name: "Submerged"})
    MERGE (e4:Environment {name: "High Temperature"})

    MERGE (n1:NDTMethod {name: "Ultrasonic Testing"})
    MERGE (n2:NDTMethod {name: "GPR"})
    MERGE (n3:NDTMethod {name: "Thermography"})
    MERGE (n4:NDTMethod {name: "Acoustic Emission"})
    MERGE (n5:NDTMethod {name: "Visual Inspection"})

    MERGE (s1:Sensor {name: "Acoustic Sensor"})
    MERGE (s2:Sensor {name: "Thermal Camera"})
    MERGE (s3:Sensor {name: "Moisture Sensor"})

    MERGE (m)-[:HAS_DETERIORATION_MECHANISM]->(d1)
    MERGE (m)-[:HAS_DETERIORATION_MECHANISM]->(d2)
    MERGE (m)-[:HAS_DETERIORATION_MECHANISM]->(d3)

    MERGE (d1)-[:DETECTED_BY]->(n1)
    MERGE (d1)-[:DETECTED_BY]->(n2)
    MERGE (d2)-[:DETECTED_BY]->(n3)
    MERGE (d3)-[:DETECTED_BY]->(n4)

    MERGE (n1)-[:REQUIRES_ENVIRONMENT]->(e1)
    MERGE (n2)-[:REQUIRES_ENVIRONMENT]->(e1)
    MERGE (n3)-[:REQUIRES_ENVIRONMENT]->(e4)
    MERGE (n4)-[:REQUIRES_ENVIRONMENT]->(e2)

    MERGE (s1)-[:RECOMMENDED_FOR]->(n4)
    MERGE (s2)-[:RECOMMENDED_FOR]->(n3)
    MERGE (s3)-[:RECOMMENDED_FOR]->(n1)
    """
    kg.cypher(seed_query, log=False)
    return True

# Ensure event loop and agents
if "loop" not in st.session_state:
    st.session_state.loop   = asyncio.new_event_loop()
    st.session_state.plan   = PlannerAgent()
    st.session_state.tools  = ToolSelectorAgent()
    st.session_state.fore   = ForecasterAgent()

# Create a sidebar for navigation and stats
with st.sidebar:
    st.markdown("### 📊 Knowledge Graph Stats")
    
    # Dashboard stats
    counts = KGInterface().cypher("""
        MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC
    """)
    
    if counts:
        for row in counts:
            st.markdown(f"""
            <div class="icon-text">
                <span>{'📦' if row['label'] == 'Material' else '🔍' if row['label'] == 'NDTMethod' else '🌡️' if row['label'] == 'Environment' else '💢' if row['label'] == 'Deterioration' else '📡' if row['label'] == 'Sensor' else '📌'}</span>
                <span><b>{row['label']}:</b></span>
                <span class="badge">{row['count']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No nodes found in knowledge graph")
    
    st.markdown("---")
    
    if st.button("🧪 Seed Demo Knowledge Graph", key="sidebar_seed"):
        if seed_knowledge_graph():
            st.success("✅ Knowledge graph seeded successfully!")
    
    st.markdown("---")
    st.markdown("### 📚 Documentation")
    st.markdown("""
    - [NDT Methods Guide](https://example.com)
    - [LLM Planning Documentation](https://example.com)
    - [Knowledge Graph Schema](https://example.com)
    """)

# Main content organized in tabs
tab1, tab2, tab3 = st.tabs(["🗣️ Natural Language Planner", "📎 Structured Planner", "🔍 Knowledge Graph Explorer"])

# ------------------- TAB 1: LLM Planner -------------------
with tab1:
    st.markdown("""
    <div class="dashboard-card">
        <h3>Natural Language Inspection Planning</h3>
        <p>Describe the observed defect in natural language and let our LLM-powered system plan your inspection.</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_input = st.text_input("Describe the observed defect:", 
                              placeholder="e.g., Cracks on concrete wall in humid environment",
                              key="nl_input")

    col1, col2 = st.columns([1, 3])
    with col1:
        run_nl = st.button("🔍 Plan Inspection", key="run_nl", use_container_width=True)
    
    if user_input and run_nl:
        loop = st.session_state.loop

        st.markdown("#### Inspection Planning Process")
        
        with st.spinner("PlannerAgent thinking..."):
            plan = loop.run_until_complete(st.session_state.plan.run(user_input))
            st.markdown("""
            <div class="agent-section planner-agent">
                <h4>🧠 PlannerAgent</h4>
                <p>{}</p>
            </div>
            """.format(plan.replace('\n', '<br>')), unsafe_allow_html=True)

        with st.spinner("ToolSelectorAgent working..."):
            tools = loop.run_until_complete(st.session_state.tools.run(plan))
            st.markdown("""
            <div class="agent-section tool-agent">
                <h4>🔧 ToolSelectorAgent</h4>
                <p>{}</p>
            </div>
            """.format(tools.replace('\n', '<br>')), unsafe_allow_html=True)

        with st.spinner("ForecasterAgent running..."):
            forecast = loop.run_until_complete(st.session_state.fore.run(tools))
            st.markdown("""
            <div class="agent-section forecaster-agent">
                <h4>📉 ForecasterAgent</h4>
                <p>{}</p>
            </div>
            """.format(forecast.replace('\n', '<br>')), unsafe_allow_html=True)

        st.markdown("""
        <div class="dashboard-card">
            <h3>📊 Final Inspection Plan Summary</h3>
        </div>
        """, unsafe_allow_html=True)
        st.code(forecast, language="markdown")

# ------------------- TAB 2: KG-Driven Structured Planner -------------------
with tab2:
    st.markdown("""
    <div class="dashboard-card">
        <h3>Knowledge Graph-Based Planning</h3>
        <p>Select material, defect type, and environment to generate an inspection plan based on our knowledge graph.</p>
    </div>
    """, unsafe_allow_html=True)

    # 🔄 Load options dynamically from Neo4j
    kg = KGInterface()
    material_options = kg.get_materials()
    deterioration_options = kg.get_deterioration_types()
    environment_options = kg.get_environments()
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Material")
        material = st.selectbox("Select Material", material_options, key="kg_material")

    with col2:
        st.markdown("#### Defect Type")
        deterioration = st.selectbox("Select Defect", deterioration_options, key="kg_defect")

    with col3:
        st.markdown("#### Environment")
        environment = st.selectbox("Select Environment", environment_options, key="kg_env")

    col1, col2 = st.columns([1, 3])
    with col1:
        run_kg = st.button("🧠 Plan KG-Based Inspection", key="run_kg", use_container_width=True)

    if run_kg:
        loop = st.session_state.loop

        col1, col2 = st.columns([3, 2])

        with col1:
            with st.spinner("ToolSelectorAgent analyzing KG..."):
                plan = loop.run_until_complete(
                    st.session_state.tools.run_structured(material, deterioration, environment)
                )
                st.markdown("""
                <div class="dashboard-card">
                    <h4>🔍 ToolSelectorAgent Decision</h4>
                </div>
                """, unsafe_allow_html=True)
                st.code(plan, language="markdown")

            with st.spinner("ForecasterAgent modeling damage evolution..."):
                forecast_context = f"""
                Material: {material}
                Defect: {deterioration}
                Environment: {environment}
                """
                forecast = loop.run_until_complete(st.session_state.fore.run(forecast_context))
                kg.log_inspection_plan(plan, material, deterioration, environment)

                st.markdown("""
                <div class="dashboard-card">
                    <h4>📈 Forecasted Deterioration (12-month projection)</h4>
                </div>
                """, unsafe_allow_html=True)
                st.text(forecast)
                render_forecast_chart(forecast)
                render_gantt_chart(forecast)

        with col2:
            st.markdown("""
            <div class="dashboard-card">
                <h4>👁 Knowledge Graph Reasoning Path</h4>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("Generating visualization..."):
                subgraph = kg.get_reasoning_subgraph(material, deterioration, environment)
                if subgraph:
                    render_kg_graph(subgraph)
                else:
                    st.warning("No subgraph data found for current inputs.")


# ------------------- TAB 3: Knowledge Graph Explorer -------------------
with tab3:
    st.markdown("""
    <div class="dashboard-card">
        <h3>Knowledge Graph Explorer</h3>
        <p>Explore and seed the knowledge graph that powers our NDT planning system.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="dashboard-card">
            <h4>📦 Node Counts by Type</h4>
        </div>
        """, unsafe_allow_html=True)
        
        counts = KGInterface().cypher("""
            MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC
        """)
        
        if counts:
            # Create a more visual representation of counts
            for row in counts:
                icon = '📦' if row['label'] == 'Material' else '🔍' if row['label'] == 'NDTMethod' else '🌡️' if row['label'] == 'Environment' else '💢' if row['label'] == 'Deterioration' else '📡' if row['label'] == 'Sensor' else '📌'
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                    <div style="font-size: 24px; margin-right: 15px;">{icon}</div>
                    <div style="flex-grow: 1;">
                        <div style="font-weight: bold;">{row['label']}</div>
                    </div>
                    <div style="background-color: #3498db; color: white; padding: 5px 15px; border-radius: 12px; font-weight: bold;">
                        {row['count']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No nodes found. Try seeding first.")
            
        if st.button("🧪 Seed Demo Knowledge Graph", key="tab3_seed", use_container_width=True):
            if seed_knowledge_graph():
                st.success("✅ KG seeded successfully!")
    
    with col2:
        st.markdown("""
        <div class="dashboard-card">
            <h4>🔗 Sample Relationships</h4>
        </div>
        """, unsafe_allow_html=True)
        
        rels = KGInterface().cypher("""
            MATCH (a)-[r]->(b)
            RETURN labels(a)[0] AS from, type(r) AS relation, labels(b)[0] AS to,
                   a.name AS from_name, b.name AS to_name
            LIMIT 10
        """)
        
        if rels:
            for rel in rels:
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                    <div style="background-color: #3498db; color: white; padding: 3px 10px; border-radius: 12px; margin-right: 10px;">
                        {rel['from']}
                    </div>
                    <div style="font-weight: bold; margin-right: 5px;">
                        {rel['from_name']}
                    </div>
                    <div style="color: #7f8c8d; margin: 0 10px;">
                        —[ {rel['relation']} ]→
                    </div>
                    <div style="font-weight: bold; margin-right: 5px;">
                        {rel['to_name']}
                    </div>
                    <div style="background-color: #2ecc71; color: white; padding: 3px 10px; border-radius: 12px;">
                        {rel['to']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No relationships found. Try seeding first.")
    
    # Direct Cypher query capability for advanced users
    st.markdown("""
    <div class="dashboard-card">
        <h4>🔍 Advanced Query</h4>
        <p>Run custom Cypher queries against the knowledge graph</p>
    </div>
    """, unsafe_allow_html=True)
    
    query = st.text_area("Enter Cypher query:", 
                        height=100,
                        value="""MATCH (n)-[r]->(m)
WHERE n:Material AND m:Deterioration
RETURN n.name AS Material, type(r) AS Relation, m.name AS Deterioration""")
    
    if st.button("🔎 Run Query", key="run_cypher", use_container_width=True):
        try:
            results = KGInterface().cypher(query)
            if results:
                st.dataframe(results, use_container_width=True)
            else:
                st.info("Query returned no results")
        except Exception as e:
            st.error(f"Query error: {str(e)}")

from utils.kg_exporter import export_kg_to_owl
from utils.shacl_validator import validate_owl_with_shacl

with st.sidebar.expander("🔁 KG Export / Validation"):
    if st.button("⬇️ Export to OWL"):
        # Optional: Extract real triples from KG
        export_kg_to_owl([
            ("Concrete", "hasDefect", "Cracking"),
            ("Cracking", "detectedBy", "Ultrasonic Testing")
        ])

    if st.button("✅ Run SHACL Validation"):
        conforms, report = validate_owl_with_shacl("ndt_kg.owl", "ontology/shapes.ttl")
        if conforms:
            st.success("KG conforms to SHACL constraints!")
        else:
            st.error("❌ KG does NOT conform!")
            st.text(report)




# Footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 20px; color: #7f8c8d; font-size: 0.8em;">
    Autonomous NDT Planning System | Powered by LLM + Knowledge Graph Technology<br>
    © 2025 All Rights Reserved
</div>
""", unsafe_allow_html=True)