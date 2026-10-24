# Mega-prompt (rezervă)

Nu e nevoie să-l lipești la fiecare mesaj. Aceleași reguli sunt deja în `C:\Users\LIVIUS\.claude\CLAUDE.md`, iar hook-urile adaugă singure un „Skill hint” la fiecare mesaj.
Folosește-l doar dacă observi că un skill nu a pornit singur. Lipește-l o singură dată, la începutul conversației.

```text
Before you answer, check the skill tables in my global CLAUDE.md and use the matching Matt Pocock skill without waiting for me to name it: bugs → mattpocock-skills:diagnosing-bugs, new logic → mattpocock-skills:tdd, plans → mattpocock-skills:grilling, a feature bigger than one sitting → grill-with-docs → to-spec → to-tickets → implement (read those SKILL.md files inline and ask me once before starting), UI → impeccable + emil-design-eng, new app → start-an-app + ui-craft-layer, missing capability → find-skills, video → youtube-fetcher. Don't guess: read the code first and ask me when a rule is unclear. Never skip or delete a failing test. Tell me which checks actually ran. When I have to do something myself, answer in Romanian with numbered steps as my CLAUDE.md says.
```
