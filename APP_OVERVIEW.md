# Clinic App — Token & Queue System (Blueprint)

> Source: `context-images/` folder ke 16 screenshots (Clinic App Blueprint, 12 Screens).
> Tagline: *"Register aur parchi se online token, live queue aur doctor panel tak. Har screen, aur har screen ka kaam."*

---

## 1. Yeh application kya hai?

Yeh ek **clinic ke liye token / queue management app** hai. Clinic ka offline system (register, parchi, line mein intezaar, reception pe phone calls) ko **online** le aata hai:

- Mareez ghar baithe **online token** le sakta hai
- Phone pe **live queue** dekh sakta hai (abhi kaunsa number chal raha hai)
- Reception walk-in mareezon ko bhi usi queue mein add karta hai
- Doctor ek tap se **NEXT** patient bulata hai
- Waiting room ke **TV** pe bada number dikhta hai
- Malik (owner) ko **roz ki report** milti hai

---

## 2. Problems jo yeh solve karta hai (Offline — aaj ki problems)

| # | Problem | Detail |
|---|---------|--------|
| 1 | **Register aur parchi** | Har mareez ko naam haath se likhna |
| 2 | **Intezaar** | Mareez ko pata nahi number kab aayega, waiting room full |
| 3 | **Reception ka phone** | "Number kitna chal raha hai?" — purani file dhoondhna |

**Solution:** `1 app · 5 hisse (roles) · 12 screens`

---

## 3. Users / Roles (5 hisse)

| Role | Screens | Device |
|------|---------|--------|
| 👤 **Mareez** (Patient) | 3 screens | Phone (sirf link — app install nahi) |
| 🖥️ **Reception** | 3 screens | Computer / Tablet |
| 🧑‍⚕️ **Doctor** | 2 screens | Tablet / Phone |
| 📺 **Waiting Room** | 1 screen | Smart TV / Monitor |
| 👑 **Malik** (Owner) | 2 screens | Phone |
| 🔑 **Login** (Clinic staff) | 1 screen | Sab staff |

---

## 4. Flow — "Ek token ka safar"

1. **Mareez token leta hai** — link se, ghar baithe
2. **Reception list mein dikhta hai** — walk-in bhi isi line mein
3. **Doctor NEXT dabata hai** — purani history saamne
4. **TV aur phone pe number badalta hai** — dono jagah ek saath
5. **Malik report dekhta hai** — roz ka hisaab phone pe

```
Mareez (online token) ─┐
                       ├─► Queue ─► Doctor "NEXT" ─► TV + Mareez phone update ─► Malik report
Reception (walk-in) ───┘
```

---

## 5. Screens (12) — Detail

### 👤 Mareez (Patient)

#### Screen 1 — Token Booking
**Kaam:** Mareez ghar baithe ek link se token le le. Clinic aane se pehle hi uska number pakka.
- Doctor / OPD chunna
- Din chunna: aaj ya kal
- Naam aur phone number
- Token limit poori ho to booking apne aap band
- Link Google Maps, Instagram ya WhatsApp pe share karo *(optional)*

**Kaun use karega:** Mareez (phone pe, app install nahi)

#### Screen 2 — Token Confirm
**Kaam:** Booking ke turant baad mareez ko apna token number aur andaazan time dikhe (e.g. "Apna Token #18, Andaazan time 11:40 AM").
- Token number
- Andaazan time
- Live queue dekhne ka button
- Token cancel karne ka option *(optional)*
- SMS / WhatsApp pe confirmation *(optional)*

#### Screen 3 — Live Queue
**Kaam:** Mareez ko phone pe live dikhe ki abhi kaunsa number chal raha hai, aur uski baari kab aayegi.
- Abhi chal raha token
- Mareez ka apna token
- Kitne log aage hain
- Andaazan wait time
- Apne aap update (refresh)
- Baari aane se pehle reminder *(optional)*

### 🖥️ Reception

#### Screen 4 — Aaj ki List
**Kaam:** Reception pe aaj ke saare token ek jagah, status ke saath. Register ki zaroorat khatam.
- Har token ka status: waiting / chal raha / aaya nahi
- Mareez aaya to "arrived" mark
- Doctor ke hisaab se filter
- Naam ya number se search

