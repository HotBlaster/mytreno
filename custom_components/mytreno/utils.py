import logging
from datetime import datetime, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo                      # Python 3.9+

import aiohttp
from yarl import URL

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import HTTP_HEADERS, REQUEST_TIMEOUT, URL_BASE

_LOGGER = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Fuso / conversioni tempo
# ─────────────────────────────────────────────────────────────────────────────
_TZ = ZoneInfo("Europe/Rome")          # cambia da solo CET↔CEST

def ms_to_local_iso(ms: int | None) -> str | None:
    """Epoch-ms → stringa ISO in fuso orario di Roma."""
    return (
        datetime.fromtimestamp(ms / 1000, _TZ).isoformat(timespec="seconds")
        if ms else None
    )

def _ms_to_iso_utc(ms):
    """Epoch-ms → ISO UTC (fallback vecchie funzioni)."""
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat() if ms else None


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers “storici” per tabellone partenze / arrivi
# ─────────────────────────────────────────────────────────────────────────────
_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

def build_timestamp() -> str:
    """Stringa timestamp che ViaggiaTreno vuole per partenza/arrivi."""
    now = datetime.now(_TZ)
    # English names regardless of system locale, e.g. "Tue Oct 27 2026 15:40:00 GMT+0100"
    return (
        f"{_DAYS[now.weekday()]} {_MONTHS[now.month - 1]} "
        f"{now:%d %Y %H:%M:%S} GMT{now:%z}"
    )

def roman_to_int(roman: str):
    """Converte numeri romani I-XX in arabi; se non trova ritorna l’originale."""
    roman_numerals = {
        "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
        "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13,
        "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19,
        "XX": 20,
    }
    return roman_numerals.get(roman, roman)


async def fetch_data(hass: HomeAssistant, station_id: str):
    """Partenze e arrivi di una stazione (tutti i treni disponibili dall'API)."""
    timestamp = quote(build_timestamp(), safe="")
    urls = {
        "partenze": f"{URL_BASE}/partenze/{station_id}/{timestamp}",
        "arrivi":   f"{URL_BASE}/arrivi/{station_id}/{timestamp}",
    }
    data    = {"partenze": [], "arrivi": []}
    session = async_get_clientsession(hass)

    for kind, url in urls.items():
        try:
            async with session.get(
                URL(url, encoded=True),
                headers=HTTP_HEADERS,
                timeout=REQUEST_TIMEOUT,
            ) as res:
                if res.status != 200:
                    body = (await res.text())[:200]
                    _LOGGER.warning(
                        "MyTreno %s %s: HTTP %s, body=%r", kind, station_id, res.status, body
                    )
                    continue
                trains_raw = await res.json(content_type=None)
                if not isinstance(trains_raw, list):
                    _LOGGER.warning(
                        "MyTreno %s %s: risposta inattesa (%s): %r",
                        kind, station_id, type(trains_raw).__name__, str(trains_raw)[:200],
                    )
                    continue
                _LOGGER.debug("MyTreno %s %s: %d treni da %s", kind, station_id, len(trains_raw), url)

                # chiavi diverse per arrivi/partenze
                bin_prog_key = (
                    "binarioProgrammatoPartenzaDescrizione"
                    if kind == "partenze"
                    else "binarioProgrammatoArrivoDescrizione"
                )
                bin_eff_key = (
                    "binarioEffettivoPartenzaDescrizione"
                    if kind == "partenze"
                    else "binarioEffettivoArrivoDescrizione"
                )

                for treno in trains_raw:
                    data[kind].append(
                        {
                            "treno": treno.get("compNumeroTreno", "??"),
                            "orario": treno.get(
                                "compOrarioPartenza"
                                if kind == "partenze"
                                else "compOrarioArrivo",
                                "??",
                            ),
                            (
                                "destinazione"
                                if kind == "partenze"
                                else "provenienza"
                            ): treno.get(
                                "destinazione" if kind == "partenze" else "origine", "??"
                            ),
                            "ritardo": treno.get("ritardo", "?"),
                            "binario_previsto": roman_to_int(
                                treno.get(bin_prog_key, "N/A")
                            ),
                            "binario_effettivo": roman_to_int(
                                treno.get(bin_eff_key, "N/A")
                            ),
                        }
                    )
        except Exception as err:
            raise UpdateFailed(f"Errore fetch {kind}: {err}") from err

    return data
