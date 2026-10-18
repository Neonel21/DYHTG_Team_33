"""

Project Expedition33
Run:  streamlit run app.py
"""
import difflib
import itertools
import math
import re
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(page_title='Expedition33', page_icon='🎆', layout='wide')
DATA = Path(__file__).parent / 'data'
COLOUR = {'Mastermind': '#9085e9', 'Conspirator': '#d03b3b', 'Clear': '#5f5e5a'}
ICON = {'Mastermind': '🎯', 'Conspirator': '⛑', 'Clear': '·'}
NICKNAMES = {'Queen Margaret Union': ['qmu'], 'Glasgow University Union': ['guu'], 'The Hive': ['hive'],
             'Boyd Orr Building': ['boyd orr', 'boydy'], 'Kelvingrove Park': ['kelvingrove', 'kelvin grove', 'park'],
             'Wolfson Medical Building': ['wolfson']}


def mins(hhmm):
    hhmm = str(hhmm).zfill(4)
    return int(hhmm[:2]) * 60 + int(hhmm[2:])


def fmt(m):
    return f'{int(m // 60) % 24:02d}:{int(m % 60):02d}'


# --------------------------------------------------------------------------- 1. load & clean
@st.cache_data
def load():
    people = pd.read_csv(DATA / 'people_data.csv')
    logs = pd.read_csv(DATA / 'security_logs.csv')
    places = pd.read_csv(DATA / 'location_data.csv')
    statements = (DATA / 'student_statements.txt').read_text(encoding='utf-8')

    # buildings: coordinates and opening hours (closing after midnight rolls into the next day)
    xy = places['Geolocation'].str.strip('{}').str.split(expand=True).astype(float)
    places['Lat'], places['Lon'] = xy[0], xy[1]
    hours = places['Opening Times'].str.split('-', expand=True)
    places['Open'], places['Close'] = hours[0].map(mins), hours[1].map(mins)
    places.loc[places['Close'] <= places['Open'], 'Close'] += 24 * 60
    places.loc[(places['Open'] == 0) & (places['Close'] == 24 * 60), 'Close'] = 48 * 60   # the park never shuts

    # lecture timetable, read from the building descriptions
    lectures = {}
    for subject in people['Subject'].unique():
        for _, b in places.iterrows():
            m = re.search(re.escape(subject) + r' lectures (?:every day )?from (\d{4}) (?:to|until) (\d{4})',
                          b['Description'], re.I)
            if m:
                lectures[subject] = (b['Building Name'], mins(m[1]), mins(m[2]))

    # logs: keep the raw ID/place for evidence, then repair them
    people['Student ID'] = people['Student ID'].str.upper()
    known = set(places['Building Name'])
    logs['Raw ID'], logs['Raw place'] = logs['Student ID'], logs['Location']
    logs['Location'] = logs['Location'].map(
        lambda x: x if x in known else (difflib.get_close_matches(x, known, 1, 0.5) or [x])[0])
    t = logs['Time'].str.split('-', expand=True)
    logs['Start'], logs['End'] = t[0].map(mins), t[1].map(mins)
    logs.loc[logs['End'] <= logs['Start'], 'End'] += 24 * 60
    return people, logs.reset_index(drop=True), places, lectures, statements


people, logs, places, lectures, statements_text = load()
P = people.set_index('Name')
B = places.set_index('Building Name')


# --------------------------------------------------------------------------- 2. statements
def read_statements(text):
    out = {}
    for block in re.split(r'\n\s*Statement \d+\s*\n', '\n' + text):
        m = re.search(r'Student Number:\s*(\S+).*?Name:\s*(.+?)\n.*?Testimony:\s*(.+)', block, re.S)
        if m:
            out[m[2].strip()] = {'id': m[1].strip(), 'text': ' '.join(m[3].split())}
    return out


