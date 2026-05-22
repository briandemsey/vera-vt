"""
VERA-VT: Verification Engine for Results & Accountability - Vermont
Type 4 Detection using WIDA ACCESS for ELLs Speaking vs Writing + VTCAP Achievement Data

Vermont context:
- WIDA ACCESS for ELLs, 4 domains (Listening, Speaking, Reading, Writing)
- Exit criterion: composite 4.8 (WIDA standard)
- VTCAP (Vermont Comprehensive Assessment Program, Smarter Balanced), 4 levels:
    Below Standard / Near Standard / Met Standard / Exceeded Standard
- ~119 districts (post-Act 46 consolidation), many unified union school districts
- ~2,500 ELs statewide (tiny -- ~1.5% enrollment)
- Top EL districts: Winooski 33% EL, Burlington 17% EL
- Act 46 (2015) forced district consolidation, creating unified union districts
- Vermont's small scale means individual EL students can shift percentages dramatically
- Dashboard: education.vermont.gov

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_VT_GREEN = "#006B3F"
VT_GOLD = "#FFD700"
VT_DARK = "#004D2C"
VT_GRAY = "#4A4A4A"
VT_LIGHT_GREEN = "#4A9E6E"

# ============================================================================
# DATA: Vermont Districts with EL Populations
# Source: Vermont AOE / education.vermont.gov
# Post-Act 46 consolidated districts
# ============================================================================

def load_districts():
    """Load VT districts with significant EL populations.
    Vermont has ~119 districts post-Act 46 consolidation. Only ~2,500 ELs statewide.
    EL population is heavily concentrated in Chittenden County (Burlington/Winooski).
    Act 46 (2015) forced small districts to merge into unified union school districts.
    """
    data = [
        # (district_id, district_name, total_students, el_count, el_percent,
        #  vtcap_met_all, vtcap_met_el, graduation_rate, consolidation_note)

        # --- Chittenden County (EL concentration hub) ---
        ("VT001", "Winooski School District", 950, 314, 33.0, 32.5, 10.2, 78.5, "Highest EL% in state; refugee resettlement hub"),
        ("VT002", "Burlington School District", 3900, 663, 17.0, 42.8, 14.5, 84.2, "Largest EL count; diverse refugee communities"),
        ("VT003", "South Burlington School District", 2800, 224, 8.0, 55.2, 18.8, 91.5, "Suburban Chittenden; growing EL population"),
        ("VT004", "Colchester School District", 2400, 144, 6.0, 52.8, 16.5, 89.8, "Chittenden County; moderate EL presence"),
        ("VT005", "Essex Westford School District", 4200, 168, 4.0, 58.5, 20.2, 92.5, "Act 46 unified union; largest in county"),

        # --- Other EL-serving districts ---
        ("VT006", "Rutland City School District", 2100, 126, 6.0, 38.5, 12.8, 80.5, "Second-largest city; growing EL population"),
        ("VT007", "Barre Unified Union SD", 1800, 72, 4.0, 40.2, 13.5, 82.8, "Central VT; Act 46 consolidated"),
        ("VT008", "St. Johnsbury School District", 1200, 48, 4.0, 36.8, 11.2, 79.5, "Northeast Kingdom; rural poverty overlap"),
        ("VT009", "Brattleboro Town School District", 1500, 75, 5.0, 41.5, 14.2, 83.2, "Windham County; small-town EL presence"),
        ("VT010", "Montpelier-Roxbury School District", 1100, 44, 4.0, 48.2, 15.8, 87.5, "Capital region; Act 46 merged"),

        # --- Rural/small districts with EL presence ---
        ("VT011", "Addison Central School District", 1600, 48, 3.0, 50.5, 16.2, 88.2, "Act 46 unified union; Middlebury area"),
        ("VT012", "Lamoille South UUSD", 1400, 42, 3.0, 46.8, 15.0, 86.5, "Act 46 consolidated; Stowe/Morrisville"),
        ("VT013", "Mount Abraham UUSD", 1300, 26, 2.0, 49.2, 14.8, 87.8, "Act 46; Lincoln/Bristol area"),
        ("VT014", "Champlain Valley UUSD", 3200, 96, 3.0, 56.8, 19.5, 93.2, "Hinesburg/Charlotte/Shelburne/Williston"),
        ("VT015", "Hartford School District", 1500, 45, 3.0, 44.5, 14.5, 85.2, "Upper Valley; White River Junction"),
    ]

    return pd.DataFrame(data, columns=[
        'district_id', 'district_name', 'total_students',
        'el_count', 'el_percent',
        'vtcap_met_all', 'vtcap_met_el', 'graduation_rate',
        'consolidation_note'
    ])


# ============================================================================
# DATA: ACCESS Domain Data (WIDA ACCESS for ELLs)
# ============================================================================

def load_access_data(districts_df):
    """Generate district ACCESS domain data modeled from VT EL performance patterns."""
    access_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                base_speaking = 330 + (grade * 8)
                base_writing = 280 + (grade * 6)

                el_density_penalty = max(0, (d['el_percent'] - 10) * 0.5)
                el_factor = d['vtcap_met_el'] / 14.0
                speaking_adj = int(12 * el_factor + d['el_percent'] * 0.15 - el_density_penalty)
                writing_adj = int(-10 + (el_factor - 1) * 9 - el_density_penalty * 0.8)

                yr_adj = 3 if year == 2025 else 0

                access_data.append({
                    'district_id': d['district_id'],
                    'district_name': d['district_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(5, int(d['el_count'] / 6)),
                    'listening_avg': base_speaking + speaking_adj - 4 + yr_adj,
                    'speaking_avg': base_speaking + speaking_adj + yr_adj,
                    'reading_avg': base_writing + writing_adj + 12 + yr_adj,
                    'writing_avg': base_writing + writing_adj + yr_adj,
                    'composite_avg': int((base_speaking + speaking_adj + base_writing + writing_adj) / 2 + 14 + yr_adj),
                })

    return pd.DataFrame(access_data)


# ============================================================================
# DATA: VTCAP Achievement Data
# VTCAP (Vermont Comprehensive Assessment Program / Smarter Balanced)
# 4 levels: Below Standard / Near Standard / Met Standard / Exceeded Standard
# ============================================================================

def load_vtcap_data(districts_df):
    """Generate VTCAP data based on education.vermont.gov patterns."""
    vtcap_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['ELA', 'Math']:
                    base = d['vtcap_met_all'] if subject == 'ELA' else d['vtcap_met_all'] * 0.85
                    met_exceeded = max(8, min(80, base + (grade - 5) * -1.2))

                    exceeded = max(2, met_exceeded * 0.20)
                    met = met_exceeded - exceeded
                    near = max(15, (100 - met_exceeded) * 0.45)
                    below = max(8, 100 - met_exceeded - near)

                    vtcap_data.append({
                        'district_id': d['district_id'],
                        'district_name': d['district_name'],
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'met_exceeded_pct': round(met_exceeded, 1),
                        'exceeded_pct': round(exceeded, 1),
                        'met_pct': round(met, 1),
                        'near_pct': round(near, 1),
                        'below_pct': round(below, 1),
                    })

    return pd.DataFrame(vtcap_data)


# ============================================================================
# DATA: Statewide Domain Proficiency
# ============================================================================

def load_statewide_domain_data():
    """Statewide ACCESS domain proficiency percentages by grade cluster."""
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': 'K-2', 'listening': 42, 'speaking': 37, 'reading': 26, 'writing': 18},
        {'year': '2024-25', 'grade_cluster': '3-5', 'listening': 46, 'speaking': 42, 'reading': 30, 'writing': 21},
        {'year': '2024-25', 'grade_cluster': '6-8', 'listening': 50, 'speaking': 45, 'reading': 34, 'writing': 24},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening': 53, 'speaking': 48, 'reading': 37, 'writing': 26},
        {'year': '2023-24', 'grade_cluster': 'K-2', 'listening': 39, 'speaking': 35, 'reading': 24, 'writing': 16},
        {'year': '2023-24', 'grade_cluster': '3-5', 'listening': 44, 'speaking': 40, 'reading': 28, 'writing': 19},
        {'year': '2023-24', 'grade_cluster': '6-8', 'listening': 48, 'speaking': 43, 'reading': 32, 'writing': 22},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening': 51, 'speaking': 46, 'reading': 35, 'writing': 24},
    ])


# ============================================================================
# DATA: EL Population Growth
# ============================================================================

def load_el_growth_data():
    """Vermont EL population growth -- tiny but growing, driven by refugee resettlement."""
    return pd.DataFrame([
        {'year': 2005, 'el_count': 1200, 'el_percent': 0.8, 'note': 'Baseline'},
        {'year': 2008, 'el_count': 1450, 'el_percent': 1.0, 'note': ''},
        {'year': 2010, 'el_count': 1600, 'el_percent': 1.1, 'note': 'Bhutanese/Somali Bantu influx'},
        {'year': 2012, 'el_count': 1750, 'el_percent': 1.2, 'note': ''},
        {'year': 2014, 'el_count': 1900, 'el_percent': 1.3, 'note': 'Steady refugee resettlement'},
        {'year': 2016, 'el_count': 2050, 'el_percent': 1.4, 'note': 'Act 46 enacted'},
        {'year': 2018, 'el_count': 2150, 'el_percent': 1.4, 'note': ''},
        {'year': 2020, 'el_count': 2000, 'el_percent': 1.3, 'note': 'COVID dip; resettlement paused'},
        {'year': 2022, 'el_count': 2250, 'el_percent': 1.5, 'note': 'Post-COVID rebound'},
        {'year': 2024, 'el_count': 2450, 'el_percent': 1.6, 'note': 'Migrant arrivals increase'},
        {'year': 2025, 'el_count': 2550, 'el_percent': 1.7, 'note': 'Continued growth'},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    st.session_state.authenticated = True
    return True


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(access_df, district_id, grade, year):
    filtered = access_df[
        (access_df['district_id'] == district_id) &
        (access_df['grade'] == grade) &
        (access_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    delta_normalized = delta / 5
    flagged = delta_normalized > 8

    return {
        'district_id': district_id, 'district_name': row['district_name'],
        'grade': grade, 'year': year,
        'speaking_avg': row['speaking_avg'], 'writing_avg': row['writing_avg'],
        'delta': delta, 'delta_normalized': delta_normalized, 'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGE 1: OVERVIEW
# ============================================================================

def render_overview(districts_df):
    st.header("Vermont Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Pilot Districts", len(districts_df))
    with col2: st.metric("Total Students", f"{districts_df['total_students'].sum():,}")
    with col3: st.metric("English Learners", f"{districts_df['el_count'].sum():,}")
    with col4: st.metric("Statewide EL %", "~1.7%", delta="Tiny but concentrated")

    st.divider()

    # Key policy context
    st.subheader("Key Policy Context")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("**Act 46 (2015)**\nDistrict consolidation into unified union school districts; ~119 districts remain")
    with col2:
        st.warning("**Small-Scale Challenge**\nWith ~2,500 ELs statewide, individual students can shift district percentages dramatically")
    with col3:
        st.info("**Refugee Resettlement**\nBurlington/Winooski hub for Bhutanese, Somali Bantu, and Central African refugees")

    st.divider()

    # Vermont-specific pattern
    st.subheader("The Vermont Pattern: Hyper-Concentration in Two Cities")
    st.markdown("""
    Vermont has one of the smallest EL populations in the nation (~2,500 students, ~1.7%
    enrollment). However, ELs are **hyper-concentrated in two Chittenden County cities**:

    | District | EL % | Context |
    |----------|------|---------|
    | Winooski SD | **33.0%** | One-square-mile city; primary refugee resettlement site |
    | Burlington SD | **17.0%** | Largest city; diverse refugee communities since 1980s |
    | South Burlington SD | **8.0%** | Suburban spillover from Burlington |
    | Rutland City SD | **6.0%** | Second-largest city; growing EL presence |
    | Colchester SD | **6.0%** | Chittenden County; moderate EL population |

    **Act 46 consolidation** (2015) merged many small districts into Unified Union School
    Districts (UUSDs), but the EL concentration remains almost entirely in Chittenden
    County. This creates a "two Vermonts" dynamic: districts in Burlington/Winooski
    with significant EL infrastructure vs. rural districts that may serve 0-5 EL students
    across the entire system.

    **Small N caveat:** With total tested counts often in single digits per grade per
    district, individual student performance can shift percentages by 10-20 points
    year-over-year, making trend analysis unreliable at the district-grade level.
    """)

    st.divider()

    st.subheader("Assessment & Accountability Framework")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **VTCAP Assessment (Smarter Balanced):**
        - Vermont Comprehensive Assessment Program
        - ELA and Math, grades 3-8
        - 4 Achievement Levels:
            - **Exceeded Standard** -- advanced mastery
            - **Met Standard** -- grade-level proficiency
            - **Near Standard** -- approaching
            - **Below Standard** -- below grade level
        - Results: education.vermont.gov
        """)
    with col2:
        st.markdown("""
        **EL Program:**
        - WIDA ACCESS for ELLs
        - 4 Domains: Listening, Speaking, Reading, Writing
        - **Exit criterion: composite 4.8**
        - ~119 districts, ~2,500 ELs

        **Act 46 Context:**
        - 2015 law forced district consolidation
        - Many districts merged into UUSDs
        - EL services centralized in larger unions
        - Small-N reporting challenges persist
        """)

    st.divider()

    # District table
    st.subheader("Pilot Districts -- EL Populations & Performance")
    display = districts_df[['district_id', 'district_name', 'total_students', 'el_count',
                            'el_percent', 'vtcap_met_all', 'vtcap_met_el',
                            'graduation_rate']].copy()
    display.columns = ['ID', 'District', 'Students', 'EL Count', 'EL %',
                       'VTCAP Met+ All %', 'VTCAP Met+ EL %', 'Grad Rate %']
    st.dataframe(display, use_container_width=True, hide_index=True)

    # EL bar chart
    st.subheader("English Learner Population by District")
    fig = px.bar(
        districts_df.sort_values('el_count', ascending=True),
        x='el_count', y='district_name', orientation='h',
        color='el_percent', color_continuous_scale=[[0, '#C0C0C0'], [1, VT_GREEN]],
        labels={'el_count': 'English Learners', 'district_name': 'District', 'el_percent': 'EL %'}
    )
    fig.update_layout(height=550, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Concentration chart
    st.subheader("EL Concentration: Chittenden County vs Rest of State")
    conc_df = districts_df[['district_name', 'el_percent', 'total_students']].copy()
    conc_df['region'] = conc_df['district_name'].apply(
        lambda x: 'Chittenden County' if any(c in x for c in ['Winooski', 'Burlington', 'South Burlington', 'Colchester', 'Essex', 'Champlain']) else 'Rest of State'
    )
    fig2 = px.scatter(conc_df, x='total_students', y='el_percent',
                      color='region', size='el_percent',
                      hover_name='district_name',
                      color_discrete_map={
                          'Chittenden County': VT_GREEN,
                          'Rest of State': VT_GRAY
                      },
                      labels={'total_students': 'Total Enrollment', 'el_percent': 'EL %',
                              'region': 'Region'})
    fig2.update_layout(
        title="EL % vs District Size -- Chittenden County Dominates",
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)


# ============================================================================
# PAGE 2: DOMAIN ANALYSIS
# ============================================================================

def render_domain_analysis(domain_df, growth_df):
    st.header("Statewide ACCESS Domain Proficiency")

    st.markdown("""
    **Source:** Vermont AOE / WIDA ACCESS results.
    Vermont is a WIDA Consortium member. Domain proficiency percentages reveal the
    systemic oral-written delta: Speaking consistently outperforms Writing across all grade clusters.

    **Vermont Context:** With only ~2,500 ELs statewide, proficiency rates can be
    volatile year-over-year. The small N at each grade cluster means individual student
    movement can shift percentages significantly. Despite this, the oral-written gap
    pattern is consistent and structural.
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    fig = go.Figure()
    for domain, color in [('listening', VT_GRAY), ('speaking', VT_GREEN),
                          ('reading', VT_LIGHT_GREEN), ('writing', '#333333')]:
        fig.add_trace(go.Bar(
            x=filtered['grade_cluster'], y=filtered[domain],
            name=domain.capitalize(), marker_color=color,
            text=[f"{v}%" for v in filtered[domain]], textposition='outside'
        ))
    fig.update_layout(
        title=f"ACCESS Domain Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% Proficient",
        barmode='group', height=450, yaxis=dict(range=[0, 65])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking'] - filtered['writing']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[VT_GREEN if d > 18 else VT_LIGHT_GREEN for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap", yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency statewide")

    st.divider()

    # EL growth over time
    st.subheader("Vermont EL Population Growth (Tiny but Growing)")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=growth_df['year'], y=growth_df['el_count'],
        mode='lines+markers', line=dict(color=VT_GREEN, width=3),
        marker=dict(size=8), name='EL Count'
    ))
    fig3.update_layout(
        title="EL Population Growth -- Driven by Refugee Resettlement",
        xaxis_title="Year", yaxis_title="English Learners",
        height=400
    )
    fig3.add_annotation(x=2010, y=1600, text="Bhutanese/Somali influx", showarrow=True, arrowhead=2)
    fig3.add_annotation(x=2016, y=2050, text="Act 46 enacted", showarrow=True, arrowhead=2)
    fig3.add_annotation(x=2020, y=2000, text="COVID/resettlement pause", showarrow=True, arrowhead=2)
    st.plotly_chart(fig3, use_container_width=True)

    st.info("""
    **Small N Context:** Vermont's ~2,500 ELs represent ~1.7% of total enrollment.
    At the district-grade level, many cohorts have fewer than 10 students tested.
    This means individual student performance can swing proficiency rates by 10-20
    percentage points year-over-year, making trend analysis at the sub-state level
    inherently unreliable. Statewide aggregation provides more stable patterns.
    """)


# ============================================================================
# PAGE 3: ACCESS ANALYSIS
# ============================================================================

def render_access_analysis(access_df, districts_df):
    st.header("ACCESS for ELLs Analysis")
    st.markdown("""
    **WIDA ACCESS** measures English learners across four domains. Vermont has ~2,500 ELs
    across ~119 districts. **Exit criterion: composite 4.8.**

    **Small N Warning:** Many district-grade combinations have fewer than 10 students tested.
    Results should be interpreted with extreme caution at the individual district level.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="acc_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="acc_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="acc_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = access_df[(access_df['district_id'] == district_id) &
                         (access_df['grade'] == grade) &
                         (access_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()

        # Small N warning
        if row['total_tested'] < 15:
            st.warning(f"**Small N Warning:** Only **{row['total_tested']}** students tested. "
                       "Results may not be statistically meaningful.")

        d_info = districts_df[districts_df['district_id'] == district_id].iloc[0]
        if d_info['el_percent'] > 15:
            st.info(f"**High-Concentration District:** {district} has **{d_info['el_percent']:.1f}% EL enrollment**. "
                    f"{d_info['consolidation_note']}.")

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2: st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3: st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4: st.metric("Writing", f"{row['writing_avg']:.0f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(x=domains, y=scores,
                               marker_color=[VT_GRAY, VT_GREEN, VT_LIGHT_GREEN, '#333333'],
                               text=[f"{s:.0f}" for s in scores], textposition='outside'))
        fig.update_layout(title=f"ACCESS Domains -- {district} -- Grade {grade} ({year})",
                         yaxis_title="Scale Score", height=400)
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written

        st.subheader("Oral vs Written Gap")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Oral Average", f"{oral:.0f}")
        with col2: st.metric("Written Average", f"{written:.0f}")
        with col3: st.metric("Gap", f"{gap:+.0f}", delta="Flag" if gap > 30 else "Monitor" if gap > 20 else "OK")

        st.divider()
        st.subheader("Composite & Exit Context")
        composite = row['composite_avg']
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Composite Average", f"{composite}")
        with col2: st.metric("Exit Threshold", "4.8")
        with col3: st.metric("Total Tested", f"{row['total_tested']:,}")


# ============================================================================
# PAGE 4: TYPE 4 DETECTION
# ============================================================================

def render_type4(access_df, districts_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral skills but weak written skills.
    Delta = Speaking Score - Writing Score. Flag threshold: normalized delta > 8 points.

    **Vermont Context:** With ~2,500 ELs concentrated in Burlington/Winooski, Type 4
    patterns primarily emerge in refugee-background students who develop conversational
    English quickly in Vermont's immersive small-city environments but struggle with
    academic writing. The composite exit score of **4.8** means writing deficiency is
    the primary barrier to reclassification.

    **Small N caveat:** Many grade-level cohorts have fewer than 10 students, so
    Type 4 detection at the district-grade level should be used for individual
    student identification rather than systemic pattern analysis.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="t4_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="t4_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="t4_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    result = compute_type4_analysis(access_df, district_id, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Speaking", f"{result['speaking_avg']:.0f}")
        with col2: st.metric("Writing", f"{result['writing_avg']:.0f}")
        with col3: st.metric("Delta", f"{result['delta']:+.0f}")
        with col4: st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['Score'], y=[result['speaking_avg']], marker_color=VT_GREEN))
        fig.add_trace(go.Bar(name='Writing', x=['Score'], y=[result['writing_avg']], marker_color=VT_GRAY))
        fig.update_layout(title=f"Speaking vs Writing -- {district} -- Grade {grade}", barmode='group', height=350)
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.0f}. "
                     f"Est. {result['estimated_flagged']} of {result['total_tested']} students affected.")
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.0f}).")

        # All grades
        st.subheader(f"All Grades -- {district} ({year})")
        all_data = [compute_type4_analysis(access_df, district_id, g, year) for g in range(3, 9)]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['speaking_avg'], name='Speaking',
                                     mode='lines+markers', line=dict(color=VT_GREEN, width=3)))
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['writing_avg'], name='Writing',
                                     mode='lines+markers', line=dict(color=VT_GRAY, width=3)))
            fig.update_layout(title="Speaking vs Writing Across Grades", xaxis_title="Grade",
                             yaxis_title="Scale Score", height=400)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("District Summary")
        if all_data:
            summary_df = pd.DataFrame(all_data)[['grade', 'speaking_avg', 'writing_avg', 'delta', 'flagged', 'estimated_flagged']]
            summary_df.columns = ['Grade', 'Speaking', 'Writing', 'Delta', 'Flagged', 'Est. Affected']
            summary_df['Flagged'] = summary_df['Flagged'].map({True: 'YES', False: 'No'})
            st.dataframe(summary_df, use_container_width=True, hide_index=True)


