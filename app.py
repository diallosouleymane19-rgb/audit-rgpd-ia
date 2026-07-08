"""
SMD Dashboard — Interface de pilotage SMD Global Consulting LLC
Streamlit Cloud — https://share.streamlit.io

Pages :
  1. KPIs          — Indicateurs clés (Notion API)
  2. CRM Pipeline  — Pipeline prospects (Notion)
  3. Rapport IA    — Generateur micro-audit RGPD + AI Act (Claude Sonnet)
  4. Routeur SMD   — Envoyer instruction en langage naturel aux agents Make
  5. Marketing     — Contenus LinkedIn generés (Notion)
  6. Systeme       — Etat des scenaris Make
"""

import streamlit as st
import requests
import json
from datetime import date

try:
    from generate_rapport_docx import generer_rapport
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SMD Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Notion DBs
NOTION_DB_CRM       = "40fb8514-337d-4550-b899-743383a02169"
NOTION_DB_DASHBOARD = "ad90d1fd-7f41-400b-97bc-3098faa335a5"
NOTION_DB_MARKETING = "7abdb6fc-eae3-43de-afd5-71252ab60f0e"
NOTION_API_VER      = "2022-06-28"

# Make webhooks
MAKE_WEBHOOK_ROUTEUR = "https://hook.eu1.make.com/5hbyls7ztgpvc76avtx06h3gfpbi4u2o"
MAKE_SCENARIOS = [
    {"id": "6258440", "nom": "Routeur-LLM",             "emoji": "🔀"},
    {"id": "6259845", "nom": "Agent Admin Convertir",   "emoji": "🏢"},
    {"id": "6259927", "nom": "Agent Admin Archiver",    "emoji": "📁"},
    {"id": "6245020", "nom": "Agent Commercial",        "emoji": "📧"},
    {"id": "6245203", "nom": "Agent Marketing",         "emoji": "📢"},
    {"id": "6260014", "nom": "Alertes Erreurs SMD",     "emoji": "🔔"},
    {"id": "6260071", "nom": "Dashboard KPIs (daily)",  "emoji": "📊"},
]

# Anthropic
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL   = "claude-sonnet-4-5"

# ─────────────────────────────────────────────────────────────
# HELPERS SECRETS
# ─────────────────────────────────────────────────────────────

def get_notion_token():
    try:
        return st.secrets["notion"]["token"]
    except Exception:
        return None

def get_make_key():
    try:
        return st.secrets["make"]["api_key"]
    except Exception:
        return None

def get_anthropic_key():
    try:
        return st.secrets["anthropic"]["api_key"]
    except Exception:
        return None