def places_claimed(text):
    """Buildings a statement says they went to (skipping sentences like 'was tempted to go to Hive')."""
    said = set()
    for sentence in re.split(r'(?<=[.!?…])\s+', text.lower().replace('’', "'")):
        if re.search(r"\b(tempted|tried to get me|wasn'?t|didn'?t|instead|had a plan)\b", sentence):
            continue
        for b in places['Building Name']:
            words = [b.lower(), b.lower().replace(' building', '')] + NICKNAMES.get(b, [])
            if b == 'Kelvin Building':
                words = ['kelvin building']
            if any(re.search(r'\b' + re.escape(w) + r'\b', sentence) for w in words):
                said.add(b)
    return said


statements = read_statements(statements_text)


# --------------------------------------------------------------------------- 3. red flags
@st.cache_data
def find_flags():
    flags = []                      # (name, severity, flag, detail, visit rows)
    for _, p in people.iterrows():
        name, sid = p['Name'], p['Student ID']
        day = logs[logs['Name'] == name].sort_values('Start')
        fake = day[day['Raw ID'] != sid]
        if len(fake):
            flags.append((name, 3, 'Logged under a false ID', f"logs say {fake['Raw ID'].iloc[0]}, real ID {sid}", list(fake.index)))
        for i, v in day.iterrows():
            if v['Raw place'] not in B.index:
                flags.append((name, 3, 'Building that doesn’t exist', f"'{v['Raw place']}' {fmt(v['Start'])}", [i]))
            o, c = B.loc[v['Location'], ['Open', 'Close']]
            s, e = (v['Start'], v['End']) if v['Start'] >= o else (v['Start'] + 1440, v['End'] + 1440)
            if not (o <= s and e <= c):
                flags.append((name, 3, 'Inside a closed building', f"{v['Location']} {fmt(v['Start'])}–{fmt(v['End'])}", [i]))
            if 'over 18' in B.loc[v['Location'], 'Description'].lower() and p['Age'] < 18:
                flags.append((name, 3, 'Under 18 in an 18+ club', f"age {p['Age']}, {v['Location']}", [i]))
        rows = list(day.iterrows())
        for (ia, a), (ib, b) in zip(rows, rows[1:]):
            if b['Start'] < a['End']:
                flags.append((name, 3, 'In two places at once', f"{a['Location']} and {b['Location']} at {fmt(b['Start'])}",
                              [ia, ib]))
        if p['Subject'] in lectures:
            lb, ls, le = lectures[p['Subject']]
            if day[(day['Location'] == lb) & (day['Start'] < le) & (day['End'] > ls)].empty:
                flags.append((name, 2, 'Skipped own lecture', f'{lb} {fmt(ls)}', []))
        if name in statements:
            st_ = statements[name]
            if st_['id'] != sid:
                flags.append((name, 2, 'Gave the wrong ID in interview', f"said {st_['id']}", []))
            missing = places_claimed(st_['text']) - set(day['Location'])
            for m in sorted(missing):
                flags.append((name, 2, 'Statement doesn’t match logs', f'says {m}, never logged there', []))
    return pd.DataFrame(flags, columns=['Name', 'Severity', 'Flag', 'Detail', 'Visits'])


flags = find_flags()
bad_visits = {v for vs in flags.loc[flags['Severity'] == 3, 'Visits'] for v in vs}


def meetings(a, b):
    """Every time a and b were logged in the same building at the same time."""
    out = []
    for _, x in logs[logs['Name'] == a].iterrows():
        for _, y in logs[(logs['Name'] == b) & (logs['Location'] == x['Location'])].iterrows():
            s, e = max(x['Start'], y['Start']), min(x['End'], y['End'])
            if e > s:
                out.append((x['Location'], s, e))
    return out


conspirators = sorted(flags.loc[flags['Severity'] == 3, 'Name'].unique())