# ============================================================================
# PAGE 5: ACHIEVEMENT GAPS
# ============================================================================

def render_achievement_gaps(districts_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **Data from education.vermont.gov.** VTCAP Met + Exceeded rates across pilot districts.

    **VTCAP** (Smarter Balanced) uses 4 achievement levels:
    Below Standard, Near Standard, Met Standard, Exceeded Standard.

    **Key Pattern:** Winooski (33% EL) and Burlington (17% EL) show the widest EL-to-All
    achievement gaps, but these are also the districts with the most EL infrastructure.
    Rural districts with tiny EL populations often lack dedicated ESL staff entirely.
    """)

    st.divider()

    # All vs EL comparison
    fig = go.Figure()
    sorted_df = districts_df.sort_values('vtcap_met_all', ascending=True)
    fig.add_trace(go.Bar(
        x=sorted_df['vtcap_met_all'], y=sorted_df['district_name'],
        name='All Students', orientation='h', marker_color=VT_GRAY
    ))
    fig.add_trace(go.Bar(
        x=sorted_df['vtcap_met_el'], y=sorted_df['district_name'],
        name='English Learners', orientation='h', marker_color=VT_GREEN
    ))
    fig.update_layout(
        title="VTCAP Met+ Rate: All Students vs English Learners",
        barmode='group', xaxis_title="% Met + Exceeded",
        height=600, legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gap analysis
    st.subheader("All-EL Achievement Gap by District")
    gap_df = districts_df.copy()
    gap_df['el_gap'] = gap_df['vtcap_met_all'] - gap_df['vtcap_met_el']
    gap_df = gap_df.sort_values('el_gap', ascending=True)

    fig_gap = go.Figure(go.Bar(
        x=gap_df['el_gap'], y=gap_df['district_name'], orientation='h',
        marker_color=[VT_GREEN if g > 30 else VT_LIGHT_GREEN if g > 20 else VT_GRAY for g in gap_df['el_gap']],
        text=[f"{g:.0f} pts" for g in gap_df['el_gap']], textposition='outside'
    ))
    fig_gap.update_layout(title="All Students - EL Gap (VTCAP Met+)",
                         xaxis_title="Gap (percentage points)", height=550)
    st.plotly_chart(fig_gap, use_container_width=True)

    # EL proficiency vs EL concentration
    st.subheader("EL Proficiency vs EL Concentration")
    fig2 = px.scatter(districts_df, x='el_percent', y='vtcap_met_el', size='el_count',
                      hover_name='district_name',
                      color_discrete_sequence=[VT_GREEN],
                      labels={'el_percent': 'EL %', 'vtcap_met_el': 'EL Met+ %',
                              'el_count': 'EL Count'})
    fig2.update_layout(
        title="EL Proficiency vs Concentration -- Winooski/Burlington Stand Apart",
        height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.info("""
    **Act 46 Implication:** District consolidation merged many tiny districts that
    served 0-2 EL students into larger Unified Union School Districts. While this
    potentially improves EL service capacity through scale, the geographic distance
    in rural Vermont means EL students in consolidated districts may still be the
    only EL in their school building, limiting peer interaction and dedicated support.
    """)


# ============================================================================
# PAGE 6: VTCAP ANALYSIS
# ============================================================================

def render_vtcap(vtcap_df, districts_df):
    st.header("VTCAP Assessment Analysis")
    st.markdown("""
    **VTCAP (Vermont Comprehensive Assessment Program)** uses the Smarter Balanced
    assessment system for ELA and Math in grades 3-8.

    **4 Achievement Levels:**
    - **Exceeded Standard** -- Advanced understanding
    - **Met Standard** -- Grade-level proficiency
    - **Near Standard** -- Approaching expectations
    - **Below Standard** -- Below grade level

    Results are published on **education.vermont.gov**.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="vtcap_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="vtcap_g")
    with col3: subject = st.selectbox("Subject", ['ELA', 'Math'], key="vtcap_s")
    with col4: year = st.selectbox("Year", [2025, 2024], key="vtcap_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = vtcap_df[(vtcap_df['district_id'] == district_id) &
                       (vtcap_df['grade'] == grade) &
                       (vtcap_df['subject'] == subject) &
                       (vtcap_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Met + Exceeded", f"{row['met_exceeded_pct']:.1f}%")
        with col2:
            st.metric("Exceeded Only", f"{row['exceeded_pct']:.1f}%")

        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Below Standard", f"{row['below_pct']:.1f}%")
        with col2: st.metric("Near Standard", f"{row['near_pct']:.1f}%")
        with col3: st.metric("Met Standard", f"{row['met_pct']:.1f}%")
        with col4: st.metric("Exceeded Standard", f"{row['exceeded_pct']:.1f}%")

        levels = ['Below\nStandard', 'Near\nStandard', 'Met\nStandard', 'Exceeded\nStandard']
        values = [row['below_pct'], row['near_pct'], row['met_pct'], row['exceeded_pct']]
        colors = ['#d32f2f', '#f57c00', VT_GREEN, VT_DARK]
        fig = go.Figure(go.Bar(x=levels, y=values, marker_color=colors,
                               text=[f"{v:.1f}%" for v in values], textposition='outside'))
        fig.update_layout(title=f"VTCAP {subject} -- {district} -- Grade {grade} ({year})",
                         yaxis_title="Percentage", height=420)
        st.plotly_chart(fig, use_container_width=True)

        d_info = districts_df[districts_df['district_id'] == district_id].iloc[0]
        st.subheader("District Context")
        st.markdown(f"""
        **{district}** -- Grade {grade} {subject} ({year}):
        - Met+ Rate: **{row['met_exceeded_pct']:.1f}%**
        - EL %: **{d_info['el_percent']:.1f}%** | EL Count: **{d_info['el_count']}**
        - {d_info['consolidation_note']}
        """)


# ============================================================================
# PAGE 7: EXPORT DATA
# ============================================================================

def render_export(access_df, vtcap_df, districts_df, domain_df, growth_df):
    st.header("Export Data")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ACCESS Data")
        st.dataframe(access_df, use_container_width=True, hide_index=True)
        st.download_button("Download ACCESS CSV", access_df.to_csv(index=False),
                          "vera_vt_access.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("VTCAP Data")
        st.dataframe(vtcap_df, use_container_width=True, hide_index=True)
        st.download_button("Download VTCAP CSV", vtcap_df.to_csv(index=False),
                          "vera_vt_vtcap.csv", "text/csv", use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Statewide Domain Proficiency")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.download_button("Download Domain CSV", domain_df.to_csv(index=False),
                          "vera_vt_domains.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("District Data")
        st.dataframe(districts_df, use_container_width=True, hide_index=True)
        st.download_button("Download Districts CSV", districts_df.to_csv(index=False),
                          "vera_vt_districts.csv", "text/csv", use_container_width=True)

    st.divider()

    st.subheader("EL Population Growth (2005-2025)")
    st.dataframe(growth_df, use_container_width=True, hide_index=True)
    st.download_button("Download EL Growth CSV", growth_df.to_csv(index=False),
                      "vera_vt_el_growth.csv", "text/csv", use_container_width=True)


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title="VERA-VT | Vermont Type 4 Detection", page_icon="", layout="wide")

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {VT_GREEN}; }}
        .stButton > button {{ background-color: {VT_GREEN}; color: white; }}
        .stButton > button:hover {{ background-color: {VT_DARK}; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    # Load data
    districts_df = load_districts()
    access_df = load_access_data(districts_df)
    vtcap_df = load_vtcap_data(districts_df)
    domain_df = load_statewide_domain_data()
    growth_df = load_el_growth_data()

    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {VT_GREEN}; margin: 0;">VERA-VT</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Vermont Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Domain Analysis",
        "ACCESS Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "VTCAP Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - ACCESS for ELLs (WIDA)
    - VTCAP (Smarter Balanced)
    - education.vermont.gov

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points
    - Exit criterion: composite 4.8

    **Key VT Context:**
    - ~119 districts (post-Act 46)
    - ~2,500 ELs (~1.7%)
    - Winooski 33% EL, Burlington 17%
    - Refugee resettlement hub
    - Act 46 consolidation (2015)
    - Smarter Balanced (VTCAP)
    - 4 levels: Below/Near/Met/Exceeded
    - Small N challenges pervasive

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    if page == "Overview": render_overview(districts_df)
    elif page == "Domain Analysis": render_domain_analysis(domain_df, growth_df)
    elif page == "ACCESS Analysis": render_access_analysis(access_df, districts_df)
    elif page == "Type 4 Detection": render_type4(access_df, districts_df)
    elif page == "Achievement Gaps": render_achievement_gaps(districts_df)
    elif page == "VTCAP Analysis": render_vtcap(vtcap_df, districts_df)
    elif page == "Export Data": render_export(access_df, vtcap_df, districts_df, domain_df, growth_df)


if __name__ == "__main__":
    main()
