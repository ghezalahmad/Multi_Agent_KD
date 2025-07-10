import sys
from pathlib import Path
import time

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))  
import streamlit as st
import asyncio
from utils.graph_vis import render_kg_graph
from utils.forecast_chart import render_forecast_chart
from agents.planner_agent import PlannerAgent
from agents.tool_agent import ToolSelectorAgent
from agents.forecaster_agent import ForecasterAgent
from agents.critique_agent import CritiqueAgent
from agents.risk_assessment_agent import RiskAssessmentAgent # Added
from kg_interface import KGInterface
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

    .critique-agent-custom {
        background-color: #f0f0f0; /* Light grey background */
        border-left: 4px solid #777; /* Dark grey border */
    }

    .risk-agent-custom {
        background-color: #fff0f0; /* Light red background */
        border-left: 4px solid #c00; /* Dark red border */
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

# Helper function to display agent outputs consistently
def display_agent_output(title: str, html_content: str, css_class: str, icon: str = "🤖"):
    st.markdown(f"""
    <div class="agent-section {css_class}">
        <h4>{icon} {title}</h4>
        <p>{html_content}</p>
    </div>
    """, unsafe_allow_html=True)

# Helper function to display agent outputs consistently
def display_agent_output(title: str, html_content: str, css_class: str, icon: str = "🤖"):
    st.markdown(f"""
    <div class="agent-section {css_class}">
        <h4>{icon} {title}</h4>
        <p>{html_content}</p>
    </div>
    """, unsafe_allow_html=True)

def render_focused_forecast_ui(loop, recommended_methods_list: list, forecaster_agent, base_context_parts: dict, key_suffix: str):
    st.markdown("---")
    st.markdown("#### Focused Deterioration Forecast")

    if recommended_methods_list:
        selected_methods = st.multiselect(
            "Select NDT Method(s) for Focused Forecast:",
            options=recommended_methods_list,
            key=f"focused_select_{key_suffix}"
        )
        if st.button("Re-run Forecast for Selected", key=f"rerun_forecast_{key_suffix}"):
            if selected_methods:
                # Construct context string based on what's in base_context_parts
                context_lines = [f"Focusing on NDT methods: {', '.join(selected_methods)}."]
                if "user_input" in base_context_parts: # Tab 1 like context
                    context_lines.append(f"Original user query: {base_context_parts['user_input']}")
                    context_lines.append(f"Initial plan context: {base_context_parts['plan_agent_output']}")
                    context_lines.append(f"Tool selection context: {base_context_parts['tools_summary']}")
                elif "material" in base_context_parts: # Tab 2 like context
                    context_lines.append(f"Original context: Material: {base_context_parts['material']}, Defect: {base_context_parts['defect']}, Environment: {base_context_parts['environment']}")

                focused_context_rerun = "\n".join(context_lines)

                with st.spinner("ForecasterAgent running focused forecast..."):
                    focused_forecast_output = loop.run_until_complete(forecaster_agent.run(focused_context_rerun))
                    st.markdown("##### Focused Forecast Results:")
                    st.code(focused_forecast_output, language="markdown")
                    if "material" in base_context_parts: # Only render charts if it's from structured planner (Tab2-like) for now
                        render_forecast_chart(focused_forecast_output)
                        render_gantt_chart(focused_forecast_output)
            else:
                st.warning("Please select at least one NDT method for focused forecast.")
    else:
        st.info("No specific NDT methods available to allow focused forecast.")

def render_feedback_buttons(kg_interface_instance: KGInterface, session_state_plan_id_key: str, key_suffix: str):
    st.markdown("---")
    st.markdown("##### Was this plan helpful?")
    fb_col1, fb_col2 = st.columns(2)
    current_plan_id = st.session_state.get(session_state_plan_id_key)

    with fb_col1:
        if st.button("👍 Yes", key=f"helpful_{key_suffix}", use_container_width=True):
            if current_plan_id:
                kg_interface_instance.log_plan_feedback(plan_id=current_plan_id, is_helpful=True)
                st.toast("🙏 Thank you for your feedback!", icon="👍")
            else:
                st.toast("Error: Plan ID not found for feedback.", icon="⚠️")
    with fb_col2:
        if st.button("👎 No", key=f"unhelpful_{key_suffix}", use_container_width=True):
            if current_plan_id:
                # Potentially add a text input here for detailed feedback if "No"
                # feedback_text = st.text_input("Please provide details (optional):", key=f"feedback_text_{key_suffix}")
                kg_interface_instance.log_plan_feedback(plan_id=current_plan_id, is_helpful=False) #, feedback_text=feedback_text if feedback_text else None)
                st.toast("🙏 Thank you! Your feedback helps us improve.", icon="💡")
            else:
                st.toast("Error: Plan ID not found for feedback.", icon="⚠️")

def seed_knowledge_graph():
    kg = KGInterface()
    seed_query = """
    MERGE (m:Material {name: "Concrete"})
        SET m.commonApplications = "Buildings, Bridges, Foundations", m.description = "A composite material composed of fine and coarse aggregate bonded together with a fluid cement that hardens over time."
    MERGE (m2:Material {name: "Steel"})
        SET m2.commonApplications = "Structural frames, Reinforcement, Pipelines", m2.description = "An alloy of iron and carbon, widely used in construction for its high tensile strength."
    MERGE (m3:Material {name: "Wood"})
        SET m3.commonApplications = "Framing, Furniture, Decorative elements", m3.description = "A natural composite material, primarily composed of cellulose fibers."

    MERGE (d1:Deterioration {name: "Cracking"})
        SET d1.detailedDescription = "A linear fracture in a material, which can vary in width, depth, and orientation. Can be surface-breaking or internal, and may propagate under stress."
    MERGE (d2:Deterioration {name: "Corrosion"})
        SET d2.detailedDescription = "The degradation of a material, typically a metal, due to chemical or electrochemical reactions with its environment. Results in material loss and formation of oxides."
    MERGE (d3:Deterioration {name: "Delamination"})
        SET d3.detailedDescription = "The separation of layers in a composite material or laminated structure, or layers of concrete from a substrate. Can be caused by impact, moisture, or thermal stresses."

    MERGE (pc1:PhysicalChange {name: "Spalling"})
        SET pc1.detailedDescription = "The flaking or chipping away of a material's surface, often seen in concrete due to corrosion of rebar or freeze-thaw cycles."

    MERGE (e1:Environment {name: "Humid"})
    MERGE (e2:Environment {name: "Dry"})
    MERGE (e3:Environment {name: "Submerged"})
    MERGE (e4:Environment {name: "High Temperature"})

    MERGE (n1:NDTMethod {name: "Ultrasonic Testing"})
        SET n1.description = "Uses high-frequency sound waves to detect internal flaws and characterize material thickness.", n1.costEstimate = "Medium", n1.methodCategory = "Volumetric",
            n1.detectionCapabilities = "Detects internal and surface flaws like cracks, voids, and delaminations; measures thickness.", n1.applicableMaterialsNote = "Requires good acoustic coupling; highly attenuative or geometrically complex materials can be challenging.",
            n1.methodLimitations = "Requires skilled operator; surface must be accessible and relatively smooth; not ideal for very thin materials or complex geometries without specialized techniques."
    MERGE (n2:NDTMethod {name: "GPR"})
        SET n2.description = "Ground Penetrating Radar uses electromagnetic waves to image the subsurface.", n2.costEstimate = "High", n2.methodCategory = "Volumetric"
    MERGE (n3:NDTMethod {name: "Thermography"})
        SET n3.description = "Infrared thermography detects temperature differences to find defects like delaminations or moisture.", n3.costEstimate = "Medium", n3.methodCategory = "Surface"
    MERGE (n5:NDTMethod {name: "Visual Inspection"})
        SET n5.description = "The oldest and most common NDT method, relying on direct observation of the material surface.", n5.costEstimate = "Low", n5.methodCategory = "Surface",
            n5.detectionCapabilities = "Detects surface-breaking defects, discoloration, and gross anomalies visible to the naked eye or with low magnification.", n5.applicableMaterialsNote = "Effectiveness depends on surface condition, lighting, and inspector skill. May require surface cleaning.",
            n5.methodLimitations = "Only detects surface-breaking defects; cannot determine internal structure or depth of defects; effectiveness highly dependent on lighting, access, and inspector acuity. May require surface cleaning for optimal results."
    MERGE (n4:NDTMethod {name: "Acoustic Emission"})
        SET n4.description = "Passively listens for energy releases (acoustic emissions) from active cracks or defects under stress.", n4.costEstimate = "High", n4.methodCategory = "Volumetric"

    MERGE (s1:Sensor {name: "Acoustic Sensor"})
    MERGE (s2:Sensor {name: "Thermal Camera"})
    MERGE (s3:Sensor {name: "Moisture Sensor"})

    MERGE (risk1:RiskType {name: "Safety Hazard - Working at Heights"})
        SET risk1.riskDescription = "Risk of falls or injury when inspecting structures at significant heights without proper safety equipment or procedures.",
            risk1.mitigationSuggestion = "Use scaffolding, aerial work platforms, fall arrest systems. Ensure personnel are trained for working at heights."
    MERGE (risk2:RiskType {name: "Material Contamination Risk"})
        SET risk2.riskDescription = "Some NDT methods (e.g., certain penetrants or couplants) may leave residues that could contaminate sensitive materials or affect subsequent processes.",
            risk2.mitigationSuggestion = "Use approved, low-residue consumables. Perform thorough post-inspection cleaning procedures."
    MERGE (risk3:RiskType {name: "Equipment Accessibility Issue"})
        SET risk3.riskDescription = "The inspection area may be difficult to access with bulky NDT equipment or require extensive setup.",
            risk3.mitigationSuggestion = "Plan access routes. Use portable or miniaturized equipment if available. Consider remote inspection techniques."

    MERGE (n1)-[:hasPotentialRisk]->(risk3)
    MERGE (n5)-[:hasPotentialRisk]->(risk1)

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
    st.session_state.critique = CritiqueAgent()
    st.session_state.risk = RiskAssessmentAgent() # Added RiskAssessmentAgent

# Create a sidebar for navigation and stats
with st.sidebar:
    st.markdown("### 📊 Knowledge Graph Stats")
    
    counts = KGInterface().cypher("""
        MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC
    """)
    
    if counts:
        for row in counts:
            st.markdown(f"""
            <div class="icon-text">
                <span>{'📦' if row['label'] == 'Material' else '🔍' if row['label'] == 'NDTMethod' else '🌡️' if row['label'] == 'Environment' else '💢' if row['label'] == 'Deterioration' else '📡' if row['label'] == 'Sensor' else 'ρίσκο' if row['label'] == 'RiskType' else '📌'}</span>
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
tab1, tab2, tab3, tab4 = st.tabs([
    "🗣️ Natural Language Planner", 
    "📎 Structured Planner", 
    "🔍 Knowledge Graph Explorer", 
    "📚 Ontology Builder"
])

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

    col1_run_nl, col2_run_nl = st.columns([1, 3])
    with col1_run_nl:
        run_nl = st.button("🔍 Plan Inspection", key="run_nl", use_container_width=True)
    
    if user_input and run_nl:
        loop = st.session_state.loop
        kg_instance_tab1 = KGInterface() # Instance for KG calls in this tab

        st.markdown("#### Inspection Planning Process")
        
        with st.spinner("PlannerAgent thinking..."):
            plan_agent_output_tab1 = loop.run_until_complete(st.session_state.plan.run(user_input))
            plan_agent_output_tab1_html = plan_agent_output_tab1.replace('\n', '<br>')
            display_agent_output("PlannerAgent", plan_agent_output_tab1_html, "planner-agent", icon="🧠")

        with st.spinner("ToolSelectorAgent working..."):
            tool_agent_output_tab1 = loop.run_until_complete(st.session_state.tools.run(plan_agent_output_tab1))
            tools_summary_tab1 = tool_agent_output_tab1.get("summary_text", "")
            recommended_methods_tab1_list = tool_agent_output_tab1.get("recommended_methods", [])
            tools_summary_tab1_html = tools_summary_tab1.replace('\n', '<br>')
            display_agent_output("ToolSelectorAgent", tools_summary_tab1_html, "tool-agent", icon="🔧")

        with st.spinner("CritiqueAgent reviewing recommendations..."):
            rag_details_for_critique_tab1 = ""
            if recommended_methods_tab1_list:
                rag_details_for_critique_tab1 = kg_instance_tab1.get_entities_details_for_rag(
                    method_names=recommended_methods_tab1_list
                    # Material & defect names for RAG in Tab 1 are implicitly part of user_input/planner_output
                    # get_entities_details_for_rag can handle None for material/defect names
                )
            critique_context_tab1 = (
                f"**Scenario Context (from user input & planner):**\nUser Input: {user_input}\nPlanner Output: {plan_agent_output_tab1}\n\n"
                f"**Proposed NDT Approach by ToolSelectorAgent:**\n{tools_summary_tab1}\n" # summary_text already contains method names
                f"**Detailed NDT Method Information (from Knowledge Graph for RAG):**\n{rag_details_for_critique_tab1}"
            )
            critique_output_tab1 = loop.run_until_complete(st.session_state.critique.run(critique_context_tab1))
            critique_output_tab1_html = critique_output_tab1.replace('\n', '<br>')
            # Using a generic class name, specific style is inline
            display_agent_output("Critique & Considerations", critique_output_tab1_html, "critique-agent-custom", icon="🕵️‍♂️")


        with st.spinner("RiskAssessmentAgent analyzing potential risks..."):
            rag_details_for_risk_tab1 = rag_details_for_critique_tab1 # Reuse RAG details which now include risks
            risk_context_tab1 = (
                f"**Scenario Context (from user input & planner):**\nUser Input: {user_input}\nPlanner Output: {plan_agent_output_tab1}\n\n"
                f"**Proposed NDT Methods:** {', '.join(recommended_methods_tab1_list)}\n\n"
                f"**Detailed NDT Method Information (including potential risks from KG):**\n{rag_details_for_risk_tab1}"
            )
            risk_output_tab1 = loop.run_until_complete(st.session_state.risk.run(risk_context_tab1))
            risk_output_tab1_html = risk_output_tab1.replace('\n', '<br>')
            # Using a generic class name, specific style is inline
            display_agent_output("Potential Risk Analysis", risk_output_tab1_html, "risk-agent-custom", icon="⚠️")

        forecast_text_tab1 = ""
        with st.spinner("ForecasterAgent running..."):
            # Context for forecaster should ideally include selected NDT methods.
            # For now, using ToolSelector's summary.
            forecaster_context_tab1 = f"{tools_summary_tab1}\nCritique: {critique_output_tab1}\nRisks: {risk_output_tab1}"
            forecast_text_tab1 = loop.run_until_complete(st.session_state.fore.run(forecaster_context_tab1))
            forecast_text_tab1_html = forecast_text_tab1.replace('\n', '<br>')
            display_agent_output("ForecasterAgent", forecast_text_tab1_html, "forecaster-agent", icon="📉")

        st.markdown("""
        <div class="dashboard-card">
            <h3>📊 Final Inspection Plan Summary</h3>
        </div>
        """, unsafe_allow_html=True)
        st.code(forecast_text_tab1, language="markdown")

        # Use the refactored UI function for focused forecast
        tab1_focused_forecast_context_parts = {
            "user_input": user_input,
            "plan_agent_output": plan_agent_output_tab1, # Ensure this is available in scope
            "tools_summary": tools_summary_tab1 # Ensure this is available
        }
        render_focused_forecast_ui(loop, recommended_methods_tab1_list, st.session_state.fore, tab1_focused_forecast_context_parts, "tab1")

        if 'current_plan_id_tab1' not in st.session_state: # Initialize for Tab 1
            st.session_state.current_plan_id_tab1 = None

        if forecast_text_tab1:
            # Log the inspection plan for Tab 1
            # Extract material, defect, environment from tool_agent_output_tab1
            extracted_material_tab1 = tool_agent_output_tab1.get("extracted_material", "NL_Derived_Unknown")
            extracted_defect_tab1 = tool_agent_output_tab1.get("extracted_defect", "NL_Derived_Unknown")
            extracted_environment_tab1 = tool_agent_output_tab1.get("extracted_environment", "NL_Derived_Unknown")

            # Ensure values are not "unknown" which might be too generic for KG properties
            if extracted_material_tab1 == "unknown": extracted_material_tab1 = "NL_Derived_Unknown"
            if extracted_defect_tab1 == "unknown": extracted_defect_tab1 = "NL_Derived_Unknown"
            if extracted_environment_tab1 == "unknown": extracted_environment_tab1 = "NL_Derived_Unknown"

            st.session_state.current_plan_id_tab1 = kg_instance_tab1.log_inspection_plan(
                plan_text=forecast_text_tab1, # Using forecast as the plan text
                material=extracted_material_tab1,
                defect=extracted_defect_tab1,
                environment=extracted_environment_tab1
            )
            if st.session_state.current_plan_id_tab1:
                st.caption(f"Plan logged with ID: {st.session_state.current_plan_id_tab1}")

            # Use the refactored UI function for feedback buttons
            render_feedback_buttons(kg_instance_tab1, "current_plan_id_tab1", "tab1")

# ------------------- TAB 2: KG-Driven Structured Planner -------------------
with tab2:
    st.markdown("""
    <div class="dashboard-card">
        <h3>Knowledge Graph-Based Planning</h3>
        <p>Select material, defect type, and environment to generate an inspection plan based on our knowledge graph.</p>
    </div>
    """, unsafe_allow_html=True)

    kg_tab2_instance = KGInterface()
    material_options = kg_tab2_instance.get_materials()
    deterioration_options = kg_tab2_instance.get_deterioration_types()
    environment_options = kg_tab2_instance.get_environments()
    
    col1_kg, col2_kg, col3_kg = st.columns(3)

    with col1_kg:
        st.markdown("#### Material")
        material = st.selectbox("Select Material", material_options, key="kg_material")

    with col2_kg:
        st.markdown("#### Defect Type")
        deterioration = st.selectbox("Select Defect", deterioration_options, key="kg_defect")

    with col3_kg:
        st.markdown("#### Environment")
        environment = st.selectbox("Select Environment", environment_options, key="kg_env")

    col1_run_kg, col2_run_kg = st.columns([1, 3])
    with col1_run_kg:
        run_kg = st.button("🧠 Plan KG-Based Inspection", key="run_kg", use_container_width=True)

    if 'current_plan_id_tab2' not in st.session_state:
        st.session_state.current_plan_id_tab2 = None

    if run_kg:
        loop = st.session_state.loop
        st.session_state.current_plan_id_tab2 = None

        col1_results_kg, col2_results_kg = st.columns([3, 2])

        with col1_results_kg:
            with st.spinner("ToolSelectorAgent analyzing KG..."):
                tool_agent_output_tab2 = loop.run_until_complete(
                    st.session_state.tools.run_structured(material, deterioration, environment)
                )
                plan_summary_tab2 = tool_agent_output_tab2.get("summary_text", "")
                recommended_methods_tab2_list = tool_agent_output_tab2.get("recommended_methods", [])

                st.markdown("""
                <div class="dashboard-card">
                    <h4>🔍 ToolSelectorAgent Decision</h4>
                </div>
                """, unsafe_allow_html=True)
                st.code(plan_summary_tab2, language="markdown")

            with st.spinner("CritiqueAgent reviewing recommendations..."):
                rag_details_for_critique_tab2 = kg_tab2_instance.get_entities_details_for_rag(
                    material_name=material,
                    defect_name=deterioration,
                    method_names=recommended_methods_tab2_list
                )
                critique_context_tab2 = (
                    f"**Scenario:**\n"
                    f"Material: {material}\n"
                    f"Defect/Observation: {deterioration}\n"
                    f"Environment: {environment}\n\n"
                    f"**Proposed NDT Approach by ToolSelectorAgent:**\n{plan_summary_tab2}\n"
                    f"**Detailed NDT Method Information (from Knowledge Graph for RAG):**\n{rag_details_for_critique_tab2}"
                )
                critique_output_tab2 = loop.run_until_complete(st.session_state.critique.run(critique_context_tab2))
                critique_output_tab2_html = critique_output_tab2.replace('\n', '<br>')
                display_agent_output("Critique & Considerations", critique_output_tab2_html, "critique-agent-custom", icon="🕵️‍♂️")

            with st.spinner("RiskAssessmentAgent analyzing potential risks..."):
                # RAG details already include risk information due to previous step
                rag_details_for_risk_tab2 = rag_details_for_critique_tab2
                risk_context_tab2 = (
                    f"**Scenario Context:**\nMaterial: {material}\nDefect/Observation: {deterioration}\nEnvironment: {environment}\n\n"
                    f"**Proposed NDT Methods:** {', '.join(recommended_methods_tab2_list)}\n\n"
                    f"**Detailed NDT Method Information (including potential risks from KG):**\n{rag_details_for_risk_tab2}"
                )
                risk_output_tab2 = loop.run_until_complete(st.session_state.risk.run(risk_context_tab2))
                risk_output_tab2_html = risk_output_tab2.replace('\n', '<br>')
                display_agent_output("Potential Risk Analysis", risk_output_tab2_html, "risk-agent-custom", icon="⚠️")

            forecast_text_tab2 = ""
            with st.spinner("ForecasterAgent modeling damage evolution..."):
                forecast_context_tab2_initial = f"""
                Material: {material}
                Defect: {deterioration}
                Environment: {environment}
                Recommended NDT Methods by ToolSelector: {', '.join(recommended_methods_tab2_list) if recommended_methods_tab2_list else "None specified"}
                Critique: {critique_output_tab2}
                Risks: {risk_output_tab2}
                """
                forecast_text_tab2 = loop.run_until_complete(st.session_state.fore.run(forecast_context_tab2_initial))

                plan_id_tab2 = kg_tab2_instance.log_inspection_plan(plan_summary_tab2, material, deterioration, environment)
                if 'current_plan_id_tab2' not in st.session_state:
                    st.session_state.current_plan_id_tab2 = None
                st.session_state.current_plan_id_tab2 = plan_id_tab2

                st.markdown("""
                <div class="dashboard-card">
                    <h4>📈 Forecasted Deterioration (12-month projection)</h4>
                </div>
                """, unsafe_allow_html=True)
                st.text(forecast_text_tab2)
                render_forecast_chart(forecast_text_tab2)
                render_gantt_chart(forecast_text_tab2)

                # Use the refactored UI function for focused forecast
                tab2_focused_forecast_context_parts = {
                    "material": material, # Ensure this is available in scope
                    "defect": deterioration, # Ensure this is available
                    "environment": environment # Ensure this is available
                }
                render_focused_forecast_ui(loop, recommended_methods_tab2_list, st.session_state.fore, tab2_focused_forecast_context_parts, "tab2")

                if forecast_text_tab2:
                    # Use the refactored UI function for feedback buttons
                    render_feedback_buttons(kg_tab2_instance, "current_plan_id_tab2", "tab2")

        with col2_results_kg:
            st.markdown("""
            <div class="dashboard-card">
                <h4>👁 Knowledge Graph Reasoning Path</h4>
            </div>
            """, unsafe_allow_html=True)

            if run_kg:
                with st.spinner("Generating visualization..."):
                    subgraph = kg_tab2_instance.get_reasoning_subgraph(material, deterioration, environment)
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
    
    col1_exp, col2_exp = st.columns(2)
    
    with col1_exp:
        st.markdown("""
        <div class="dashboard-card">
            <h4>📦 Node Counts by Type</h4>
        </div>
        """, unsafe_allow_html=True)
        
        counts = KGInterface().cypher("""
            MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC
        """)
        
        if counts:
            for row in counts:
                icon = '📦' if row['label'] == 'Material' else '🔍' if row['label'] == 'NDTMethod' else '🌡️' if row['label'] == 'Environment' else '💢' if row['label'] == 'Deterioration' else '📡' if row['label'] == 'Sensor' else 'ρίσκο' if row['label'] == 'RiskType' else '📌'
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
    
    with col2_exp:
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

# ------------------- TAB 4: Ontology Builder -------------------
from agents.ontology_agent import OntologyBuilderAgent

with tab4:
    st.markdown("""
    <div class="dashboard-card">
        <h3>📚 Ontology Builder</h3>
        <p>Generate OWL axioms from competency questions using a local Ollama-powered LLM.</p>
    </div>
    """, unsafe_allow_html=True)

    cq_input = st.text_area("✍️ Enter one or more competency questions (one per line):", height=150)
    uploaded_file = st.file_uploader("📄 Or upload a .txt file", type=["txt"])

    cqs = []
    if uploaded_file:
        lines = uploaded_file.read().decode("utf-8").splitlines()
        cqs = [line.strip() for line in lines if line.strip()]
    elif cq_input.strip():
        cqs = [line.strip() for line in cq_input.split("\n") if line.strip()]

    if st.button("🔁 Run Ontology Builder"):
        if not cqs:
            st.warning("Please input or upload at least one question.")
        else:
            loop = st.session_state.loop
            agent = OntologyBuilderAgent()
            results = []
            latencies = []

            with st.spinner("Running LLM for all CQs..."):
                for cq_item in cqs:
                    start = time.time()
                    try:
                        axiom = loop.run_until_complete(agent.run(cq_item))
                        results.append((cq_item, axiom))
                        latencies.append(time.time() - start)
                    except Exception as e:
                        results.append((cq_item, f"# ERROR: {str(e)}"))
                        latencies.append(0)

            for i, (cq_item, axiom) in enumerate(results, start=1):
                st.markdown(f"### CQ {i}: {cq_item}")
                st.code(axiom.strip(), language="markdown")

            if results:
                avg_latency = sum(latencies) / len(latencies)
                st.success(f"✅ Done! Avg generation time: {avg_latency:.2f}s")

            if st.button("💾 Export Results"):
                import datetime
                from pathlib import Path
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = Path("outputs/ontology/")
                out_path.mkdir(parents=True, exist_ok=True)
                file_path = out_path / f"ontology_output_{timestamp}.ttl"
                with open(file_path, "w", encoding="utf-8") as f:
                    for cq_item, axiom in results:
                        f.write(f"# CQ: {cq_item}\n{axiom}\n\n")
                st.success(f"Ontology saved to {file_path}")
         
    st.markdown("""
    <div class="dashboard-card">
        <h4>🔍 Advanced Query</h4>
        <p>Run custom Cypher queries against the knowledge graph</p>
    </div>
    """, unsafe_allow_html=True)
    
    query_text_area = st.text_area("Enter Cypher query:",
                        height=100,
                        value="""MATCH (n)-[r]->(m)
WHERE n:Material AND m:Deterioration
RETURN n.name AS Material, type(r) AS Relation, m.name AS Deterioration""")
    
    if st.button("🔎 Run Query", key="run_cypher", use_container_width=True):
        try:
            results_cypher = KGInterface().cypher(query_text_area)
            if results_cypher:
                st.dataframe(results_cypher, use_container_width=True)
            else:
                st.info("Query returned no results")
        except Exception as e:
            st.error(f"Query error: {str(e)}")

from utils.kg_exporter import export_kg_to_owl
from utils.shacl_validator import validate_owl_with_shacl

with st.sidebar.expander("🔁 KG Export / Validation"):
    if st.button("⬇️ Export KG to Turtle/OWL"):
        try:
            kg_interface_for_export = KGInterface() # Create an instance for the export
            output_filename = "ndt_knowledge_graph.ttl"
            export_kg_to_owl(kg_interface_for_export, output_file=output_filename)
            st.success(f"Knowledge Graph exported to `{output_filename}` successfully!")
            with open(output_filename, "rb") as fp:
                st.download_button(
                    label="Download Exported KG",
                    data=fp,
                    file_name=output_filename,
                    mime="text/turtle"
                )
        except Exception as e:
            st.error(f"Error during KG export: {e}")
            # Consider logging the full traceback here for debugging
            # import traceback
            # st.text_area("Error details:", traceback.format_exc(), height=200)


    if st.button("✅ Run SHACL Validation"):
        conforms = False # Initialize conforms
        report = ""      # Initialize report
        # It's better to let the user upload the file they want to validate,
        # or validate the most recently exported file if that's the workflow.
        # For now, assuming validation of the default exported file.
        exported_file_to_validate = "ndt_knowledge_graph.ttl"
        shacl_constraints_file = "shacl/shacl_constraints.ttl"

        if not Path(exported_file_to_validate).exists():
            st.warning(f"File `{exported_file_to_validate}` not found. Please export the KG first.")
        elif not Path(shacl_constraints_file).exists():
            st.error(f"SHACL constraints file `{shacl_constraints_file}` not found.")
        else:
            try:
                conforms, report = validate_owl_with_shacl(exported_file_to_validate, shacl_constraints_file)
                if conforms:
                    st.success(f"`{exported_file_to_validate}` conforms to SHACL constraints!")
                else:
                    st.error(f"❌ `{exported_file_to_validate}` does NOT conform to SHACL constraints!")
                    st.text_area("Validation Report:", report, height=300)
            except Exception as e:
                st.error(f"Error during SHACL validation: {e}")
                # import traceback
                # st.text_area("Error details:", traceback.format_exc(), height=200)
        # The success/error messages are now inside the try/except block based on validation result.
        # The final "if conforms:" block outside is redundant if messages are handled inside.
        # I will remove the final if/else for conforms/report as it's handled above.

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 20px; color: #7f8c8d; font-size: 0.8em;">
    Autonomous NDT Planning System | Powered by LLM + Knowledge Graph Technology<br>
    © 2025 All Rights Reserved
</div>
""", unsafe_allow_html=True)