def notion_headers():
    token = get_notion_token()
    if not token:
        return None
    return {
        "Authorization": "Bearer " + token,
        "Notion-Version": NOTION_API_VER,
        "Content-Type": "application/json",
    }

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://i.imgur.com/placeholder.png", width=60) if False else None
    st.markdown("## 🧠 SMD Dashboard")
    st.markdown("*SMD Global Consulting LLC*")
    st.divider()
    page = st.radio(
        "Navigation",
        [
            "📊 KPIs",
            "🏢 CRM Pipeline",
            "🔬 Rapport IA",
            "🔀 Routeur SMD",
            "📢 Marketing",
            "⚙️ Systeme",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Secrets configurés :")
    st.caption("Notion : " + ("✅" if get_notion_token() else "❌ manquant"))
    st.caption("Make   : " + ("✅" if get_make_key()    else "❌ manquant"))
    st.caption("Claude : " + ("✅" if get_anthropic_key() else "❌ manquant"))

# ─────────────────────────────────────────────────────────────
# PAGE 1 — KPIs
# ─────────────────────────────────────────────────────────────
if page == "📊 KPIs":
    st.title("📊 Tableau de bord KPIs")
    st.caption("Mis à jour automatiquement chaque matin à 08h00 via Make")

    hdrs = notion_headers()
    if not hdrs:
        st.error("Token Notion manquant — configurer dans Streamlit Cloud > Secrets")
        st.code('[notion]\ntoken = "secret_..."', language="toml")
        st.stop()

    @st.cache_data(ttl=300)
    def load_kpis():
        r = requests.post(
            "https://api.notion.com/v1/databases/" + NOTION_DB_DASHBOARD + "/query",
            headers=notion_headers(),
            json={"page_size": 20},
            timeout=15,
        )
        if r.status_code != 200:
            return None, r.text
        return r.json().get("results", []), None

    with st.spinner("Chargement KPIs Notion..."):
        pages, err = load_kpis()

    if err:
        st.error("Erreur Notion : " + err[:200])
    elif not pages:
        st.warning("Aucune donnée dans la DB Dashboard. Vérifier les IDs et les partages Notion.")
    else:
        # Afficher chaque KPI comme métrique
        cols = st.columns(len(pages))
        for col, p in zip(cols, pages):
            props = p.get("properties", {})
            # Lire les propriétés (noms tels que définis dans Notion)
            titre_prop  = props.get("Métrique", props.get("Metrique", props.get("Name", {})))
            valeur_prop = props.get("Valeur", {})

            titre  = ""
            if titre_prop.get("type") == "title":
                rts = titre_prop.get("title", [])
                titre = rts[0]["plain_text"] if rts else ""
            elif titre_prop.get("type") == "rich_text":
                rts = titre_prop.get("rich_text", [])
                titre = rts[0]["plain_text"] if rts else ""

            valeur = ""
            if valeur_prop.get("type") == "number":
                valeur = str(valeur_prop.get("number", "—"))
            elif valeur_prop.get("type") == "rich_text":
                rts = valeur_prop.get("rich_text", [])
                valeur = rts[0]["plain_text"] if rts else "—"

            with col:
                st.metric(titre or "KPI", valeur or "—")

    st.divider()
    if st.button("Rafraîchir les KPIs", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────
# PAGE 2 — CRM Pipeline
# ─────────────────────────────────────────────────────────────
elif page == "🏢 CRM Pipeline":
    st.title("🏢 CRM Pipeline Prospects")

    hdrs = notion_headers()
    if not hdrs:
        st.error("Token Notion manquant")
        st.stop()

    # Filtre statut
    STATUTS = ["Tous", "✉️ Email envoyé", "🎉 Converti", "⏸️ Sans suite"]
    filtre = st.selectbox("Filtrer par statut", STATUTS)

    @st.cache_data(ttl=60)
    def load_crm(filtre_statut):
        body = {"page_size": 100, "sorts": [{"property": "Date", "direction": "descending"}]}
        if filtre_statut != "Tous":
            body["filter"] = {
                "property": "Statut",
                "select": {"equals": filtre_statut},
            }
        r = requests.post(
            "https://api.notion.com/v1/databases/" + NOTION_DB_CRM + "/query",
            headers=notion_headers(),
            json=body,
            timeout=15,
        )
        if r.status_code != 200:
            return None, r.text
        return r.json().get("results", []), None

    with st.spinner("Chargement CRM..."):
        rows, err = load_crm(filtre)

    if err:
        st.error("Erreur : " + err[:200])
    elif not rows:
        st.info("Aucun prospect trouvé pour ce filtre.")
    else:
        st.caption(str(len(rows)) + " prospects")
        data = []
        for p in rows:
            props = p.get("properties", {})

            def txt(key):
                prop = props.get(key, {})
                ptype = prop.get("type", "")
                if ptype in ("title", "rich_text"):
                    items = prop.get(ptype, [])
                    return items[0]["plain_text"] if items else ""
                if ptype == "select":
                    sel = prop.get("select")
                    return sel["name"] if sel else ""
                if ptype == "email":
                    return prop.get("email", "") or ""
                if ptype == "date":
                    d = prop.get("date")
                    return d["start"][:10] if d else ""
                return ""

            data.append({
                "Cabinet":  txt("Cabinet") or txt("Name"),
                "Contact":  txt("Contact"),
                "Email":    txt("Email"),
                "Statut":   txt("Statut"),
                "Date":     txt("Date"),
                "Ville":    txt("Ville"),
                "Taille":   txt("Taille"),
            })
        st.dataframe(data, use_container_width=True, hide_index=True)

    if st.button("Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────
# PAGE 3 — RAPPORT IA (AI Act + RGPD)
# ─────────────────────────────────────────────────────────────
elif page == "🔬 Rapport IA":
    st.title("🔬 Generateur de rapport RGPD + AI Act")
    st.caption("Saisir les reponses Tally → Claude analyse → rapport structure pret a envoyer au client")

    TALLY_URL = "https://tally.so/r/rjpjW2"
    st.info("Lien questionnaire client : " + TALLY_URL)

    QUESTIONS = {
        "Bloc A — Registre des traitements": [
            ("A1", "Avez-vous un registre des traitements de donnees ?", "CRITIQUE"),
            ("A2", "Avez-vous nomme un DPO ou referent RGPD ?", "IMPORTANTE"),
            ("A3", "Vos employes sont-ils formes au RGPD ?", "IMPORTANTE"),
        ],
        "Bloc B — Site web / Cookies": [
            ("B1", "Avez-vous une politique de confidentialite sur votre site ?", "CRITIQUE"),
            ("B2", "Avez-vous un bandeau cookies conforme ?", "CRITIQUE"),
            ("B3", "Vos formulaires web ont-ils une case de consentement ?", "CRITIQUE"),
            ("B4", "Votre site est-il securise en HTTPS ?", "IMPORTANTE"),
        ],
        "Bloc C — Securite": [
            ("C1", "Vos donnees sont-elles sauvegardees regulierement ?", "CRITIQUE"),
            ("C2", "Utilisez-vous des mots de passe forts et uniques ?", "IMPORTANTE"),
            ("C3", "Avez-vous un antivirus/firewall actif ?", "IMPORTANTE"),
            ("C4", "Avez-vous un plan en cas de violation de donnees ?", "CRITIQUE"),
        ],
        "Bloc D — Sous-traitants": [
            ("D1", "Avez-vous signe des DPA avec vos prestataires ?", "CRITIQUE"),
            ("D2", "Vos prestataires sont-ils tous dans l'UE ou pays adequats ?", "CRITIQUE"),
            ("D3", "Avez-vous une liste de vos sous-traitants ?", "IMPORTANTE"),
        ],
        "Bloc E — Droits des personnes": [
            ("E1", "Pouvez-vous repondre a une demande d'acces aux donnees en 30 jours ?", "CRITIQUE"),
            ("E2", "Pouvez-vous supprimer les donnees d'une personne sur demande ?", "CRITIQUE"),
        ],
        "Bloc F — Email marketing": [
            ("F1", "Avez-vous le consentement explicite pour vos emails marketing ?", "CRITIQUE"),
            ("F2", "Proposez-vous un lien de desinscription dans chaque email ?", "CRITIQUE"),
        ],
        "Bloc G — EU AI Act (Art. 50 + obligations generales)": [
            ("G1", "Utilisez-vous des outils d'IA dans votre activite ?",                         "INFORMATIF"),
            ("G2", "Ces outils d'IA prennent-ils des decisions automatiques sur des personnes ?", "CRITIQUE"),
            ("G3", "Informez-vous vos clients quand ils interagissent avec une IA ?",             "IMPORTANTE"),
            ("G4", "Avez-vous evalue les risques de vos outils d'IA ?",                          "CRITIQUE"),
            ("G5", "Vos systemes d'IA generative affichent-ils clairement leur nature IA ?",      "CRITIQUE"),
            ("G6", "Avez-vous une politique interne d'usage acceptable de l'IA ?",               "IMPORTANTE"),
        ],
    }

    NB_QUESTIONS = sum(len(v) for v in QUESTIONS.values())

    # 1. Infos client
    st.subheader("1  Informations client")
    c1, c2 = st.columns(2)
    with c1:
        client_nom     = st.text_input("Nom de l'entreprise *", placeholder="Cabinet Dupont")
        client_contact = st.text_input("Nom du dirigeant",      placeholder="Jean Dupont")
    with c2:
        client_email   = st.text_input("Email client *",        placeholder="jean@dupont.fr")
        client_secteur = st.text_input("Secteur",               placeholder="Expertise comptable")
    client_salaries = st.text_input("Nombre de salaries",       placeholder="12")

    # 2. Reponses
    st.subheader("2  Reponses du questionnaire")
    st.caption("Saisir les reponses recues dans Tally > Submissions")

    reponses = {}
    for bloc_titre, questions in QUESTIONS.items():
        with st.expander(bloc_titre, expanded=True):
            cols_q = st.columns(2)
            for idx, (code, question, niveau) in enumerate(questions):
                badge = "CRITIQUE" if niveau == "CRITIQUE" else ("IMPORT." if niveau == "IMPORTANTE" else "INFO")
                with cols_q[idx % 2]:
                    rep = st.radio(
                        "[" + badge + "] " + code + " — " + question,
                        ["OUI", "NON"],
                        index=None,
                        key="rep_" + code,
                        horizontal=True,
                    )
                    reponses[code] = rep

    # Score temps reel
    nb_rep   = sum(1 for v in reponses.values() if v is not None)
    score    = sum(1 for v in reponses.values() if v == "OUI")
    crit_non = [
        c for bl, qs in QUESTIONS.items()
        for (c, _, niv) in qs if niv == "CRITIQUE" and reponses.get(c) == "NON"
    ]

    if nb_rep > 0:
        st.divider()
        st.subheader("Score en temps reel")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Score", str(score) + " / " + str(NB_QUESTIONS))
        with m2:
            st.metric("Repondus", str(nb_rep) + " / " + str(NB_QUESTIONS))
        with m3:
            pct = score / NB_QUESTIONS
            if pct >= 0.90:   niv_lbl = "EXCELLENT"
            elif pct >= 0.65: niv_lbl = "MOYEN"
            elif pct >= 0.40: niv_lbl = "INSUFFISANT"
            else:              niv_lbl = "NON CONFORME"
            st.metric("Niveau", niv_lbl)
        with m4:
            if pct >= 0.90:   up_prix = "150 EUR/mois"
            elif pct >= 0.65: up_prix = "1 500 EUR"
            elif pct >= 0.40: up_prix = "2 500 EUR"
            else:              up_prix = "4 000 EUR"
            st.metric("Upsell estime", up_prix)
        st.progress(score / NB_QUESTIONS,
                    text=str(score) + "/" + str(NB_QUESTIONS) + " (" + str(round(score / NB_QUESTIONS * 100)) + "%)")
        if crit_non:
            st.error("Points CRITIQUE non conformes : " + ", ".join(crit_non))

    # 3. Generation IA
    st.divider()
    st.subheader("3  Analyse IA — Claude Sonnet")

    anthropic_key = get_anthropic_key()
    if not anthropic_key:
        st.warning("Cle API Anthropic manquante.\n\n```toml\n[anthropic]\napi_key = \"sk-ant-...\"\n```")

    seuil_rep = NB_QUESTIONS - 4  # Tolere 4 non-repondus
    can_gen = bool(client_nom and anthropic_key and nb_rep >= seuil_rep)

    if st.button("Generer l'analyse IA", type="primary", disabled=not can_gen, use_container_width=True):
        # Construire le texte des reponses
        lignes = []
        for bt, qs in QUESTIONS.items():
            lignes.append("\n--- " + bt + " ---")
            for code, question, niveau in qs:
                rv = reponses.get(code) or "Non repondu"
                lignes.append("[" + code + "] (" + niveau + ") " + question + " : " + rv)
        rep_txt = "\n".join(lignes)

        pct_score = score / NB_QUESTIONS
        if pct_score >= 0.90:   niv_str = "EXCELLENT"
        elif pct_score >= 0.65: niv_str = "MOYEN"
        elif pct_score >= 0.40: niv_str = "INSUFFISANT"
        else:                   niv_str = "NON CONFORME"

        sys_prompt = (
            "Tu es un expert en conformite RGPD et EU AI Act. "
            "Tu analyses des questionnaires d'audit pour SMD Global Consulting LLC. "
            "Tu reponds UNIQUEMENT en JSON valide, sans texte avant ni apres."
        )

        user_prompt = (
            "Analyse ce micro-audit RGPD + AI Act.\n\n"
            "CLIENT :\n"
            "- Entreprise : " + client_nom + "\n"
            "- Dirigeant : " + (client_contact or "Non renseigne") + "\n"
            "- Secteur : " + (client_secteur or "Non renseigne") + "\n"
            "- Salaries : " + (client_salaries or "Non renseigne") + "\n\n"
            "SCORE : " + str(score) + "/" + str(NB_QUESTIONS) + " — Niveau : " + niv_str + "\n\n"
            "REPONSES :\n" + rep_txt + "\n\n"
            "Genere ce JSON :\n"
            "{\n"
            '  "synthese_executive": "Paragraphe 100 mots : niveau conformite, risques, action prioritaire.",\n'
            '  "risque_amende": "Risque amende CNIL/AI Act : montants reels, articles. 2-3 phrases.",\n'
            '  "analyse_blocs": {\n'
            '    "A": {"score": 0, "max": 3, "titre": "Registre des traitements", "analyse": "2-3 phrases."},\n'
            '    "B": {"score": 0, "max": 4, "titre": "Site web / Cookies", "analyse": "2-3 phrases."},\n'
            '    "C": {"score": 0, "max": 4, "titre": "Securite", "analyse": "2-3 phrases."},\n'
            '    "D": {"score": 0, "max": 3, "titre": "Sous-traitants", "analyse": "2-3 phrases."},\n'
            '    "E": {"score": 0, "max": 2, "titre": "Droits des personnes", "analyse": "2-3 phrases."},\n'
            '    "F": {"score": 0, "max": 2, "titre": "Email marketing", "analyse": "2-3 phrases."},\n'
            '    "G": {"score": 0, "max": 6, "titre": "EU AI Act", "analyse": "2-3 phrases.  Citer Art. 50 et obligations applicables."}\n'
            "  },\n"
            '  "recommandations": [\n'
            '    {"priorite": "CRITIQUE", "code_question": "A1", "action": "Action concrete.", "pourquoi": "Risque legal.", "delai": "0-30 jours", "article": "Art. 30 RGPD"}\n'
            "  ],\n"
            '  "plan_action": [\n'
            '    {"ordre": 1, "action": "Action", "responsable": "Qui", "delai": "0-30j", "ressource": "Outil", "kpi": "Mesure"}\n'
            "  ],\n"
            '  "opportunite_commerciale": "Proposition mission SMD adaptee au score (service, tarif, duree)."\n'
            "}\n\n"
            "Regles : scores calcules d'apres les OUI, min 5 recommandations CRITIQUE en premier, "
            "plan couvrant 0-30j / 30-90j / 90-180j, articles de loi reels (RGPD + EU AI Act 2024/1689)."
        )

        with st.spinner("Claude Sonnet analyse... (30-60 secondes)"):
            try:
                r = requests.post(
                    ANTHROPIC_API_URL,
                    headers={
                        "x-api-key": anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": ANTHROPIC_MODEL,
                        "max_tokens": 4096,
                        "system": sys_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                    timeout=90,
                )
                if r.status_code != 200:
                    st.error("Erreur API HTTP " + str(r.status_code) + " : " + r.text[:300])
                else:
                    raw = r.json()["content"][0]["text"].strip()
                    if raw.startswith("```"):
                        parts = raw.split("```")
                        raw = parts[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                    st.session_state["ia_result"]   = json.loads(raw)
                    st.session_state["ia_nom"]      = client_nom
                    st.session_state["ia_score"]    = score
                    st.session_state["ia_niveau"]   = niv_str
                    st.session_state["ia_nb_q"]     = NB_QUESTIONS
                    st.session_state["ia_contact"]  = client_contact
                    st.session_state["ia_email"]    = client_email
                    st.session_state["ia_secteur"]  = client_secteur
                    st.session_state["ia_salaries"] = client_salaries
                    st.success("Analyse generee avec succes !")
                    st.rerun()
            except json.JSONDecodeError as e:
                st.error("JSON invalide : " + str(e))
                st.code(raw[:500])
            except Exception as e:
                st.error("Erreur : " + str(e))

    if not can_gen:
        missing = []
        if not client_nom:          missing.append("nom de l'entreprise")
        if not anthropic_key:       missing.append("cle API Anthropic")
        if nb_rep < seuil_rep:      missing.append(str(seuil_rep - nb_rep) + " reponses manquantes")
        if missing:
            st.caption("Manquant : " + " | ".join(missing))

    # Affichage resultats
    if "ia_result" in st.session_state:
        res  = st.session_state["ia_result"]
        nom  = st.session_state.get("ia_nom", client_nom)
        sc   = st.session_state.get("ia_score", score)
        nv   = st.session_state.get("ia_niveau", "")
        nb_q = st.session_state.get("ia_nb_q", NB_QUESTIONS)

        st.divider()
        st.subheader("Analyse — " + nom + " — " + str(sc) + "/" + str(nb_q) + " — " + nv)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Synthese", "Par bloc", "Recommandations", "Plan d'action", "Commercial"]
        )

        with tab1:
            st.markdown("**Synthese executive**")
            st.text_area("Copier dans le rapport Word", value=res.get("synthese_executive", ""),
                         height=180, key="edit_synthese")
            st.markdown("**Risque amende estime**")
            st.text_area(" ", value=res.get("risque_amende", ""), height=110, key="edit_amende")

        with tab2:
            for lettre, data in res.get("analyse_blocs", {}).items():
                sb  = data.get("score", 0)
                mb  = data.get("max", 1)
                tb  = data.get("titre", "Bloc " + lettre)
                pct_b = sb / mb if mb else 0
                col_b = "green" if pct_b == 1.0 else ("orange" if pct_b >= 0.5 else "red")
                st.markdown("**Bloc " + lettre + " — " + tb + "** : :" + col_b + "[" + str(sb) + "/" + str(mb) + "]")
                st.text_area("analyse_" + lettre, value=data.get("analyse", ""),
                             height=90, key="edit_b_" + lettre, label_visibility="collapsed")

        with tab3:
            for i, reco in enumerate(res.get("recommandations", []), 1):
                prio  = reco.get("priorite", "")
                col_r = "red" if prio == "CRITIQUE" else ("orange" if prio == "IMPORTANTE" else "blue")
                st.markdown(
                    str(i) + ". :" + col_r + "[" + prio + "]"
                    + " `" + reco.get("code_question", "") + "` — " + reco.get("action", "")
                )
                ca, cb = st.columns(2)
                with ca:
                    st.caption("Pourquoi : " + reco.get("pourquoi", ""))
                with cb:
                    st.caption("Delai : " + reco.get("delai", "") + "  |  " + reco.get("article", ""))
                st.markdown("---")

        with tab4:
            plan = res.get("plan_action", [])
            if plan:
                st.dataframe(
                    [
                        {
                            "#":            p.get("ordre", ""),
                            "Action":       p.get("action", ""),
                            "Responsable":  p.get("responsable", ""),
                            "Delai":        p.get("delai", ""),
                            "Ressource":    p.get("ressource", ""),
                            "KPI":          p.get("kpi", ""),
                        }
                        for p in plan
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

        with tab5:
            st.success("Proposition commerciale generee par l'IA")
            st.text_area(
                "A inclure dans l'email de livraison",
                value=res.get("opportunite_commerciale", ""),
                height=180,
                key="edit_comm",
            )
            pct_r = sc / nb_q
            if pct_r >= 0.90:
                st.info("Proposer : Veille reglementaire — 150 EUR/mois")
            elif pct_r >= 0.65:
                st.warning("Proposer : Mission conformite complete — 1 500 EUR")
            elif pct_r >= 0.40:
                st.error("Proposer : Mission urgente 6 mois — 2 500 EUR")
            else:
                st.error("Proposer : Mission complete + DPO externalise — 4 000 EUR")

        # ── Telechargement rapport Word ───────────────────────
        st.divider()
        col_dl, col_reset = st.columns([2, 1])
        with col_dl:
            if DOCX_AVAILABLE:
                client_info = {
                    "nom":       nom,
                    "contact":   st.session_state.get("ia_contact", ""),
                    "email":     st.session_state.get("ia_email", ""),
                    "secteur":   st.session_state.get("ia_secteur", ""),
                    "salaries":  st.session_state.get("ia_salaries", ""),
                }
                try:
                    docx_buf  = generer_rapport(client_info, sc, nb_q, nv, res)
                    nom_fichier = "Rapport-Audit-" + nom.replace(" ", "-") + "-" + date.today().strftime("%Y%m%d") + ".docx"
                    st.download_button(
                        label="Telecharger le rapport Word (.docx)",
                        data=docx_buf,
                        file_name=nom_fichier,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error("Erreur generation Word : " + str(e))
            else:
                st.warning("python-docx non installe — ajouter dans requirements.txt")
        with col_reset:
            if st.button("Effacer et recommencer", type="secondary", use_container_width=True):
                for k in ["ia_result", "ia_nom", "ia_score", "ia_niveau", "ia_nb_q",
                          "ia_contact", "ia_email", "ia_secteur", "ia_salaries"]:
                    st.session_state.pop(k, None)
                st.rerun()

# ─────────────────────────────────────────────────────────────
# PAGE 4 — ROUTEUR SMD
# ─────────────────────────────────────────────────────────────
elif page == "🔀 Routeur SMD":
    st.title("🔀 Routeur SMD — Instructions en langage naturel")
    st.caption("Envoi au webhook Make → Haiku classe → Agent execute")

    with st.expander("Exemples d'instructions", expanded=False):
        st.markdown("""
- **Commercial** : `Envoyer un email de prospection a Cabinet Lefebvre, DG Jean Martin, jean@lefebvre.fr, Bordeaux, 15 salaries`
- **Admin Convertir** : `Convertir le prospect Cabinet Lefebvre`
- **Admin Archiver** : `Archiver le prospect Cabinet Legrand sans suite`
- **Marketing** : `Generer un post LinkedIn sur les risques CNIL pour les cabinets comptables`
        """)

    instruction = st.text_area(
        "Instruction",
        placeholder="Envoyer un email de prospection a...",
        height=120,
    )

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        envoyer = st.button("Envoyer", type="primary", disabled=not bool(instruction.strip()))

    if envoyer and instruction.strip():
        with st.spinner("Envoi au Routeur Make..."):
            try:
                r = requests.post(
                    MAKE_WEBHOOK_ROUTEUR,
                    json={"instruction": instruction.strip()},
                    timeout=30,
                )
                if r.status_code in (200, 202):
                    st.success("Instruction envoyee ! Make traite la demande.")
                    st.code(r.text[:200] if r.text else "(reponse vide)", language="text")
                else:
                    st.error("Erreur HTTP " + str(r.status_code) + " : " + r.text[:200])
            except Exception as e:
                st.error("Erreur reseau : " + str(e))

    st.divider()
    st.markdown("**Flux de traitement :**")
    st.markdown("""
```
Instruction
  → Webhook Make Routeur (6258440)
    → Claude Haiku — classifie l'action et extrait les entites
      → smd-dispatcher (Supabase Edge Function v8)
        → Agent Commercial   → Notion CRM + Gmail
        → Agent Marketing    → Notion Marketing DB
        → Agent Admin        → Notion CRM (Statut)
```
    """)

# ─────────────────────────────────────────────────────────────
# PAGE 5 — MARKETING
# ─────────────────────────────────────────────────────────────
elif page == "📢 Marketing":
    st.title("📢 Contenus Marketing LinkedIn")

    hdrs = notion_headers()
    if not hdrs:
        st.error("Token Notion manquant")
        st.stop()

    @st.cache_data(ttl=120)
    def load_marketing():
        r = requests.post(
            "https://api.notion.com/v1/databases/" + NOTION_DB_MARKETING + "/query",
            headers=notion_headers(),
            json={
                "page_size": 20,
                "sorts": [{"timestamp": "created_time", "direction": "descending"}],
            },
            timeout=15,
        )
        if r.status_code != 200:
            return None, r.text
        return r.json().get("results", []), None

    with st.spinner("Chargement contenus marketing..."):
        posts, err = load_marketing()

    if err:
        st.error("Erreur : " + err[:200])
    elif not posts:
        st.info("Aucun contenu marketing trouve.")
    else:
        for p in posts:
            props = p.get("properties", {})

            def rtxt(key):
                prop = props.get(key, {})
                ptype = prop.get("type", "")
                if ptype in ("title", "rich_text"):
                    items = prop.get(ptype, [])
                    return items[0]["plain_text"] if items else ""
                return ""

            sujet   = rtxt("Sujet") or rtxt("Name") or "Sans titre"
            contenu = rtxt("Contenu") or rtxt("Post")
            date_c  = p.get("created_time", "")[:10]

            with st.expander(sujet + "  —  " + date_c):
                if contenu:
                    st.text_area("Contenu", value=contenu, height=200,
                                 key="mkt_" + p["id"], label_visibility="collapsed")
                else:
                    st.caption("(Contenu vide — verifier la propriete 'Contenu' dans Notion)")

    if st.button("Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────
# PAGE 6 — SYSTEME
# ─────────────────────────────────────────────────────────────
elif page == "⚙️ Systeme":
    st.title("⚙️ Etat du systeme")

    make_key = get_make_key()

    # Etat des secrets
    st.subheader("Secrets Streamlit")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Notion token",   "OK" if get_notion_token()   else "MANQUANT")
    with c2:
        st.metric("Make API key",   "OK" if make_key             else "MANQUANT")
    with c3:
        st.metric("Anthropic key",  "OK" if get_anthropic_key()  else "MANQUANT")

    st.divider()

    # Etat scenaris Make
    st.subheader("Scenaris Make")
    if not make_key:
        st.warning("Make API key manquante — impossible de verifier l'etat des scenaris.")
        st.code('[make]\napi_key = "VOTRE_MAKE_API_KEY"', language="toml")
    else:
        MAKE_TEAM_ID = "1889560"

        @st.cache_data(ttl=60)
        def load_scenarios():
            results = []
            for sc in MAKE_SCENARIOS:
                try:
                    r = requests.get(
                        "https://eu1.make.com/api/v2/scenarios/" + sc["id"],
                        headers={"Authorization": "Token " + make_key},
                        params={"teamId": MAKE_TEAM_ID},
                        timeout=10,
                    )
                    if r.status_code == 200:
                        data = r.json().get("scenario", {})
                        results.append({
                            "Scenario":   sc["emoji"] + " " + sc["nom"],
                            "Statut":     "ACTIF" if data.get("isEnabled") else "INACTIF",
                            "Derniere exec": data.get("lastExecution", {}).get("started", "—")[:19].replace("T", " ") if data.get("lastExecution") else "—",
                            "ID":         sc["id"],
                        })
                    else:
                        results.append({
                                     "Scenario":   sc["emoji"] + " " + sc["nom"],
                            "Statut":     "ERREUR HTTP " + str(r.status_code),
                            "Derniere exec": "—",
                            "ID":         sc["id"],
                        })
                except Exception as e:
                    results.append({
                        "Scenario":   sc["emoji"] + " " + sc["nom"],
                        "Statut":     "ERREUR: " + str(e)[:50],
                        "Derniere exec": "—",
                        "ID":         sc["id"],
                    })
            return results

        with st.spinner("Interrogation Make API..."):
            scenario_data = load_scenarios()

        st.dataframe(scenario_data, use_container_width=True, hide_index=True)

        if st.button("Rafraichir scenaris", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # Architecture
    st.subheader("Architecture")
    st.markdown("""
| Composant | Detail |
|---|---|
| **Supabase** | `ckfzczuvjbxgrwgpqrdz` — Edge Function `smd-dispatcher` (v8) |
| **Make Team** | `1889560` — Region EU1 |
| **Notion CRM** | `40fb8514-337d-4550-b899-743383a02169` |
| **Notion Dashboard** | `ad90d1fd-7f41-400b-97bc-3098faa335a5` |
| **Notion Marketing** | `7abdb6fc-eae3-43de-afd5-71252ab60f0e` |
| **Webhook Routeur** | `hook.eu1.make.com/5hbyls7ztgpvc76avtx06h3gfpbi4u2o` |
    """)

    st.divider()
    st.subheader("Test webhook Routeur")
    test_payload = st.text_input("Payload test", value='{"instruction": "Test ping depuis Dashboard"}')
    if st.button("Envoyer test"):
        try:
            payload = json.loads(test_payload)
            r = requests.post(MAKE_WEBHOOK_ROUTEUR, json=payload, timeout=15)
            st.code("HTTP " + str(r.status_code) + "\n" + r.text[:300], language="text")
        except json.JSONDecodeError:
            st.error("JSON invalide")
        except Exception as e:
            st.error(str(e))