@st.cache_data
def find_Mastermind(conspirators):
    clean = [n for n in people['Name'] if n not in set(flags['Name'])]
    met = {n: [c for c in conspirators if meetings(n, c)] for n in clean}
    best = max(met, key=lambda n: len(met[n]))
    return best, met[best]


Mastermind, Mastermind_met = find_Mastermind(tuple(conspirators))
role = {n: 'Mastermind' if n == Mastermind else 'Conspirator' if n in conspirators else 'Clear' for n in people['Name']}


# --------------------------------------------------------------------------- 4. communities (Louvain)
@st.cache_data
def find_communities():
    """Link students who share a society or spent 15+ minutes in the same building, then let Louvain group them."""
    G = nx.Graph()
    G.add_nodes_from(people['Name'])
    socs = people[['Name', 'Societies']].copy()
    socs['Societies'] = socs['Societies'].fillna('').str.findall(r"'([^']+)'|\"([^\"]+)\"").map(
        lambda found: {a or b for a, b in found})
    for society, members in socs.explode('Societies').dropna().groupby('Societies')['Name']:
        for a, b in itertools.combinations(sorted(set(members)), 2):
            G.add_edge(a, b, weight=G.get_edge_data(a, b, {'weight': 0})['weight'] + 1)
    for place, v in logs.groupby('Location'):
        v = v.sort_values('Start').to_dict('records')
        for i, a in enumerate(v):
            for b in v[i + 1:]:
                if b['Start'] >= a['End']:
                    break
                overlap = min(a['End'], b['End']) - b['Start']
                if a['Name'] != b['Name'] and overlap >= 15:
                    w = G.get_edge_data(a['Name'], b['Name'], {'weight': 0})['weight']
                    G.add_edge(a['Name'], b['Name'], weight=w + overlap / 60)
    groups = sorted(nx.community.louvain_communities(G, weight='weight', seed=42), key=len, reverse=True)
    community = {n: i for i, g in enumerate(groups) for n in g}

    short = {'Computing Science': 'Computing', 'Veterinary Medicine': 'Vet Med', 'English Literature': 'English Lit',
             'Mathematics': 'Maths'}

    def label(g):                                   # name each community after its main subjects
        top = people[people['Name'].isin(g)]['Subject'].value_counts()
        top.index = [short.get(s, s) for s in top.index]
        return top.index[0] if len(top) == 1 or top.iloc[1] < 3 else f'{top.index[0]} & {top.index[1]}'
    names = [label(g) for g in groups]

    # layout: each community in its own cluster, clusters arranged in a ring
    ring = nx.circular_layout(range(len(groups)), scale=3.2)
    pos = {}
    for i, g in enumerate(groups):
        local = nx.spring_layout(G.subgraph(g), weight='weight', seed=42)
        span = max(max(abs(x), abs(y)) for x, y in local.values()) or 1
        pos.update({n: (ring[i][0] + 1.1 * x / span, ring[i][1] + 1.1 * y / span) for n, (x, y) in local.items()})

    # how strongly each pair of communities is linked
    links = {}
    for a, b, d in G.edges(data=True):
        ca, cb = sorted((community[a], community[b]))
        if ca != cb:
            links[(ca, cb)] = links.get((ca, cb), 0) + d['weight']
    return groups, names, community, pos, ring, links


groups, group_names, community, positions, ring, community_links = find_communities()
GROUP_COLOURS = ['#3987e5', '#199e70', '#c98500', '#d55181', '#008300', '#7d7bb8', '#5f8fa8', '#a07a5a']


# --------------------------------------------------------------------------- 5. the page
st.title('Expedition33')
st.caption('DYHTG Hackathon project for SAS category.')

tab1, tab2, tab3, tab4 = st.tabs(['Overview', 'The Web Graph', 'Campus Map', 'Student Search'])

