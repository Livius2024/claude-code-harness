# Porțile GitHub ale fabricii (branch protection + auto-merge)

În firele (threads) unui proiect claude.ai nu rulează hook-uri, `settings.json` sau skill-uri din repo. De aceea tot ce nu are voie agentul să sară stă în GitHub. Agentul deschide PR-ul și pornește auto-merge; GitHub îl unește singur doar când toate verificările obligatorii sunt verzi.

| Poartă | Unde | Ce oprește |
|---|---|---|
| `checks` | `.github/workflows/ci.yml` | Teste (pytest / npm test), tipuri (pyright / typecheck), lint (ruff / lint), build |
| `acceptance` | `ci.yml` + `scripts/check_acceptance.py` | O cerință `R<n>` din `spec.md` fără rând în `ACCEPTANCE.md`, rânduri orfane, PASS fără comandă, SHA sau dovadă |
| `owner-approval` | `.github/workflows/owner-approval.yml` + `.github/owner-approval-paths.txt` | Un PR care atinge reguli fiscale/audit/contabile/legale, contractul (`spec.md`, `plan.md`, `AGENTS.md`) sau porțile, până pui tu eticheta `owner-approved` |
| `browser-qa` (opțional) | `.github/workflows/browser-qa.yml` + `e2e/` | Un ecran care nu se deschide sau nu arată ce cere `ACCEPTANCE.md`, la desktop și pe telefon. Pune pe PR un comentariu cu capturi de ecran. Oprit până există `e2e/playwright.config.ts` |
| Review Codex | chatgpt.com → Settings → Code review (automatic) | Constatări P0/P1 după `## Code Review Rules` din `AGENTS.md`; PR-ul nu se unește până nu sunt rezolvate conversațiile |
| Protecția ramurii `main` | `.github/branch-protection.json` | Push direct, force-push, ștergere; merge fără cele 3 verificări verzi sau cu conversații nerezolvate |

## Pornire (o singură dată pe repo, ~2 minute)

Ai nevoie de `gh` (GitHub CLI) autentificat (`gh auth login`). Comenzile merg la fel în PowerShell și în bash. Rulează-le din mapa proiectului, după primul push pe GitHub.

1. Permite auto-merge și ștergerea ramurilor după merge:
   ```
   gh repo edit --enable-auto-merge --enable-squash-merge --delete-branch-on-merge
   ```
2. Creează eticheta cu care aprobi tu:
   ```
   gh label create owner-approved --color 0E8A16 --description "Owner reviewed the domain-rule or gate changes"
   ```
3. Protejează `main`:
   ```
   gh api -X PUT "repos/{owner}/{repo}/branches/main/protection" --input .github/branch-protection.json
   ```
4. Verifică: `gh api "repos/{owner}/{repo}/branches/main/protection" --jq ".required_status_checks.contexts"` trebuie să arate cele 3 nume.

**Repo privat pe planul GitHub Free:** pasul 3 dă `HTTP 403 Upgrade to GitHub Pro`. Protecția ramurilor și auto-merge pe repo-uri private cer GitHub Pro (sau repo public). Fără ele, verificările rulează și se văd roșu/verde, dar nimic nu le impune.

## Cum lucrezi zilnic

- **PR obișnuit:** nu faci nimic. Agentul deschide PR-ul, pornește auto-merge, repară ce găsesc CI și Codex; GitHub unește când e verde.
- **PR care atinge reguli** (fiscal, audit, contabil, legal, contract, porți): `owner-approval` e roșu și agentul îți scrie un rând în fir cu fișierele. Te uiți la diff, apoi:
  ```
  gh pr edit <număr> --add-label owner-approved
  ```
  (sau pe github.com: PR → Labels → `owner-approved`). Verificarea se reia singură și PR-ul se unește. Agentul nu pune niciodată eticheta el însuși.
- **Altă listă de căi protejate:** editezi `.github/owner-approval-paths.txt` (un glob pe rând). Verificarea (workflow-ul, scriptul și lista) rulează mereu în versiunea de pe `main` (`pull_request_target`), deci un PR nu se poate „deproteja” singur; schimbarea listei e ea însăși un PR care îți cere eticheta.
- **Primul commit:** starter-ul trebuie să ajungă pe `main` înainte de primul PR (așa face `new-project.ps1` + primul tău commit). Altfel `owner-approval` nu rulează pe acel PR și GitHub îl așteaptă la nesfârșit.
- **Limită cunoscută:** un PR care schimbă `.github/` poate adăuga un job cu același nume (`owner-approval`) care trece mereu. Poarta reală tot îl marchează roșu, iar Codex îl semnalează ca P0, dar uită-te la diff-ul din `.github/` înainte să pui eticheta.
- **PR rămas în urma lui `main`** (`strict: true`): agentul face „Update branch” și CI rulează din nou pe codul unit.

## QA în browser cu capturi pe PR (aplicații web)

- **Pornire:** agentul o pornește singur la primul ecran (redenumește `e2e/playwright.config.example.ts` în `e2e/playwright.config.ts` și pune comanda de pornire a aplicației, vezi `e2e/README.md`). E gratuit: rulează pe GitHub Actions, fără servicii plătite.
- **Ce vezi:** pe fiecare PR apare un comentariu „Browser QA” cu un tabel (fiecare verificare, cu cerința `R<n>`, pe desktop și pe telefon) și capturile de ecran. Raportul complet e în artefactul `browser-qa` al rulării (14 zile).
- **Unde stau capturile:** pe ramura `browser-qa-screenshots`, creată automat, câte o mapă `pr-<număr>/`. O poți șterge oricând; se recreează la următorul PR (comentariile vechi rămân fără imagini). Pe un repo **public** capturile sunt publice, de aceea verificările folosesc doar date de test.
- **Opțional, s-o faci obligatorie:** Settings → Branches → `main` → Edit → „Require status checks” → adaugă `browser-qa`. Pe un proiect fără interfață web trece oricum (nu face nimic), deci nu blochează.
- **Repo privat:** capturile din comentariu se văd doar când ești logat pe GitHub cu acces la repo (NEVERIFICAT încă pe un repo privat; artefactul merge oricum).

## Ce nu se poate impune din GitHub

- Calitatea testelor: Codex le judecă (P1 „comportament nou fără test”), nu CI.
- Că agentul chiar a întrebat înainte de spec/plan: regula e în `.claude/rules/factory.md`; tu aprobi `spec.md` și `plan.md` (sunt căi protejate).