# ─────────────────────────────────────────────────────────────────────────────
#  Tracking live del singolo treno selezionato
# ─────────────────────────────────────────────────────────────────────────────
async def _resolve_train(train_number: str, session: aiohttp.ClientSession):
    """/cercaNumeroTrenoTrenoAutocomplete → station_id + timestamp."""
    url = f"{URL_BASE}/cercaNumeroTrenoTrenoAutocomplete/{train_number}"
    async with session.get(url, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT) as res:
        txt = (await res.text()).strip()
        if res.status != 200 or not txt:
            raise UpdateFailed(f"Treno {train_number} non trovato (HTTP {res.status})")
    try:
        candidates = txt.split("|")[1:]
        for cand in reversed(candidates):  # prova dal più recente
            parts = cand.strip().split(" ")[0].split("-")
            if len(parts) == 3:
                _, station_id, ts = parts
                return station_id, ts
        raise ValueError(f"Nessun candidato valido trovato: {txt}")
    except Exception as err:
        raise UpdateFailed(f"Parsing autocomplete: {err} (raw='{txt}')") from err
    return station_id, ts
async def fetch_train_data(hass: HomeAssistant, train_number: str):
    """
    Ritorna dict:
      - ritardo, stato, ultima_stazione, ora_ultimo_rilevamento
      - prossima_stazione, orario_previsto_prossima
      - fermate[]   (lista di dict)
    """
    if not train_number:
        return {}

    session = async_get_clientsession(hass)

    # ── 1.  resolve per avere station_id + timestamp
    station_id, ts = await _resolve_train(train_number, session)

    # ── 2.  andamentoTreno (overview)
    url_andamento = f"{URL_BASE}/andamentoTreno/{station_id}/{train_number}/{ts}"
    # ── 3.  tratteCanvas   (tutte le fermate)
    url_tratte    = f"{URL_BASE}/tratteCanvas/{station_id}/{train_number}/{ts}"

    async with session.get(url_andamento, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT) as res_a, \
               session.get(url_tratte,    headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT) as res_t:
        if res_a.status != 200:
            raise UpdateFailed(f"Errore HTTP {res_a.status} su andamentoTreno")
        andamento = await res_a.json(content_type=None)
        if res_t.status != 200:
            raise UpdateFailed(f"Errore HTTP {res_t.status} su tratteCanvas")
        tratte_raw = await res_t.json(content_type=None)
        if not isinstance(tratte_raw, list):
            tratte_raw = []

    # ── riepilogo
    fermate = []
    prossima_stazione        = None
    orario_previsto_prossima = None

    for item in tratte_raw:
        f = item.get("fermata", {})
        arr_eff = f.get("arrivoReale")
        part_eff = f.get("partenzaReale")
        arrivato = bool(arr_eff or part_eff)

        orario_prev  = ms_to_local_iso(f.get("programmata"))
        orario_eff   = ms_to_local_iso(f.get("effettiva"))

        bin_eff = f.get("binarioEffettivoArrivoDescrizione") \
                  or f.get("binarioEffettivoPartenzaDescrizione")
        bin_prog = f.get("binarioProgrammatoArrivoDescrizione") \
                   or f.get("binarioProgrammatoPartenzaDescrizione")
        binario = roman_to_int(bin_eff or bin_prog)

        fermate.append(
            {
                "stazione": f.get("stazione", "--"),
                "programmata": orario_prev,
                "effettiva":   orario_eff,
                "ritardo": f.get("ritardo", 0),
                "arrivato": arrivato,
                "binario": binario,
            }
        )
        if not arrivato and not prossima_stazione:
            prossima_stazione        = f.get("stazione")
            orario_previsto_prossima = orario_prev

    # “stato” → prima lingua ITA
    stato_raw = andamento.get("compRitardoAndamento", [])
    stato     = stato_raw[0] if isinstance(stato_raw, list) else stato_raw

    return {
        "train_number":             train_number,
        "ritardo":                  andamento.get("ritardo", 0),
        "stato":                    stato,
        "ultima_stazione":          andamento.get("stazioneUltimoRilevamento", "--"),
        "ora_ultimo_rilevamento":   ms_to_local_iso(andamento.get("oraUltimoRilevamento")),
        "prossima_stazione":        prossima_stazione,
        "orario_previsto_prossima": orario_previsto_prossima,
        "fermate":                  fermate,
    }