with tab1:
    c = st.columns(4)
    c[0].metric('Students', len(people))
    c[1].metric('Log entries', len(logs))
    c[2].metric('Conspirators', len(conspirators))
    c[3].metric('Mastermind', Mastermind)
    st.success(f'**{Mastermind}** has a spotless record. Was in the same place at the same time as '
               f'**{len(Mastermind_met)} of {len(conspirators)}** conspirators.')
    st.subheader('Who stands out')
    summary = (flags.drop_duplicates(['Name', 'Flag']).sort_values('Severity', ascending=False).groupby('Name')
               .agg(Score=('Severity', 'sum'), Why=('Flag', lambda f: ', '.join(dict.fromkeys(f))))
               .sort_values('Score', ascending=False).reset_index())
    summary.insert(0, 'Role', summary['Name'].map(lambda n: f"{ICON[role[n]]} {role[n]}"))
    st.dataframe(summary, hide_index=True, use_container_width=True)
    st.caption('Probability weight(Score): 3 points for each kind of thing that is impossible or against the rules, 2 for each thing that doesnt add up.')

with tab2:
    st.subheader('The suspects')
    st.caption('Drag the circles around. Hover a line to see where and when two people met.')
    net = Network(height='620px', width='100%', bgcolor='#111110', font_color='#f0efec', cdn_resources='in_line')
    for n in [Mastermind] + conspirators:
        net.add_node(n, label=n, color=COLOUR[role[n]], size=40 if n == Mastermind else 25,
                     title=f"{role[n]}\n" + '\n'.join(flags.loc[flags['Name'] == n, 'Flag'].unique()))
    group = [Mastermind] + conspirators
    for i, a in enumerate(group):
        for b in group[i + 1:]:
            m = meetings(a, b)
            if m:
                net.add_edge(a, b, title='\n'.join(f'{w} {fmt(s)}–{fmt(e)}' for w, s, e in m),
                             color=COLOUR['Mastermind'] if Mastermind in (a, b) else '#8a3a3a',
                             width=2 + sum(e - s for _, s, e in m) / 40)
    html = net.generate_html().replace('</body>', '''<script>
      new ResizeObserver(() => { if (typeof network !== 'undefined') { network.redraw(); network.fit(); } })
        .observe(document.getElementById('mynetwork'));
    </script><style>#mynetwork{border:none!important} .card{border:none!important}</style></body>''')
    components.html(html, height=640)
    st.markdown('🎯 purple = Mastermind  ·  ⛑ red = conspirator  ·  thicker line = longer together')

    # ---- community graphs
    st.divider()
    st.subheader('Communities')
    suspects_in = {i: [n for n in groups[i] if role[n] != 'Clear'] for i in range(len(groups))}
    spread = sum(1 for v in suspects_in.values() if v)
    st.caption(f'Every student, linked to anyone sharing a society or 15+ minutes in the same building, then grouped '
               f'with the Louvain method. The suspects are spread across **{spread} of {len(groups)}** communities, '
               f'so this isn’t one friendship group: someone had to bring them together.')
    left, right = st.columns([3, 2])

    # chart 1: everyone, clustered by community, suspects highlighted
    fig = go.Figure()
    for (a, b) in itertools.combinations([Mastermind] + conspirators, 2):
        if (a == Mastermind or b == Mastermind) and meetings(a, b):
            fig.add_scatter(x=[positions[a][0], positions[b][0]], y=[positions[a][1], positions[b][1]], mode='lines',
                            line=dict(color=COLOUR['Mastermind'], width=1.5), opacity=0.6, hoverinfo='skip', showlegend=False)
    for i, g in enumerate(groups):
        clear = [n for n in g if role[n] == 'Clear']
        fig.add_scatter(x=[positions[n][0] for n in clear], y=[positions[n][1] for n in clear], mode='markers',
                        marker=dict(size=7, color=GROUP_COLOURS[i % len(GROUP_COLOURS)]), opacity=0.55,
                        name=group_names[i], hovertext=[f'{n} · {P.loc[n, "Subject"]}' for n in clear], hoverinfo='text')
        fig.add_annotation(x=ring[i][0] * 1.45, y=ring[i][1] * 1.45, text=f'<b>{group_names[i]}</b><br>{len(g)} students',
                           showarrow=False, font=dict(color='#c3c2b7', size=12))
    for r in ['Conspirator', 'Mastermind']:
        who = [n for n in people['Name'] if role[n] == r]
        fig.add_scatter(x=[positions[n][0] for n in who], y=[positions[n][1] for n in who], mode='markers+text',
                        marker=dict(size=18 if r == 'Mastermind' else 13, color=COLOUR[r], line=dict(color='#111110', width=2)),
                        text=who, textposition='top center', textfont=dict(color='#f0efec', size=11),
                        name=r, hovertext=[f'{n} · {r} · {group_names[community[n]]}' for n in who], hoverinfo='text')
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), showlegend=False,
                      yaxis=dict(visible=False, scaleanchor='x'))
    left.markdown('**Everyone, grouped by community**')
    left.plotly_chart(fig, use_container_width=True, theme=None)
    left.caption('Small dots = students, coloured by community. Red = conspirator, purple = Mastermind '
                 '(lines show who the Mastermind met).')

    # chart 2: one circle per community, thicker line = more connected
    fig = go.Figure()
    top = max(community_links.values())
    for (a, b), w in community_links.items():
        fig.add_scatter(x=[ring[a][0], ring[b][0]], y=[ring[a][1], ring[b][1]], mode='lines',
                        line=dict(color='#4a4945', width=1 + 9 * w / top), hoverinfo='skip', showlegend=False)
    fig.add_scatter(x=[ring[i][0] for i in range(len(groups))], y=[ring[i][1] for i in range(len(groups))],
                    mode='markers+text', textposition='middle center',
                    marker=dict(size=[18 + 1.4 * len(g) for g in groups],
                                color=[GROUP_COLOURS[i % len(GROUP_COLOURS)] for i in range(len(groups))],
                                line=dict(color=['#d03b3b' if suspects_in[i] else '#111110' for i in range(len(groups))],
                                          width=[2 + 2 * len(suspects_in[i]) for i in range(len(groups))])),
                    text=[f'<b>{len(suspects_in[i])}</b>' if suspects_in[i] else '' for i in range(len(groups))],
                    textfont=dict(color='white', size=15),
                    hovertext=[f"{group_names[i]} · {len(g)} students<br>Suspects: {', '.join(suspects_in[i]) or 'none'}"
                               for i, g in enumerate(groups)], hoverinfo='text', showlegend=False)
    for i in range(len(groups)):
        fig.add_annotation(x=ring[i][0], y=ring[i][1] - 0.95, text=group_names[i], showarrow=False,
                           font=dict(color='#c3c2b7', size=12))
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False, range=[-5.2, 5.2]),
                      yaxis=dict(visible=False, range=[-4.6, 4.2], scaleanchor='x'))
    right.markdown('**How the communities connect**')
    right.plotly_chart(fig, use_container_width=True, theme=None)
    right.caption('One circle per community (bigger = more students). The number and red ring show how many '
                  'suspects are inside. Thicker line = more links between two communities.')


