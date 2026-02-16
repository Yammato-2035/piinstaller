# Stream-URLs Energy, radioeins, rbb 88.8 (radio-browser.info Abgleich)

Abgleich mit der Radio-Browser-API (de1.api.radio-browser.info), um gültige URLs und Qualität (Codec/Bitrate) für die Sender zu sichern, die bei uns keinen Ton lieferten.

---

## Energy

| | Unsere URL (vorher) | Radio-Browser-API |
|--|---------------------|--------------------|
| **URL** | `https://frontend.streamonkey.net/energy-berlin/stream/mp3` | „Energy Berlin“ gibt es in der API als **Radio Energy Berlin** mit `http://nrj.de/berlin` → Codec **AAC**, Bitrate 0. |
| **Problem** | `energy-berlin` liefert bei uns keinen Ton; die API listet **keine** MP3-URL für „Energy Berlin“. Viele andere Energy-Streams sind **MP3 128** und `lastcheckok: 1`. |
| **Empfohlene URL** | – | **https://edge62.streamonkey.net/energy-digital/stream/mp3** („Energy - Hit Music Only!“ / „Energy Hit Music Only!“) – **MP3, 128 kbps**, lastcheckok 1. |

**Qualität laut API**: MP3 128 kbps (für energy-digital); „Radio Energy Berlin“ (nrj.de/berlin) = AAC.

---

## radioeins

| | Unsere URL (vorher) | Radio-Browser-API |
|--|---------------------|--------------------|
| **URL** | `http://rbb-radioeins-live.cast.addradio.de/rbb/radioeins/live/mp3/128/stream.mp3` | Einträge mit **dispatcher.rndfnk.com**; `url_resolved` sind **rndfnk.com**-Streams **mit Token** (cid, sid, token) in der Query. |
| **Problem** | addradio-URL könnte veraltet sein oder anders weitergeleitet werden; die API nutzt **dispatcher.rndfnk.com** als Einstieg, der auf tokenisierte rndfnk.com-Streams umleitet. |
| **Empfohlene URL** | – | **https://dispatcher.rndfnk.com/rbb/radioeins/live/mp3/mid** (bzw. bei Bedarf Qualität anpassen) – Einstieg wie in der API; Redirect liefert MP3 128. |

**Qualität laut API**: MP3 128 kbps (alle getesteten radioeins-Einträge).

---

## rbb 88.8

| | Unsere URL (vorher) | Radio-Browser-API |
|--|---------------------|--------------------|
| **URL** | `https://dispatcher.rndfnk.com/rbb/rbb888/live/mp3/mid` | „RBB 88.8“ / „RBB 88.8 Radio Berlin“ – **url** und **url_resolved** in der API teils **http** (nicht https): `http://dispatcher.rndfnk.com/rbb/rbb888/live/mp3/mid`. |
| **Problem** | Möglicherweise erwartet der Server HTTP oder verhält sich bei HTTPS anders (Redirect/Token). |
| **Empfohlene URL** | – | **http://dispatcher.rndfnk.com/rbb/rbb888/live/mp3/mid** (wie in der API). |

**Qualität laut API**: MP3 128 kbps, lastcheckok 1.

---

## Umgesetzte Anpassungen im Projekt

- **Energy**: URL in `stations.py` und ggf. QML-Fallback auf **https://edge62.streamonkey.net/energy-digital/stream/mp3** (MP3 128).
- **radioeins**: URL auf **https://dispatcher.rndfnk.com/rbb/radioeins/live/mp3/mid** umgestellt (Dispatcher statt addradio).
- **rbb 88.8**: URL auf **http://dispatcher.rndfnk.com/rbb/rbb888/live/mp3/mid** umgestellt (HTTP wie in der API).

Referenz: **https://de1.api.radio-browser.info** (Stations-Suche nach Name/Country); Felder `url`, `url_resolved`, `codec`, `bitrate`, `lastcheckok`.
