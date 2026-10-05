# AM language: banane ke steps

## Idea (ek line me)

AM = Python ki syntax + Python ki saari libraries + kuch Python bugs ka automatic fix.

Hum apna parser nahi banate. Python ka apna parser (`ast` module) code ko tree
me badalta hai, hum us tree me sirf bugs wale hisse badalte hain, aur Python
use chala deta hai.

```
.am file → ast.parse → Fixer (amlang/fixer.py) → compile → run
```

## Project ka dhaancha

| File | Kaam |
|---|---|
| `amlang/fixer.py` | Saare bug fixes. Har fix ek `visit_*` function hai |
| `amlang/__init__.py` | `.am` file compile karna, aur `import` se `.am` files dhundhna |
| `amlang/errors.py` | Aasaan error messages aur hints |
| `amlang/check.py` | `am --check`: bina chalaye problems dhundhna |
| `editors/vscode/` | VS Code extension |
| `site/` | Website (GitHub Pages) |
| `amlang/cli.py` | `am` command aur interactive prompt |
| `tests/test_fixes.py` | Har fix ka test |
| `examples/` | Example `.am` programs |

## Steps

### Step 1: Core (ho gaya ✅)
- [x] `.am` file chalana: `am file.am`
- [x] Interactive prompt: `am`
- [x] `.am` files ek doosre ko `import` kar sakein
- [x] Python files bhi `.am` files import kar sakein (`import amlang`)
- [x] Saari Python libraries chalein
- [x] Tests + GitHub Actions CI

### Step 2: Pehle 4 bug fixes (ho gaya ✅)
- [x] Mutable default arguments (`def f(x=[])`)
- [x] Literals ke saath `is` (`x is 1000`)
- [x] Bare `except:`
- [x] Built-in naam overwrite karna (`list = ...`)

### Step 3: Aasaan error messages (ho gaya ✅)
- [x] Python ke lambe traceback ki jagah chhota, saaf message: file + line + code, kya galat hai, kaise theek karein (`amlang/errors.py`)
- [x] Aam galtiyon ke hint: spelling galti par "Did you mean ...?", text + number, `None` value, `pip install`, divide by zero, missing `:` waghaira
- [x] Library ke andar error ho to batana ki kaunsi library, aur aapki kaunsi line ne use call kiya
- [x] `am --traceback file.am` se pura Python traceback bhi dekh sakte hain

### Step 4: Aur bug fixes (ho gaya ✅)
- [x] Loop ke andar lambda/`def` ka late binding: `[lambda: i for i in range(3)]` ab `0, 1, 2` deta hai
- [x] Decimal number ko `==` se compare karne par warning (`total == 0.3`), `math.isclose` ka hint
- [x] Function ke andar bahar wale variable par `+=` (bina `global`/`nonlocal`) ka saaf error, program chalne se pehle
- [x] Check: Python ki standard library ki saari files AM Fixer se bina crash compile hoti hain

Rule: koi fix tabhi jode jab woh Python ki library ko na tode aur Python jaanne
wale ko hairaan na kare.

### Step 5: Editor support (ho gaya ✅)
- [x] `am --check file.am`: program chalaye bina errors/warnings dhundhna (`--json` editors ke liye)
- [x] VS Code extension (`editors/vscode/`): Python jaise colours, auto-indent, comments
- [x] Type karte waqt laal/peeli lines, hint ke saath (wahi messages jo `am` deta hai)
- [x] ▶ Run button jo file ko terminal me `am` se chalata hai
- [x] CI har push par extension test karta hai aur `.vsix` file banata hai (Actions → Artifacts)

### Step 6: Release (ho gaya ✅)
- [x] MIT License: AM sabke liye free
- [x] PyPI naam `am-language` (`amlang`/`am-lang` nahi mil sakte: PyPI unhe ek hi naam maanta hai). Command `am` hi rahega
- [x] `am --version`
- [x] Package build + `twine check` pass, aur saaf venv me wheel install karke test kiya
- [x] Release workflow (`.github/workflows/release.yml`): GitHub release banate hi PyPI par publish + `.vsix` release me attach
- [x] PyPI par publish ki permission (trusted publisher)
- [x] Release `v0.1.0` (VS Code `.vsix` ke saath)
- [x] Release `v0.1.1`: AM PyPI par live, https://pypi.org/project/am-language/
- [x] VS Code Marketplace + Open VSX publish ka setup (release workflow me) — Step 7 dekho
- [x] Website: `site/` folder, GitHub Pages par — Step 8 dekho