with tab3:
    t = st.select_slider('Time', options=list(range(3 * 60, 27 * 60 + 1, 10)), value=22 * 60 + 10, format_func=fmt)
    here = logs[(logs['Start'] <= t) & (logs['End'] > t)]
    left, right = st.columns([3, 1])
    fig = go.Figure()
    is_open = [(o <= t < c) or (o <= t + 1440 < c) for o, c in zip(places['Open'], places['Close'])]
    fig.add_scatter(x=places['Lon'], y=places['Lat'], mode='markers+text', text=places['Building Name'].str.replace(' Building', ''),
                    textposition='top center', marker=dict(size=22, color=['#2a3a55' if o else '#2a2a28' for o in is_open]),
                    textfont=dict(color=['#c3c2b7' if o else '#5f5e5a' for o in is_open]), hoverinfo='skip', showlegend=False)
    xs, ys, colours, sizes, labels = [], [], [], [], []
    for place, group_ in here.groupby('Location'):            
        lat, lon = B.loc[place, ['Lat', 'Lon']]
        for k, (idx, v) in enumerate(group_.iterrows()):
            r = 0.00009 * (k + 1) ** 0.5
            xs.append(lon + 1.8 * r * math.cos(k * 2.4))
            ys.append(lat + r * math.sin(k * 2.4))
            who = role[v['Name']]
            colours.append('#ff4d4d' if idx in bad_visits else COLOUR[who] if who != 'Clear' else '#8a8984')
            sizes.append(15 if idx in bad_visits or who != 'Clear' else 9)
            labels.append(f"{v['Name']} · {place} {fmt(v['Start'])}–{fmt(v['End'])}")
    fig.add_scatter(x=xs, y=ys, mode='markers', marker=dict(size=sizes, color=colours),
                    hovertext=labels, hoverinfo='text', showlegend=False)
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
    left.plotly_chart(fig, use_container_width=True, theme=None)
    left.caption('Since some students supplied inconsistent data, and broke rules, this was indicated' \
                 'with the following.' \
                 '\nDots = students (purple = Mastermind, red = conspirator). Bright red = breaking a rule right now. '
                 'Dimmed names = building closed. ')
    right.metric('On campus', len(here))
    for _, v in here[here.index.isin(bad_visits)].iterrows():
        right.error(f"**{v['Name']}** · {v['Location']}")

