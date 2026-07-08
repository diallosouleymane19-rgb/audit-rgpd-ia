"""
Page Rapport IA — a inclure dans app.py a la place du bloc PAGE 5
Ajouter ce code dans app.py juste avant la PAGE SYSTEME
"""

# ─────────────────────────────────────────────
# PAGE 5 — RAPPORT IA
# ─────────────────────────────────────────────
elif page == "🔬 Rapport IA":
    import json as _json

    st.title("🔬 Generateur de rapport IA")
    st.caption("Saisir les reponses Tally -> Claude analyse -> rapport structure pret a envoyer au client")

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
        "Bloc G — EU AI Act": [
            ("G1", "Utilisez-vous des outils d'IA dans votre activite ?", "INFORMATIF"),
            ("G2", "Ces outils d'IA prennent-ils des decisions automatiques sur des personnes ?", "CRITIQUE"),
            ("G3", "Informez-vous vos clients quand ils interagissent avec une IA ?", "IMPORTANTE"),
            ("G4", "Avez-vous evalue les risques de vos outils d'IA ?", "CRITIQUE"),
        ],
    }

    # ── 1. Informations client ────────────────────────────────
    st.subheader("1  Informations client")
    c1, c2 = st.columns(2)
    with c1:
        client_nom     = st.text_input("Nom de l'entreprise *", placeholder="Cabinet Dupont")
        client_contact = st.text_input("Nom du dirigeant", placeholder="Jean Dupont")
    with c2:
        client_email   = st.text_input("Email client *", placeholder="jean@dupont.fr")
        client_secteur = st.text_input("Secteur", placeholder="Expertise comptable")
    client_salaries = st.text_input("Nombre de salaries", placeholder="12")

    # ── 2. Reponses Tally ─────────────────────────────────────
    st.subheader("2  Reponses du questionnaire Tally")
    st.caption("Saisir les reponses recues dans Tally > Submissions")

    reponses = {}
    for bloc_titre, questions in QUESTIONS.items():
        with st.expander(bloc_titre, expanded=True):
            cols_q = st.columns(2)
            for idx, (code, question, niveau) in enumerate(questions):
                badge = "CRITIQUE" if niveau == "CRITIQUE" else ("IMPORT." if niveau == "IMPORTANTE" else "INFO")
                with cols_q[idx % 2]:
                    rep = st.radio(
                        f"[{badge}] {code} — {question}",
                        ["OUI", "NON"],
                        index=None,
                        key="rep_" + code,
                        horizontal=True,
                    )
                    reponses[code] = rep

    # ── Score en temps reel ───────────────────────────────────
    nb_rep   = sum(1 for v in reponses.values() if v is not None)
    score    = sum(1 for v in reponses.values() if v == "OUI")
    crit_non = [c for bl, qs in QUESTIONS.items()
                for (c, _, niv) in qs if niv == "CRITIQUE" and reponses.get(c) == "NON"]

    if nb_rep > 0:
        st.divider()
        st.subheader("Score en temps reel")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Score", str(score) + " / 22")
        with m2:
            st.metric("Repondus", str(nb_rep) + " / 22")
        with m3:
            if score >= 20:   niv_lbl = "EXCELLENT"
            elif score >= 14: niv_lbl = "MOYEN"
            elif score >= 8:  niv_lbl = "INSUFFISANT"
            else:             niv_lbl = "NON CONFORME"
            st.metric("Niveau", niv_lbl)
        with m4:
            if score >= 20:   up_prix = "150 EUR/mois"
            elif score >= 14: up_prix = "1 500 EUR"
            elif score >= 8:  up_prix = "2 500 EUR"
            else:             up_prix = "4 000 EUR"
            st.metric("Upsell", up_prix)
        if nb_rep == 22:
            st.progress(score / 22, text=str(score) + "/22 (" + str(round(score / 22 * 100)) + "%)")
        if crit_non:
            st.error("Points CRITIQUE non conformes : " + ", ".join(crit_non))

    # ── 3. Generation IA ─────────────────────────────────────
    st.divider()
    st.subheader("3  Analyse IA — Claude Sonnet")

    anthropic_key = get_anthropic_key()
    if not anthropic_key:
        st.warning("Cle API Anthropic manquante. Ajouter dans Streamlit Cloud > Secrets :\n[anthropic]\napi_key = \"sk-ant-...\"")

    can_gen = bool(client_nom and anthropic_key and nb_rep >= 20)

    if st.button("Generer l'analyse IA", type="primary", disabled=not can_gen, use_container_width=True):
        lignes = []
        for bt, qs in QUESTIONS.items():
            lignes.append("\n--- " + bt + " ---")
            for code, question, niveau in qs:
                rv = reponses.get(code) or "Non repondu"
                lignes.append("[" + code + "] (" + niveau + ") " + question + " : " + rv)
        rep_txt = "\n".join(lignes)

        if score >= 20:   niv_str = "EXCELLENT"
        elif score >= 14: niv_str = "MOYEN"
        elif score >= 8:  niv_str = "INSUFFISANT"
        else:             niv_str = "NON CONFORME"

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
            "SCORE : " + str(score) + "/22 — Niveau : " + niv_str + "\n\n"
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
            '    "G": {"score": 0, "max": 4, "titre": "EU AI Act", "analyse": "2-3 phrases."}\n'
            "  },\n"
            '  "recommandations": [\n'
            '    {"priorite": "CRITIQUE", "code_question": "A1", "action": "Action concrete.", "pourquoi": "Risque legal.", "delai": "0-30 jours", "article": "Art. 30 RGPD"}\n'
            "  ],\n"
            '  "plan_action": [\n'
            '    {"ordre": 1, "action": "Action", "responsable": "Qui", "delai": "0-30j", "ressource": "Outil", "kpi": "Mesure"}\n'
            "  ],\n"
            '  "opportunite_commerciale": "Proposition mission SMD adaptee au score."\n'
            "}\n\n"
            "Regles : scores calcules d'apres les OUI, min 5 recommandations CRITIQUE en premier, "
            "plan couvrant 0-30j/30-90j/90-180j, articles de loi reels."
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
                    st.session_state["ia_result"]  = _json.loads(raw)
                    st.session_state["ia_nom"]     = client_nom
                    st.session_state["ia_score"]   = score
                    st.session_state["ia_niveau"]  = niv_str
                    st.success("Analyse generee avec succes !")
                    st.rerun()
            except _json.JSONDecodeError as e:
                st.error("JSON invalide : " + str(e))
                st.code(raw[:500])
            except Exception as e:
                st.error("Erreur : " + str(e))

    if not can_gen:
        missing = []
        if not client_nom:     missing.append("nom de l'entreprise")
        if not anthropic_key:  missing.append("cle API Anthropic")
        if nb_rep < 20:        missing.append(str(20 - nb_rep) + " reponses manquantes")
        if missing:
            st.caption("Manquant : " + " | ".join(missing))

    # ── Affichage resultats ───────────────────────────────────
    if "ia_result" in st.session_state:
        res = st.session_state["ia_result"]
        nom = st.session_state.get("ia_nom", client_nom)
        sc  = st.session_state.get("ia_score", score)
        nv  = st.session_state.get("ia_niveau", "")

        st.divider()
        st.subheader("Analyse — " + nom + " — " + str(sc) + "/22 — " + nv)

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
                pct = sb / mb if mb else 0
                col = "green" if pct == 1.0 else ("orange" if pct >= 0.5 else "red")
                st.markdown("**Bloc " + lettre + " — " + tb + "** : :" + col + "[" + str(sb) + "/" + str(mb) + "]")
                st.text_area("analyse_" + lettre, value=data.get("analyse", ""),
                             height=90, key="edit_b_" + lettre, label_visibility="collapsed")

        with tab3:
            for i, reco in enumerate(res.get("recommandations", []), 1):
                prio  = reco.get("priorite", "")
                col   = "red" if prio == "CRITIQUE" else ("orange" if prio == "IMPORTANTE" else "blue")
                st.markdown(str(i) + ". :" + col + "[" + prio + "]" + " `" + reco.get("code_question", "") + "` — " + reco.get("action", ""))
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
                    [{"#": p.get("ordre", ""), "Action": p.get("action", ""),
                      "Responsable": p.get("responsable", ""), "Delai": p.get("delai", ""),
                      "Ressource": p.get("ressource", ""), "KPI": p.get("kpi", "")}
                     for p in plan],
                    use_container_width=True, hide_index=True,
                )

        with tab5:
            st.success("Proposition commerciale generee par l'IA")
            st.text_area("A inclure dans l'email de livraison",
                         value=res.get("opportunite_commerciale", ""), height=180, key="edit_comm")
            if sc >= 20:
                st.info("Proposer : Veille reglementaire — 150 EUR/mois")
            elif sc >= 14:
                st.warning("Proposer : Mission conformite complete — 1 500 EUR")
            elif sc >= 8:
                st.error("Proposer : Mission urgente 6 mois — 2 500 EUR")
            else:
                st.error("Proposer : Mission complete + DPO externalise — 4 000 EUR")

        st.divider()
        if st.button("Effacer et recommencer", type="secondary"):
            for k in ["ia_result", "ia_nom", "ia_score", "ia_niveau"]:
                st.session_state.pop(k, None)
            st.rerun()
