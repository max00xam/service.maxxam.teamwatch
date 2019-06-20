service.maxxam.teamwatch
========================

TeamWatch è un add-on Kodi che cambiarà il modo in cui guardi la TV,
la TV diventa 'social' consentendoti di commentare in diretta con i tuoi amici
quello che guardi in TV. TeamWatch ti permette anche di vedere
sullo schermo della TV tweets riguardando il programma che stai guardando!

Opzioni di configurazione
---------------------

- **Feed**: il feed che vuoi seguire separato da virgola.
- **TeamWatch ID**: identifica il tuo addon, consentendoti di inviargli messaggi attraverso la
pagina web. (devi tenerlo segreto)
- **Player control ID**: allows to send commands (play, pause, seek) to the player of all the addons that share the some id.

Invia messaggi e gestisci
-----------------------

Puoi inviare messaggi e comandi attraverso la pagina web www.teamwatch.it

Commandi
--------

``#tw:off`` - ferma la visualizzazione dei messaggi

``#tw:on`` - riprendi la visualizzazione dei messaggi

``#tw:playerctl:sshot`` - scatta uno screenshot

``#tw:bar:top`` - la barra verrà visualizzata in cima allo schermo

``#tw:bar:bottom`` - la barra verrà visualizzata in fondo allo schermo

``#tw[pc]:addfeed:<feed>`` - aggiunge un nuovo feed da seguire
  
``#tw[pc]:removefeed:<feed>`` - rimuove un feed dai feed seguiti
  
``#tw[pc]:playerctl:playpause`` - metti pausa/fai ripartire il video in riproduzione

``#tw[pc]:playerctl:stop`` - ferma la riproduzione del video

``#tw[pc]:rss:[on|off]`` - abilita/disabilita feed rss

``#tw[pc]:tweet:[on|off]`` - abilita/disabilita feed twitter

``#tw[pc]:playerctl:seek:<hh>:<mm>:<ss>:<cent>`` - manda il video corrente al tempo hh:mm:ss:cent
  
``#tw[pc]:playstream:<url>[&m_title=<title>`` - riproduci lo stream video dell' url

**url** può essere 'open stream' o wstream, backin, akvideo, openload, verystream, streamango

``#tw[pc]:playstream:<site>#<title>[#<streaming-site>, ...]`` - cerca titolo e guarda video

**site** può essere 'cb01' (italian language site) o 'olm' (english language site openload dot org)

**title** è una serie di parole di ricerca separate da spazio o da segno '+' (come 'hunger+games')

**stream-site** (optional) può essere wstream, backin, akvideo, openload, verystream, streamango

Se il comando è usato con "``#twpc:``" invece che "``#tw:``" il comando verrà inviato a tutti gli utenti che condividono alcuni "Player control ID" con te.
