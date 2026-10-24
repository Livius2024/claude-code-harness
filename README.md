# Configurarea Claude Code ca harness de coding (actualizat 24.10.2026, seara)

Claude Code 2.1.308, Opus 5.5, Windows 11. Backup-ul configurației vechi: `C:\Users\LIVIUS\.claude\backups\harness-2026-10-24\`.

## Principiul

Totul e **global**, pentru toate proiectele. Fiecare piesă pornește singură, în felul potrivit ei:

| Piesă | Cum pornește | Cost |
|---|---|---|
| Hook-uri | Mereu, deterministic, la evenimentele lor | ~0 tokeni (rulează în afara modelului) |
| Skill-uri | Claude le alege singur după tabelul din `CLAUDE.md`; hook-ul de prompt adaugă un indiciu | Doar numele și descrierea; conținutul se încarcă la nevoie |
| MCP (Playwright, Context7 etc.) | Unelte amânate, încărcate automat când e nevoie de ele | ~0 până la folosire |

Încărcarea tuturor skill-urilor de la început ar umple contextul și ar face agentul mai slab, nu mai bun.

## Skill-uri

- **Matt Pocock 1.3.1** e setul principal pentru inginerie.
  - Skill-urile „model-invoked” (grilling, tdd, diagnosing-bugs, code-review, domain-modeling, codebase-design, prototype, research, pr, wizard) pornesc automat.
  - Cele „user-invoked” (grill-with-docs, to-spec, to-tickets, implement, implement-spec, wayfinder, triage, handoff, retro) sunt citite și urmate de Claude singur, după o singură confirmare din partea ta pe fiecare funcționalitate.
- **Superpowers (19 skill-uri + frontend-design)** sunt blocate prin reguli `deny` în `settings.json`. Vin din contul tău claude.ai, unde fiecare e un plugin separat, „by you”; le ștergi tu acolo. Copiile pentru Codex din `C:\Users\LIVIUS\.agents\skills` (14) sunt mutate în `backups\harness-2026-10-24\agents-skills-superpowers`.
- **find-skills** (Vercel Labs): când lipsește o capacitate, Claude caută un skill gata făcut pe skills.sh, îl verifică și abia apoi îl instalează.
- **youtube-fetcher**: transcriere YouTube/TikTok/Instagram/X/Vimeo sau din fișiere locale (cu Whisper), plus o planșă de cadre pe care Claude o citește ca imagine. Folosește un mediu Python separat, în `C:\Users\LIVIUS\.claude\tools\youtube-fetcher-venv`, și `ffmpeg` instalat prin winget.
- **Skill-urile tale de domeniu**: moldovan-fiscal, cash-flow-audit, audit-documents (în `C:\Users\LIVIUS\.claude\skills`). Le-am rescris pornind de la notițele vechi pentru Codex: am scos trimiterile la scripturi care nu existau și numele de clienți. Acum trimit la șabloanele și metodologia reale din proiectul `1C python`. Regula de bază: nicio cotă, niciun articol și niciun cont din memorie, doar cu sursa citată. Copiile vechi pentru Codex au rămas neatinse în `C:\Users\LIVIUS\.agents\skills`.
- Celelalte skill-uri: UI (impeccable, emil-design-eng, break-ui, mobile-native), skill-urile Leon van Zyl (start-an-app, review-an-app, deploy-an-app, create-brand-kit), fixing-metadata, antislop, officecli, Codex review.

## Hook-uri (în `C:\Users\LIVIUS\.claude\hooks\`)

Recomandările lui Leon van Zyl (seria „harness engineering”) și ale comunității, adaptate:

| Eveniment | Hook | Ce face |
|---|---|---|
| SessionStart | `harness/session-context.mjs` | Spune agentului starea git, documentele proiectului (AGENTS.md, GLOSSARY.md, ADR) și dacă există HANDOFF.md. După compactare repetă regulile de bază. |
| UserPromptSubmit | `harness/prompt-guard.mjs` | Blochează mesajele care conțin chei secrete. Altfel adaugă un „Skill hint” (RO + EN) pentru skill-ul Matt potrivit. |
| PreToolUse | `harness/git-guardrail.mjs` | Blochează force-push, `reset --hard`, `clean -f`, push pe `main` (și push simplu din `main`), ștergeri de branch/stash forțate, `--no-verify`, în orice scriere (`git -C`, `git.exe`, ghilimele, `bash -c "…"`, `node -e`, `$(…)`, blocuri PowerShell, rânduri continuate, redirecționări), plus comenzile pe care git le rulează singur (`rebase --exec`, `submodule foreach`, `bisect run`, alias-uri `!`). Push-ul simplu e judecat în folderul în care a ajuns comanda după `cd`. Mesajele de commit nu sunt citite ca flag-uri. Rulează pe Bash, PowerShell, terminalul aplicației și Desktop Commander. Teste: `git-guardrail.test.mjs`. |
| PostToolUse | `chisle-compress/` | Scurtează output-urile foarte lungi (originalul rămâne în `chisle-spill`). |
| Stop | `harness/verify-gate.mjs` | Dacă s-a schimbat cod, rulează typecheck, lint și teste (sau comenzile din `.claude/verify.json`). Semnalează testele șterse sau sărite (`.skip`). Agentul nu poate spune „gata” până nu trec; un timeout e NEVERIFICAT, nu trecere. Ține minte commit-ul de la începutul sesiunii, deci verifică și codul pe care agentul l-a comis înainte să se oprească. Teste: `verify-gate.test.mjs`. |
| Permisiuni | `ask` pe `.env*` (fără `.env.example`) | Editarea fișierelor cu secrete cere aprobarea ta. |
| Permisiuni | `deny` pe uneltele de proces și scriere din Desktop Commander | Ar ocoli hook-urile și regulile `.env`; Claude Code are uneltele proprii. Citirea prin Desktop Commander rămâne permisă. |
| Plugin | security-guidance | Verifică securitatea diff-urilor, în fundal. |

Oprire temporară a verificării automate: variabila de mediu `HARNESS_VERIFY=0`.

## Adăugat pe 24.10.2026, din două video AI LABS

Surse: „Anthropic Just Revealed How Their Engineers Use Claude Code” (articolul lui Felix Rieseberg despre ambiție: înălțime, adâncime, lărgime) și „Vercel's CEO Just Unveiled The Greatest AI Coding Workflow Ever” (cele 7 sfaturi ale lui Guillermo Rauch). Backup înainte de modificări: `C:\Users\LIVIUS\.claude\backups\videos-2026-10-24\`.

| Piesă | Unde | Ce face | Cum pornește |
|---|---|---|---|
| `raise-the-bar` (skill) | `~/.claude/skills/` | După articolul original al lui Felix Rieseberg ([link](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/)): scara „explică → decide → reproiectează procesul”, date brute, instrumentele expertului, verificarea presupunerilor pe date, descoperiri confirmate pe date separate, țintă „imposibilă”, judecător din afară (întâi o unealtă, apoi alt model), echipă de domenii cu „red team”. | Singur, când ceri „un dashboard”, „un raport” fără scop, sau „fă-l mai bun” |
| `direction` (skill) | `~/.claude/skills/` | Compară ce s-a construit cu PRD, specificații, tichete, ADR și Non-negotiables; tabel de scor și listă de abateri (accepți sau scoți). Nu modifică nimic. | Singur, la „ne-am abătut de la plan?” sau înainte de lansare |
| `saboteur` (sub-agent) | `~/.claude/agents/` | Încearcă să strice aplicația: pași în altă ordine, dublu-clic, două taburi, date greșite, acces la datele altuia, sarcină. Doar local/test, doar pe copii de date. | Propus înainte de lansare; pornește la „da” |
| `first-time-user` (sub-agent) | `~/.claude/agents/` | Folosește aplicația ca un client nou, doar din browser, **fără acces la cod** (are numai unelte de browser). Spune unde se blochează un începător. | Idem |
| `journey-runner` (sub-agent) | `~/.claude/agents/` | Parcurge toate traseele principale în browser și măsoară „sesiunile fără erori”; salvează `.scratch/journeys/results.json`. | Idem |
| Reguli „Aim higher, prove it” | `~/.claude/CLAUDE.md` | Rezultat, nu sarcină; dovadă, nu „am terminat”; review de alt model (`/codex:review`); fiecare Non-negotiable are verificarea lui. | Mereu (se încarcă în fiecare sesiune) |
| Indicii noi | `hooks/harness/prompt-guard.mjs` | Recunoaște „lansare”, „strică-l”, „utilizator nou”, „ne-am abătut”, „mai bun” și indică piesa potrivită. | La fiecare mesaj |
| Cuvintele tale | `prompt-guard.mjs` + tabelul din `~/.claude/CLAUDE.md` | „debug / bug fix / repară” → diagnosing-bugs + test de regresie; „test / testează” → tdd sau verificări + browser; „verifică / check” → verificările proiectului, browser, review independent. Testat în `prompt-guard.test.mjs` (`node --test`). | La fiecare mesaj |
| Secțiunea Non-negotiables | `project-starter/AGENTS.md` | Tabel „regulă → testul care o verifică”, completat la prima sesiune a proiectului. | La proiectele noi |

Deja existente, deci neduplicate: porțile de calitate (verify gate), scanarea de securitate la fiecare editare (security-guidance), review cu alt model (Codex), MVP înainte de tot (`prototype`, fluxul Matt).

Neinstalate, la cerere: **Vercel DeepSec** (scanare de securitate cu agenți; o scanare completă poate costa mult, se pune pe proiect cu `npx deepsec init`), **Sentry MCP** și **Gmail** pentru triajul automat al reclamațiilor (cer cont și autorizare).

## Adăugat pe 24.10.2026 (seara): Claude Code apelează Codex

Pornind de la video-ul lui Leon van Zyl „The 3 Levels of Harness Engineering” (nivelul 1 = configurare: AGENTS.md compus din fișiere mici, HANDOFF.md, hook-uri care impun comportamente, de ex. un Stop hook care nu lasă agentul să termine până nu a făcut ce trebuia) și de la dosarul software-factory (R2, evaluarea Claude, mega-promptul pentru Codex). Nivelurile 2 și 3 (harness propriu, orchestrator) rămân respinse, conform evaluării din 24.10. Backup înainte de modificări: `C:\Users\LIVIUS\.claude\backups\codex-harness-2026-10-24\`.

**Ce era deja:** Codex CLI 0.155.1 (actualizat în aceeași seară la 0.164.0, cu OK-ul tău, ca să vadă `gpt-6.1-sol`) autentificat cu contul ChatGPT; plugin-ul oficial OpenAI `codex` pentru Claude Code (sincronizat din claude.ai), cu `/codex:review`, `/codex:adversarial-review`, `/codex:rescue`, `/codex:status`, `/codex:setup` și o poartă opțională de review la Stop (dezactivată). Nu a trebuit instalat nimic.

**Ce s-a adăugat:**

| Piesă | Unde | Ce face |
|---|---|---|
| `codex-call.mjs` (lansator) | `~/.claude/hooks/harness/` | Claude poate apela singur plugin-ul Codex (comenzile `/codex:*` sunt doar pentru tine): `review --wait`, `adversarial-review --wait`, `task "<brief>"` (read-only), `status`, `result`, `cancel`. Găsește plugin-ul unde l-a pus Claude Code (env → synced → cache) și scrie joburile în același loc, deci `/codex:status` le vede. |
| `codex-models.json` (niveluri de model) | `~/.claude/hooks/harness/` | Regula ta: ieftin pentru lucrul obișnuit, Astra doar pentru greu/important. `light` = gpt-6-luna, `routine` = gpt-6.1-sol (effort high, implicit; `--effort xhigh` pentru greu-dar-nu-critic), `hard` = gpt-6-astra (`--hard`). Verificate pe cont cu `codex debug models` și `codex exec -m` pe CLI 0.164.0. Cu CLI 0.155.1 serverul ascundea `gpt-6.1-sol` (`model_not_found`): catalogul depinde de versiunea clientului, deci CLI-ul se ține la zi (`npm install -g @openai/codex@latest`). |
| Secțiunea „Codex: the second engine” | `~/.claude/CLAUDE.md` | Când și cum apelează Claude Codex: review înainte de „gata”/PR, challenge de arhitectură, diagnoză read-only, iar fix-urile, testele și implementările delimitate prin sub-agentul `codex:codex-rescue` (scrie în workspace, fără aprobări). Brief-ul duce fapte (simptom, reproducere, test care pică, fișiere, rânduri din ACCEPTANCE.md), nu concluzia. Rezumatul lui Codex e o afirmație, nu dovadă: Claude rulează verificările după. Un rezultat gol de la rescue = NEVERIFICAT, nu succes. |
| Regula de autonomie în două faze | `~/.claude/CLAUDE.md` + `project-starter/AGENTS.md` | Înainte de aprobarea `spec.md` + `plan.md`: întrebări, una pe rând, cu răspuns recomandat. După: fără întrebări pe ce e în ele; se oprește doar la contradicție, acces/costuri, reguli de domeniu/securitate/schemă/plăți, sau o verificare care nu se poate rula. Buget de reparații 3 încercări → **BLOCAT** cu diagnostic. Verificare nerulată = **NEVERIFICAT**. Commit pe ramura de feature doar dacă `plan.md` aprobat o permite; push/merge/deploy rămân la tine. |
| `ACCEPTANCE.md` | `project-starter/` | Tabel: ID → cerința în cuvintele tale → criteriu verificabil → comandă/scenariu → PASS/FAIL/NEVERIFICAT/BLOCAT → SHA → dovadă. Un rând fără comandă nu poate fi PASS. Îl citesc verificatorul (Codex), tu și `direction`. |
| Roluri în starter | `project-starter/AGENTS.md` | Claude construiește și decide; Codex revizuiește, testează, depanează și repară ce spune brief-ul; după un fix al unuia, celălalt re-verifică același SHA. Reguli lungi → `docs/<topic>.md`, legate din AGENTS.md (indexul lui Leon). Definition of done cere rânduri PASS în ACCEPTANCE.md și review-ul celuilalt motor. |
| Indicii noi în prompt-guard | `hooks/harness/prompt-guard.mjs` | „debug / repară” → reproduce + test care pică, apoi fix la Codex; „test” → teste independente de la Codex pe baza ACCEPTANCE.md; „verifică / review” → `codex-call.mjs review --wait`; „codex / alt model” → indiciul Codex. Limitele de cuvânt exclud cifrele (`pr2`, `gpt4`), iar „PR” cere intenție („fă un PR”), nu doar menționare. 11 teste în `prompt-guard.test.mjs`. |
| session-context | `hooks/harness/session-context.mjs` | Anunță și `spec.md`, `plan.md`, `ACCEPTANCE.md`; dacă spec+plan există, amintește regula de autonomie. |
| verify-gate | `hooks/harness/verify-gate.mjs` | Un timeout nu mai trece tăcut: blochează o dată cu „NEVERIFICAT” (agentul trebuie să ruleze el verificarea sau să spună clar că e nerulată), apoi lasă să treacă cu avertisment către tine. Buget total 540 s sub timeout-ul hook-ului de 600 s, ca verdictul să fie emis mereu (`HARNESS_VERIFY_BUDGET_SEC`). |

**Cum folosești:** nimic nou de apăsat. Scrii ca până acum („repară…”, „testează…”, „verifică…”, „întreabă codex…”). Claude trimite la Codex pe modelul `routine`; pentru lucru greu/important scrie „important” sau „cu Astra”, ori Claude decide singur după lista din CLAUDE.md. Poarta de review la fiecare Stop (`/codex:setup --enable-review-gate`) rămâne oprită: costă cotă Codex și până la 15 minute pe oprire, și plugin-ul nu are limită de reîncercări (constatare Codex); pornește-o doar pe un proiect în mod autonom, când vrei.

**Ce s-a testat efectiv (24.10, 18:20–19:10):**
- Repo de probă cu bug plantat (bucla sărea prima linie a facturii) și 2 teste care picau. `codex-call.mjs task --write` → Codex a modificat doar `src/invoice.mjs` (1 linie), testul neatins, `node --test` 3/3 la rularea mea, 1 min 10 s. `codex-call.mjs review --wait` → 40 s, read-only, fără constatări; cu nivelul `routine` la fel (gpt-6-sol pe CLI 0.155.1, apoi gpt-6.1-sol pe 0.164.0).
- Codex a revizuit chiar configurația de aici (read-only, gpt-6-astra): 9 constatări, verdict FIX NEEDED. Rezolvate: mapa de joburi și alegerea plugin-ului în lansator; contradicția autonomie ↔ „nu repara până aleg eu”; commit-ul din starter legat de plan.md; timeout-ul porții = NEVERIFICAT + buget total; rezultatul gol de la rescue; indiciile „gpt”/„pr” prea largi. Rămase, documentate: poarta de review a plugin-ului poate relua la nesfârșit (cod OpenAI, oprită); gate-ul lasă să treacă al doilea Stop pe un arbore neschimbat (intenționat, anti-buclă, cu avertisment către tine).
- Hook-urile rulate ca de Claude Code (JSON pe stdin, căi Windows): session-context listează spec/plan/ACCEPTANCE; verify-gate: trece cu ✓ când testele trec, tace pe arbore neschimbat, blochează la test picat (attempt 1/3), blochează o dată la timeout și avertizează a doua oară. `node --test prompt-guard.test.mjs`: 11/11.
- Modele pe cont (CLI 0.164.0): 6.1-sol, astra, 6-sol, 6-luna, reserve, 5.6-sol, 5.6-terra, 5.6-luna merg; 6.1-sol-mini, 5.4-mini, 5.3-codex-spark sunt refuzate. Pe CLI 0.155.1 și 6.1-sol era refuzat: a fost versiunea clientului, nu numele modelului (observația ta).

**Lecție după update-ul CLI:** plugin-ul ține pentru fiecare proiect un `codex app-server` partajat în fundal (`broker.json` în `~/.claude/plugins/data/codex-inline/state/<proiect>/`). După `npm install -g @openai/codex@…` acel proces rămâne pe binarul vechi și dă `model_not_found` până e oprit. L-am oprit cu comanda proprie a plugin-ului (`broker/shutdown`), apoi review-ul pe `gpt-6.1-sol` a trecut. Dacă se repetă: închide sesiunea Claude a proiectului (hook-ul SessionEnd oprește brokerul) sau cere-mi să îl opresc.

**Neatins intenționat:** tot ce e sub `~/.codex` (AGENTS.md, config.toml, hooks). Codex își face singur configurarea din `MEGA-PROMPT-CODEX-SETUP-2026-10-24.md`. `config.toml` cu `model = "gpt-6.1-sol"` e corect pe CLI 0.164.0; pe 0.155.1 dădea `model_not_found`. Dacă apare din nou eroarea, verifică întâi versiunea CLI.

## Adăugat pe 24.10.2026 (noapte): skill-ul Autopilot (nick-vels/skills), la comandă

Instalat la cererea ta, ca skill pornit **doar** când tastezi `/autopilot` într-un proiect ales de tine. Nu se declanșează singur (are `disable-model-invocation: true` din fabrică, iar hook-ul de indicii sare peste comenzile cu `/`). Fluxul Matt rămâne cel implicit pentru restul.

- **Instalare:** `npx skills add nick-vels/skills --skill autopilot -g -y -a claude-code` → copie în `~/.claude/skills/autopilot` (v2.2.0, MIT). Update: `npx skills update autopilot -g`; scoatere: `npx skills remove autopilot -g`. Apare în listă după repornirea sesiunii.
- **Folosire:** `/autopilot <ideea>` sau `/autopilot brief.md`; moduri `full | semi (implicit) | interview | manual`, adâncime `strict | normal | deep`; `/autopilot` gol reia o rulare întreruptă. Creează `.autopilot/` (manifest, spec, tichete, `state.js`, dashboard local pe 127.0.0.1) și face un commit per ticket. Fără push.
- **Verificarea de conflict (Codex, read-only, apoi reparat):**

| Problemă găsită | Rezolvare |
|---|---|
| Regula `ask` pe `Edit(**/.env.*)` prindea și `.env.example`, pe care Autopilot îl scrie des | Documentația oficială: ordinea e deny → ask → allow, deci un `allow` pe `.env.example` nu poate face excepție de la `ask` pe `.env.*`. Soluția: lista explicită în `settings.json` (`.env`, `.local`, `.development`, `.dev`, `.production`, `.prod`, `.staging`, `.test`, `.ci`, `.preview`, `.backup`, `.secret*`, `.*.local`); `.env.example` (doar nume, fără valori) nu mai cere aprobare. Un nume neobișnuit de fișier `.env.<altceva>` nu mai e acoperit: adaugă-l în listă dacă îl folosești. Scris și în CLAUDE.md și în starter. |
| verify-gate ar fi rulat testele la fiecare oprire a orchestratorului, pe un arbore în care executanții încă scriu | Poarta se oprește singură cât `.autopilot/state.js` arată o rulare neterminată cu „puls” (data din `updatedAt` sau a fișierului, care se rescrie la orice comandă `ap.py`) mai nou de 12 ore. O rulare tăcută peste 12 ore (abandonată sau pauză lungă) nu mai ține poarta oprită; la pornirea sesiunii primești un rând „rulare Autopilot neterminată, inactivă de N h; `/autopilot` gol o reia”, iar la reluare pauza revine singură. Testat: activ → pauză; vechi → verifică; terminat → verifică. |
| Indiciile din prompt-guard și re-afirmarea regulilor Matt după compactare ar fi reintrodus Matt/Codex în mijlocul rulării | Cât rulează Autopilot, prompt-guard păstrează doar blocarea secretelor, iar session-context anunță rularea în loc de pașii starterului. Test de regresie în `prompt-guard.test.mjs` (12/12). |
| CLAUDE.md trimitea fix-urile la Codex și skill-uri Matt, prompt-ul executorului Autopilot le interzice | Regulă în CLAUDE.md: în `/autopilot` conduc fazele lui; executanții nu cheamă Codex/Matt; review Codex doar la acceptanța finală, dacă îl ceri. |
| `git add -A -- <zonă>` ar lua și modificări ale tale preexistente în acea mapă | Regulă: `/autopilot` pornește doar pe arbore curat; altfel se oprește și îți cere commit/stash. |
| Acceptanța lui copiază `.env` real în clona de test (poate atinge servicii reale) | Regulă: niciodată `.env` real; `.env.example` + valori de test; ce cere un serviciu real = NEVERIFICAT. |
| Exemple și denumiri în rusă | Regulă: română cu tine, engleză în cod/comentarii/commit-uri; exemplele lui sunt exemple. |
| Starter-ul cere spec/plan aprobate și review-ul celuilalt motor | Paragraf „If the owner runs /autopilot” în `project-starter/AGENTS.md`: comanda înlocuiește fluxul spec → tichete; manifest/spec din `.autopilot/` țin loc de spec.md/plan.md; verdictele acceptanței se copiază în `ACCEPTANCE.md`. |

- **Rămas documentat, neschimbat:** poarta de review Codex la Stop (plugin OpenAI) nu are excepție pentru Autopilot; e oprită. `python3` e stub-ul Microsoft Store pe Windows; skill-ul cade singur pe `python`/`py -3` (3.14 prezent, testat `ap.py init`). Verificarea de versiune merge la GitHub doar la `init --check-update`; `AUTOPILOT_NO_UPDATE_CHECK=1` o oprește.
- **NEVERIFICAT:** o rulare completă `/autopilot` pe un proiect real (consumă cotă; o pornești tu când vrei).

## Livius: arhivat

Matt Pocock 1.3.1 face acum nativ tot ce făcea Livius: interviu, spec, tichete, implementare paralelă în worktree-uri, review, PR. Livius era un strat de 33 KB peste același flux, se strica la fiecare update Matt și nu l-ai folosit niciodată. Ce avea util a trecut în configurația globală: regulile pentru tine (non-programator, răspuns în română), protecția git și review-ul cu Codex.

Copia arhivată (deja adaptată la Matt 1.3.1) e în `backups\harness-2026-10-24\livius-archived`. Ca să-l readuci, copiază folderul înapoi în `C:\Users\LIVIUS\.claude\skills\livius`.

## Pluginuri

- `mattpocock-skills` 1.3.1
- `security-guidance`
- `playwright`
- `typescript-lsp`, `pyright-lsp`
- `codex` (OpenAI, sincronizat din claude.ai): review, adversarial-review, rescue, status; apelat și de Claude prin `hooks/harness/codex-call.mjs`

Toate sunt oficiale, cu excepția Matt.

## Ce NU s-a instalat și de ce

| Repo | Motiv |
|---|---|
| claude-mem | Hook pe fiecare apel de unealtă, telemetrie, consumă din abonament; dublează memoria automată din Claude Code. |
| pxpipe | Proxy cu pierdere de informație; cere interceptarea token-ului; încalcă ToS. |
| OmniRoute | Gateway terț care poate prelua token-ul; risc de blocare a contului. |
| Ouroboros, nick-vels autopilot | Al doilea orchestrator peste fluxul Matt. |
| REA | Reverse engineering, irelevant pentru aplicațiile tale. |
| addyosmani/agent-skills | Concurează direct cu Matt Pocock. |
| unlazy, i-have-adhd | Conflict cu verify gate și cu formatul tău de răspuns. |
| Chisle (reguli) | Regulile „gândește mai puțin”; a rămas doar compresorul. |
| Firecrawl, Perplexity | Cer chei API plătite. |
| MCP-uri de transcriere YouTube | Puțin folosite (4–58★); youtube-fetcher e mai complet. |

## Proiecte noi: mapa `project-starter`

Pornește de la kitul lui Leon van Zyl (`agentic-coding-starter-kit`). Kitul lui copiază în fiecare proiect `CLAUDE.md` (doar `@AGENTS.md`), `AGENTS.md` cu „reguli critice”, `DESIGN.md`, 6 sub-agenți, 17 skill-uri (de două ori: `.claude/skills` și `.agents/skills`), `settings.local.json` și CI.

La noi, skill-urile, hook-urile și MCP-urile sunt deja globale. De aceea mapa conține doar ce ține de proiect și nu dublează nimic:

| Fișier | Rol |
|---|---|
| `CLAUDE.md` | Importă `AGENTS.md`, plus note doar pentru Claude |
| `AGENTS.md` | Reguli comune pentru Claude și Codex, plus secțiunea „First session” |
| `DESIGN.md` | Sistemul vizual (gol până îl stabilești cu `impeccable`) |
| `GLOSSARY.md`, `docs/adr/` | Vocabularul și deciziile (Matt Pocock `domain-modeling`) |
| `.claude/settings.json` | Comenzile sigure permise; `db push` interzis |
| `.claude/rules/` | Reguli care se încarcă doar pentru fișierele lor: teste, UI, baze de date, 1C |
| `.claude/verify.example.json` | Comenzile de verificare, după ce există |
| `.github/workflows/ci.yml` | Aceleași verificări pe GitHub; sare peste ce nu există încă |
| `.gitignore` | Secrete, `.scratch/`, `HANDOFF.md` |

Nu am copiat sub-agenții și skill-urile lui Leon în proiect. Rolurile lor (cod, review, securitate, spec) le acoperă deja Matt Pocock, security-guidance și skill-urile globale. Două seturi ar intra în conflict.

**Folosire:** dublu-clic pe `Proiect-nou.cmd` și scrii calea mapei. Scriptul nu suprascrie niciun fișier existent și pornește git. La prima sesiune, hook-ul vede marcajul `starter:unfilled`, iar Claude completează singur `AGENTS.md` din cod și te întreabă doar ce nu poate afla.

Varianta din linia de comandă: `.\new-project.ps1 -Path "C:\Proiecte\x" -Name "Nume"`.

## Revenire la configurația veche

Copiază `settings.json` și `CLAUDE.md` din backup înapoi în `C:\Users\LIVIUS\.claude\` (ultimul: `backups\harness-fix-2026-10-24`).

Din 24.10.2026, mapa aceasta și `C:\Users\LIVIUS\.claude\hooks\` sunt depozite git: orice modificare a hook-urilor sau a documentației se poate anula. Testele hook-urilor: `node --test "harness/*.test.mjs"` rulat din `C:\Users\LIVIUS\.claude\hooks\`.
