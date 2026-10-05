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

### Step 4: Aur bug fixes (ek-ek karke, har ek ke saath test)
- [ ] Loop ke andar lambda/closure ka late binding (`[lambda: i for i in range(3)]`)
- [ ] `==` se float compare karne par warning (`0.1 + 0.2 == 0.3`)
- [ ] Function ke andar global variable ko bina `global` ke badalne par saaf error

Rule: koi fix tabhi jode jab woh Python ki library ko na tode aur Python jaanne
wale ko hairaan na kare.

### Step 5: Editor support
- [ ] VS Code me `.am` files ko Python ki tarah colour karna (sirf `files.associations` setting)
- [ ] Ek chhota VS Code extension

### Step 6: Release
- [ ] PyPI par publish karna, taaki koi bhi `pip install amlang` kar sake
- [ ] Documentation website

## Naya bug fix kaise jodein

1. `tests/test_fixes.py` me ek test likho jo bug dikhaye (abhi fail hoga).
2. `amlang/fixer.py` me ek `visit_<NodeType>` function jodo.
3. `python -m unittest discover -s tests` chalao, sab pass hona chahiye.
4. README ki "Bugs AM fixes" table me ek line jodo.
