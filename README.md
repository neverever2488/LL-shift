# Phase Shift 🎮

Retro platformera spēle, kas veidota, izmantojot Python un Pygame. Spēlei ir adaptīva ekrāna mērogošana, unikālas spēles mehānikas, pielāgojami tēlu izskati (skins) un lokālā līderu tabula.

## 🚀 Ātrais starts

### 1. Projekta lejupielāde un sagatavošana
Lejupielādējiet spēles mapi savā datorā un atveriet termināli (vai komandrindu) šajā mapē.

### 2. Atkarību instalēšana
Pārliecinieties, ka jūsu sistēmā ir instalēts Python 3. spēles darbināšanai nepieciešama `pygame` bibliotēka. Instalējiet to, izpildot komandu:
```bash
pip install pygame
```
*(Ja izmantojat virtuālo vidi, pirms tam aktivizējiet to vai izmantojiet sava projekta vietējo `pip` ceļu).*

### 3. Spēles palaišana
Lai spēle pareizi ielādētu visus nepieciešamos failus, datubāzes un iestatījumus, palaidiet to no projekta saknes mapes:
```bash
python game/phase_shift.py
```

---

## 🕹️ Spēles vadība un unikālās mehānikas

*   **Kustība:** Bultiņas `Pa kreisi` / `Pa labi` vai taustiņi `A` / `D`.
*   **Lēciens:** `Atstarpe` (Space).
*   **🔋 Uzlādētais lēciens (Charged Jump):** Īpaša mehānika, kas aizvieto standarta elementus un ļauj spēlētājam veikt paaugstinātu lēcienu, lai sasniegtu grūti pieejamas vietas.
*   **✨ Parādīšanās platforma (Appearing Platform):** Dinamiska platformu mehānika (koda konstantēs apzīmēta kā `TEMP`), kas aktivizējas vai parādās tikai noteiktos brīžos, izaicinot spēlētāja reakciju un laika plānošanu.
*   **Navigācija izvēlnē (Menu):**
    *   Kustība uz augšu/leju — bultiņas `Uz augšu` / `Uz leju` vai `W` / `S`.
    *   Apstiprināšana / Izvēle — `Enter` vai `Atstarpe`.
    *   Atpakaļ / Iziet — `Escape`.

---

## ✨ Spēles funkcijas

*   **Adaptīva mērogošana:** Spēle sākotnēji izstrādāta bāzes izšķirtspējā `960x600`, taču tā automātiski pielāgojas un mērogo fiziskos elementus (hitboxes) uz `1280x720` ekrānu, saglabājot pareizas proporcijas un neatkarību no lietotāja ierīces ekrāna specifikācijas.
*   **Vizuālo tēlu (Skins) veikals:** Iespēja pielāgot sava tēla izskatu («Sun Runner», «Violet Dash», «Mint Shift»). Izvēlētais izskats tiek saglabāts vietējā konfigurācijas failā `settings.json` un paliek aktīvs arī nākamajās spēles reizēs.
*   **Lokālā līderu tabula (Leaderboard):** Pēc spēles pabeigšanas visi rezultāti tiek automātiski saglabāti SQLite datubāzē (`leaderboard.db`). Līderu tabula kārto spēlētājus pēc savākto monētu daudzuma, bet vienāda monētu skaita gadījumā — pēc labākā trases pabeigšanas laika.

---

## 📁 Projekta struktūra

```text
phase-shift/
├── requirements.txt        # Projekta atkarības (pygame)
├── README.md               # Projekta dokumentācija (Šis fails)
└── game/                   # Spēles galvenā mape
    ├── phase_shift.py      # Galvenais izpildāmais fails (Spēles sākumpunkts)
    ├── logic.py            # Lietotājvārdu pārbaude un rezultātu kārtošanas algoritmi
    ├── leaderboard.db      # Lokālā SQLite datubāze (tiek izveidota automātiski spēles mapē)
    ├── settings.json       # Spēlētāja iestatījumi un izvēlētais tēls (tiek izveidots automātiski spēles mapē)
    └── assets/             # Vizuālie tēli (sprites), fonti un skaņu efekti
```
