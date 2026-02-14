# Senderliste Deutschland – Internetradio (MP3), inkl. SAW Musikwelt + Radio Bob.
# Synkron mit frontend RadioPlayer.tsx. Logos: Wikipedia 512px wo möglich.

RADIO_STATIONS = [
    # WDR
    {"id": "einslive", "name": "1Live", "stream_url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/WDR_1LIVE_Logo_2016.svg/512px-WDR_1LIVE_Logo_2016.svg.png", "region": "NRW", "genre": "Pop"},
    {"id": "wdr2", "name": "WDR 2", "stream_url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/WDR_2_Logo.svg/512px-WDR_2_Logo.svg.png", "region": "NRW", "genre": "Pop"},
    {"id": "wdr4", "name": "WDR 4", "stream_url": "https://wdr-wdr4-live.icecastssl.wdr.de/wdr/wdr4/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/WDR_4_logo_2012.svg/512px-WDR_4_logo_2012.svg.png", "region": "NRW", "genre": "Schlager"},
    {"id": "wdr5", "name": "WDR 5", "stream_url": "https://wdr-wdr5-live.icecastssl.wdr.de/wdr/wdr5/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/WDR_5_Logo.svg/512px-WDR_5_Logo.svg.png", "region": "NRW", "genre": "Kultur"},
    # NDR (Wikipedia NDR_Logo)
    {"id": "ndr2", "name": "NDR 2", "stream_url": "https://icecast.ndr.de/ndr/ndr2/niedersachsen/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/NDR_Logo.svg/512px-NDR_Logo.svg.png", "region": "Nord", "genre": "Pop"},
    {"id": "ndr1", "name": "NDR 1 Nds", "stream_url": "https://icecast.ndr.de/ndr/ndr1niedersachsen/hannover/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/NDR_Logo.svg/512px-NDR_Logo.svg.png", "region": "Nord", "genre": "Schlager"},
    # BR
    {"id": "bayern3", "name": "Bayern 3", "stream_url": "https://dispatcher.rndfnk.com/br/br3/live/mp3/mid", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Bayern3_Logo.svg/512px-Bayern3_Logo.svg.png", "region": "Bayern", "genre": "Pop"},
    {"id": "bayern1", "name": "Bayern 1", "stream_url": "https://dispatcher.rndfnk.com/br/br1/obb/mp3/mid", "logo_url": "https://api.ardmediathek.de/image-service/images/urn:ard:image:b366004f6196d70c?w=512", "region": "Bayern", "genre": "Schlager"},
    # DLF
    {"id": "dlf", "name": "Deutschlandfunk", "stream_url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Deutschlandfunk_logo.svg/512px-Deutschlandfunk_logo.svg.png", "region": "Bundesweit", "genre": "Info"},
    {"id": "dlfkultur", "name": "DLF Kultur", "stream_url": "https://st02.sslstream.dlf.de/dlf/02/128/mp3/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Deutschlandfunk_logo.svg/512px-Deutschlandfunk_logo.svg.png", "region": "Bundesweit", "genre": "Kultur"},
    # MDR
    {"id": "mdrjump", "name": "MDR Jump", "stream_url": "http://mdr-284320-0.cast.mdr.de/mdr/284320/0/mp3/high/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/MDR_Jump_Logo.svg/512px-MDR_Jump_Logo.svg.png", "region": "Mitte", "genre": "Pop"},
    {"id": "mdraktuell", "name": "MDR Aktuell", "stream_url": "http://mdr-284350-0.cast.mdr.de/mdr/284350/0/mp3/high/stream.mp3", "logo_url": "https://www.mdr.de/apple-touch-icon.png", "region": "Mitte", "genre": "Nachrichten"},
    # HR, SWR
    {"id": "hr3", "name": "HR3", "stream_url": "http://hr-hr3-live.cast.addradio.de/hr/hr3/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/HR3_Logo.svg/512px-HR3_Logo.svg.png", "region": "Hessen", "genre": "Pop"},
    {"id": "swr3", "name": "SWR3", "stream_url": "https://liveradio.swr.de/sw282p3/swr3/play.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/SWR3_Logo.svg/512px-SWR3_Logo.svg.png", "region": "Südwest", "genre": "Pop"},
    # Radio SAW + Musikwelt (https://www.radiosaw.de/musikwelt)
    {"id": "radiosaw", "name": "Radio SAW", "stream_url": "https://stream.radiosaw.de/saw/mp3-128/", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png", "region": "Sachsen-Anhalt", "genre": "Schlager"},
    {"id": "saw70er", "name": "SAW 70er", "stream_url": "https://stream.radiosaw.de/saw-70er/mp3-192/", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png", "region": "Sachsen-Anhalt", "genre": "70er"},
    {"id": "saw80er", "name": "SAW 80er", "stream_url": "https://stream.radiosaw.de/saw-80er/mp3-192/", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png", "region": "Sachsen-Anhalt", "genre": "80er"},
    {"id": "saw90er", "name": "SAW 90er", "stream_url": "https://stream.radiosaw.de/saw-90er/mp3-192/", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png", "region": "Sachsen-Anhalt", "genre": "90er"},
    {"id": "saw2000er", "name": "SAW 2000er", "stream_url": "https://stream.radiosaw.de/saw-2000er/mp3-192/", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png", "region": "Sachsen-Anhalt", "genre": "2000er"},
    {"id": "rockland", "name": "Rockland", "stream_url": "https://stream.radiosaw.de/rockland/mp3-192/", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png", "region": "Sachsen-Anhalt", "genre": "Rock"},
    {"id": "sawparty", "name": "SAW Party", "stream_url": "https://stream.radiosaw.de/saw-party/mp3-192/", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png", "region": "Sachsen-Anhalt", "genre": "Party"},
    {"id": "sawschlagerparty", "name": "SAW Schlagerparty", "stream_url": "https://stream.radiosaw.de/saw-schlagerparty/mp3-192/", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png", "region": "Sachsen-Anhalt", "genre": "Schlager"},
    # Weitere
    {"id": "antennebayern", "name": "Antenne Bayern", "stream_url": "https://antennebayern.cast.addradio.de/antennebayern/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Antenne_Bayern_Logo.svg/512px-Antenne_Bayern_Logo.svg.png", "region": "Bayern", "genre": "Pop"},
    {"id": "104.6rtl", "name": "104.6 RTL", "stream_url": "https://stream.104.6rtl.com/rtl", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/104.6_RTL_Logo.svg/512px-104.6_RTL_Logo.svg.png", "region": "Berlin", "genre": "Top 40"},
    {"id": "radioeins", "name": "radioeins", "stream_url": "http://rbb-radioeins-live.cast.addradio.de/rbb/radioeins/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Radio_Eins_Logo.svg/512px-Radio_Eins_Logo.svg.png", "region": "Berlin/Brandenburg", "genre": "Rock"},
    {"id": "bremenzwei", "name": "Bremen Zwei", "stream_url": "https://icecast.radiobremen.de/rb/bremenzwei/live/mp3/128/stream.mp3", "logo_url": "https://www.bremenzwei.de/static/img/favicons/apple-touch-icon-180.png", "region": "Bremen", "genre": "Kultur"},
    {"id": "rockantenne", "name": "Rock Antenne", "stream_url": "https://stream.rockantenne.de/rockantenne/stream/mp3", "logo_url": "https://www.rockantenne.de/logos/station-rock-antenne/apple-touch-icon.png", "region": "Bayern", "genre": "Rock"},
    {"id": "radiobob", "name": "Radio Bob", "stream_url": "https://streams.radiobob.de/bob-national/mp3-192/", "logo_url": "https://www.radiobob.de/favicon.ico", "region": "Bundesweit", "genre": "Rock"},
    {"id": "wdrcosmo", "name": "WDR Cosmo", "stream_url": "https://wdr-wdrcosmo-live.icecastssl.wdr.de/wdr/wdrcosmo/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/WDR_Cosmo_Logo.svg/512px-WDR_Cosmo_Logo.svg.png", "region": "NRW", "genre": "World"},
    {"id": "ndrkultur", "name": "NDR Kultur", "stream_url": "https://icecast.ndr.de/ndr/ndrkultur/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/NDR_Logo.svg/512px-NDR_Logo.svg.png", "region": "Nord", "genre": "Kultur"},
    {"id": "br2", "name": "BR-Klassik", "stream_url": "https://dispatcher.rndfnk.com/br/br2/live/mp3/mid", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Bayern_2_Logo.svg/512px-Bayern_2_Logo.svg.png", "region": "Bayern", "genre": "Klassik"},
    {"id": "swr1bw", "name": "SWR1 BW", "stream_url": "https://liveradio.swr.de/sw282p3/swr1bw/play.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/SWR1_Logo.svg/512px-SWR1_Logo.svg.png", "region": "Südwest", "genre": "Schlager"},
    {"id": "swr4", "name": "SWR4", "stream_url": "https://liveradio.swr.de/sw282p3/swr4bw/play.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/SWR4_Logo.svg/512px-SWR4_Logo.svg.png", "region": "Südwest", "genre": "Schlager"},
    {"id": "hr1", "name": "HR1", "stream_url": "http://hr-hr1-live.cast.addradio.de/hr/hr1/live/mp3/128/stream.mp3", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/HR1_Logo.svg/512px-HR1_Logo.svg.png", "region": "Hessen", "genre": "Schlager"},
    {"id": "rbb888", "name": "rbb 88.8", "stream_url": "http://rbb-888-live.cast.addradio.de/rbb/888/live/mp3/128/stream.mp3", "logo_url": "https://www.rbb88-8.de/apple-touch-icon.png", "region": "Berlin", "genre": "Info"},
    {"id": "energy", "name": "Energy", "stream_url": "https://stream.energy.de/energy.mp3", "logo_url": "https://www.energy.de/favicon.ico", "region": "Bundesweit", "genre": "Charts"},
]

# Name → Logo-URL für Sender ohne logo_url (z. B. aus Favoriten/API)
STATION_LOGO_FALLBACKS = {s["name"]: s.get("logo_url", "") for s in RADIO_STATIONS if s.get("logo_url")}
