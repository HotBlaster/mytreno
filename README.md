# ⚠️ Fork non ufficiale

Questo repository è un **fork** di [lotablet/mytreno](https://github.com/lotablet/mytreno), il cui progetto originale **non è più mantenuto** dall'autore.

Il fork nasce per mantenere l'integrazione funzionante con le versioni recenti di Home Assistant (es. 2026.10).

> **Nota:** la manutenzione è svolta **con l'aiuto dell'intelligenza artificiale**.
> Gli aggiornamenti potrebbero essere **lenti**.

Tutto il merito del progetto originale va a [@lotablet](https://github.com/lotablet). Se vuoi sostenere l'autore originale:

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/lotablet)

# ![icon](https://github.com/lotablet/mytreno/blob/main/custom_components/mytreno/images/icon.png) MyTreno  
<p align="center">
  <img src="https://github.com/lotablet/mytreno/blob/main/custom_components/mytreno/images/logo.png" alt="logo" />
</p>


**MyTreno** ti permette di monitorare in tempo reale **partenze e arrivi dei treni italiani** tramite il servizio **ViaggiaTreno** di Trenitalia, nella tua Lovelace!


Se nel componente manca la tua stazione preferita [SCRIVI QUI](https://github.com/lotablet/mytreno/issues/1)
---

## ✅ Funzionalità attuali

- Recupero automatico delle **partenze** e degli **arrivi** da qualsiasi stazione italiana
- Integrazione configurabile **via UI** da *Impostazioni → Integrazioni*
- Sensore aggiornato in tempo reale con treni in transito
- Card Lovelace pronta all’uso
- 🔥**Nuova Feature** - Tracking dei singoli treni nel popup 🔥

---

## 📦 Installazione tramite HACS

1. Vai in **HACS → Integrazioni**
2. Clicca su Menu **⋮ → Aggiungi repository personalizzato**
3. Inserisci questo URL e scegli tipo **"Integrazione"** :
```
https://github.com/HotBlaster/mytreno
```


4. Dopo aver aggiunto il repository, cerca “**MyTreno**” nell’elenco delle integrazioni HACS
5. Installa e riavvia Home Assistant

### 🔧 Configurazione

1. Vai su **Impostazioni → Dispositivi e Servizi**
2. Clicca su **"Aggiungi Integrazione"**
3. Cerca **MyTreno** e inserisci la città.

---

# 💡 Card Lovelace 



## MyTreno Card

![version](https://img.shields.io/badge/version-2.3.0-blue)
![hacs](https://img.shields.io/badge/HACS-custom-orange)

> Card Lovelace per visualizzare partenze e arrivi dei treni usando ViaggiaTreno.
> Repository: [HotBlaster/mytreno-card](https://github.com/HotBlaster/mytreno-card) (fork di [lotablet/mytreno-card](https://github.com/lotablet/mytreno-card))

## 📦 Installazione via HACS (Custom repositories)

1. Se hai già installato la *MyTreno Card* originale (lotablet), rimuovila: **HACS → MyTreno Card → ⋮ → Rimuovi**
2. Vai in **HACS → Menu ⋮ (in alto a destra) → Custom repositories** (*Archivi digitali personalizzati*)
3. Compila i campi:
   - **Repository:**
     ```
     https://github.com/HotBlaster/mytreno-card
     ```
   - **Tipo:** `Dashboard` (nelle versioni meno recenti di HACS: `Lovelace` / `Plugin`)
4. Clicca **Aggiungi**, poi cerca **MyTreno Card** in HACS e clicca **Scarica**
5. Ricarica la pagina del browser (svuota la cache se la card non compare)
6. Aggiungi la card nella dashboard (la trovi nella lista delle card)

La card richiede solo il sensore creato tramite l'integrazione:
```
type: custom:my-treno-card
sensor: sensor.mytreno_NOMECITTA
```