#### PyPI par pehli baar publish kaise karein

1. https://pypi.org/account/register/ par account banao (email verify aur 2FA on karna zaroori hai).
2. https://pypi.org/manage/account/publishing/ kholo → **Add a new pending publisher** → GitHub tab me ye bharo:
   - PyPI Project Name: `am-language`
   - Owner: `chaman640`
   - Repository name: `Python-based-language.am`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
3. GitHub repo → **Settings → Environments → New environment** → naam `pypi` → Save.
4. GitHub repo → **Releases → Draft a new release** → naya tag (jaise `v0.1.1`) → **Publish release**.
5. **Actions** tab me `release` workflow chalega. Hara (green) hone ke baad koi bhi
   `pip install am-language` kar sakta hai, aur `.vsix` file release page par mil jaayegi.

Agli baar release ke liye: `pyproject.toml`, `amlang/__init__.py` aur
`editors/vscode/package.json` me version badhao (jaise `0.2.0`), phir naya release banao.

### Step 7: VS Code Marketplace
- [x] Icon (`editors/vscode/images/icon.png`), author, keywords, Marketplace README
- [x] Release workflow `VSCE_PAT` secret ho to Marketplace par publish karta hai (aur `OVSX_PAT` ho to Open VSX par)
- [ ] **Aapko ek baar karna hai** (neeche ke steps), phir release `v0.1.2`

#### Marketplace par pehli baar publish kaise karein
1. https://dev.azure.com par Microsoft account se login karo (free). Pehli baar ho to ek organization banane ko kahega, koi bhi naam do.
2. Upar right **User settings** (aadmi wala icon) → **Personal access tokens** → **New Token**:
   - Name: `vsce`
   - Organization: **All accessible organizations**
   - Expiration: sabse lamba (1 saal)
   - Scopes: **Custom defined** → **Show all scopes** → **Marketplace** → **Manage** tick karo
   - **Create** → jo token dikhe use copy kar lo (ye dobara nahi dikhega)
3. https://marketplace.visualstudio.com/manage par usi Microsoft account se jao → **Create publisher**:
   - ID: `chaman640` (bilkul yahi, kyunki `package.json` me yahi hai)
   - Name: `Anuj Mishra`
4. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - Name: `VSCE_PAT`, Secret: step 2 wala token
5. GitHub → **Releases → Draft a new release** → tag `v0.1.2` → **Publish release**.
6. Kuch minute baad VS Code me Extensions panel me "AM Language" search karne par extension dikhega.

### Step 8: Google aur AI chatbots par AM aur Anuj Mishra
- [x] Website `site/index.html`: "AM programming language, created by Anuj Mishra", structured data (Google ko batata hai ki creator kaun hai), FAQ
- [x] `sitemap.xml`, `robots.txt`, `llms.txt` (AI chatbots ke liye short parichay)
- [x] Har jagah author "Anuj Mishra": PyPI, VS Code, LICENSE, `am --version`, `CITATION.cff`
- [ ] **Aapko karna hai:**
  1. GitHub repo → **Settings → Pages** → Source: **GitHub Actions**. Phir **Actions → website → Run workflow**.
     Website khulegi: https://chaman640.github.io/Python-based-language.am/
  2. GitHub repo page par **About** ke paas ⚙️ → Description: `AM programming language by Anuj Mishra: Python syntax, fewer bugs`,
     Website: upar wala link, Topics: `programming-language`, `python`, `beginners`, `am-language`
  3. https://search.google.com/search-console → **URL prefix** me website ka link → verify (HTML tag ya file) →
     **Sitemaps** me `sitemap.xml` submit → **URL inspection** → **Request indexing**
  4. Logon tak pahunchao: LinkedIn, Reddit (r/Python, r/learnprogramming), dev.to par post likho
     "I built AM, a Python-based programming language" — har post me website ka link.
     Jitni jagah link hoga, Google aur AI utni jaldi AM ko pehchanenge.

## Naya bug fix kaise jodein

1. `tests/test_fixes.py` me ek test likho jo bug dikhaye (abhi fail hoga).
2. `amlang/fixer.py` me ek `visit_<NodeType>` function jodo.
3. `python -m unittest discover -s tests` chalao, sab pass hona chahiye.
4. README ki "Bugs AM fixes" table me ek line jodo.