#### Screen 5 — Walk-in Entry
**Kaam:** Jo mareez seedha clinic aaye, uska token turant banao. Wo bhi usi line mein jud jaata hai.
- Naam, phone, doctor
- Naya token turant
- Online aur walk-in, dono ek hi queue mein
- Token slip print *(optional)*
- SMS pe token number *(optional)*

#### Screen 6 — Patient Search
**Kaam:** Purani file dhoondhne ki zaroorat nahi. Phone number ya naam daalo, mareez saamne.
- Phone ya naam se search
- Kitni visits huin
- Last visit ki date
- Mareez ki profile

### 🧑‍⚕️ Doctor

#### Screen 7 — Next Patient
**Kaam:** Doctor ke liye ek tap: agla mareez bulao. TV aur mareez ke phone pe number apne aap badal jaata hai.
- Abhi wala token
- NEXT button
- Agle 3 token
- Mareez ko skip / hold karna

#### Screen 8 — Patient History
**Kaam:** Mareez ki purani visits ek nazar mein. Kya hua tha, kya dawa di thi.
- Visits ki timeline
- Har visit ke notes
- Dawa / advice
- Reports ya photos attach karna *(optional)*

### 📺 Waiting Room

#### Screen 9 — TV Screen
**Kaam:** Waiting room ke TV pe bada number. Awaaz lagane ki zaroorat nahi.
- Abhi chal raha token (bada)
- Agle tokens
- Clinic ka naam
- Announcement / awaaz ke saath number *(optional)*

**Kaun use karega:** Waiting room (koi bhi smart TV ya monitor)

### 👑 Malik (Owner)

#### Screen 10 — Roz ki Report
**Kaam:** Malik ko clinic ka poora din ek nazar mein, phone pe.
- Aaj kitne mareez aaye
- Average wait time
- 7 din ka chart
- Kitne mareez aaye nahi (no-show)
- Mahine ki report download *(optional)*

**Kaun use karega:** Malik / Doctor

#### Screen 11 — Settings
**Kaam:** Clinic ke rules aap khud set karo, developer ki zaroorat nahi.
- Online token ON / OFF
- Roz ka token limit
- OPD timing
- Doctors add / remove

### 🔑 Staff

#### Screen 12 — Login
**Kaam:** Staff ka safe login. Har kisi ko sirf apna kaam dikhe.
- Mobile number + OTP
- Role ke hisaab se access: reception, doctor, malik
- Logout

---

## 6. Future Add-ons — "Aur kya jud sakta hai"

- **WhatsApp / SMS reminder** — baari se pehle mareez ko reminder (provider ke through)
- **Online payment** — consultation fee pehle hi
- **Prescription / report upload** — mareez ke liye digital
- **Multiple doctors / branches** — har doctor ki alag queue
- **Hindi + English** — zubaan ka option

---

## 7. Kaam kaise hoga — 5 Steps

1. **Baat-cheet** — clinic ki zaroorat samajhna: kitne doctor, timing, rush
2. **Design** — screens pehle dikhenge, aapki haan ke baad hi build
3. **Build + Testing** — clinic mein asal use karke check
4. **Training** — reception aur doctor ko chalana sikhana
5. **Handover** — code aur saare accounts clinic ke naam pe

---

## 8. Technical Summary (development ke liye)

**Core entities:**
- `Clinic` (naam, OPD timing, daily token limit, online token on/off)
- `Doctor` / OPD
- `Patient` (naam, phone, visits)
- `Token` (number, date, doctor, source: online/walk-in, status: waiting / serving / done / skipped / hold / no-show, estimated time)
- `Visit` (notes, dawa/advice, attachments)
- `Staff User` (mobile, role: reception / doctor / malik)

**Key requirements:**
- Real-time updates (doctor NEXT → TV + reception + mareez phone sab jagah turant)
- Patient side bina login / bina app install — sirf shareable web link
- Staff side OTP login + role-based access
- Online aur walk-in tokens ek hi queue mein
- Daily limit poori hone pe booking auto-close
- Mobile-first patient screens; tablet/desktop reception; full-screen TV display