with tab4:
    order = [Mastermind] + conspirators + sorted(n for n in people['Name'] if role[n] == 'Clear' and n != Mastermind)
    name = st.selectbox('Student', order, format_func=lambda n: f'{ICON[role[n]]} {n}')
    p = P.loc[name]
    st.markdown(f"### {ICON[role[name]]} {name}  \n{p['Subject']}, year {p['Year of Study']} · age {p['Age']} · "
                f"ID {p['Student ID']} · **{role[name]}**")
    f = flags[flags['Name'] == name]
    if f.empty:
        st.success('No red flags.')
    for _, r in f.iterrows():
        (st.error if r['Severity'] == 3 else st.warning)(f"**{r['Flag']}**: {r['Detail']}")

    day = logs[logs['Name'] == name].sort_values('Start')
    fig = go.Figure(go.Bar(y=day['Location'], x=day['End'] - day['Start'], base=day['Start'], orientation='h',
                           marker_color=['#d03b3b' if i in bad_visits else '#3987e5' for i in day.index],
                           hovertext=[f"{r.Location} {fmt(r.Start)}–{fmt(r.End)}" for r in day.itertuples()],
                           hoverinfo='text'))
    ticks = list(range(3 * 60, 27 * 60 + 1, 120))
    fig.update_layout(height=80 + 45 * len(day), margin=dict(l=10, r=10, t=10, b=30), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c3c2b7', size=13),
                      xaxis=dict(tickvals=ticks, ticktext=[fmt(x) for x in ticks], range=[3 * 60, 27 * 60],
                                 gridcolor='#2c2c2a', automargin=True, showticklabels=True),
                      yaxis=dict(type='category', autorange='reversed', automargin=True, showticklabels=True))
    st.markdown('**Their day** (red = breaks a rule)')
    st.plotly_chart(fig, use_container_width=True, theme=None)

    if name in statements:
        st.markdown('**What they told security**')
        st.info(statements[name]['text'])
    if name == Mastermind:
        st.markdown('**Meetings with conspirators**')
        st.dataframe(pd.DataFrame([(c, w, fmt(s), fmt(e)) for c in conspirators for w, s, e in meetings(name, c)],
                                  columns=['Conspirator', 'Where', 'From', 'To']), hide_index=True, use_container_width=True)
