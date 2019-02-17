git password 
8WORMODdHp1qJnMSxISM

Sto guardando un film (o lo seleziono un film dalla lista?**)
Mando l'invito con "titolo del film" e durata invite_time (ad esempio 1m) e invite_id
(possibilità di mandare l'invito a pcid, feed o broadcast)
Quando si riceve un invito se si accetta si risponde on (ok:invite_id)
Passati invite_time secondi invio a tutti quelli che hanno accettato il play

(**) aggiungere una voce al context menu?
     bisogna modificare service.py per ricevere i messaggi anche quando non
     si sta guardando un video...
     
"""                    
                elif param == "#tw:playerctl:info":
                    self._log('VideoPlayer.Title: %s' % xbmc.getInfoLabel("VideoPlayer.Title"))
                    self._log('VideoPlayer.TVShowTitle: %s' % xbmc.getInfoLabel("VideoPlayer.TVShowTitle"))
                    self._log('VideoPlayer.Tagline: %s' % xbmc.getInfoLabel("VideoPlayer.Tagline"))
                    self._log('VideoPlayer.ChannelName: %s' % xbmc.getInfoLabel("VideoPlayer.ChannelName"))
                    self.id_chat = jresult['id']
                elif param.startswith("#tw:playerctl:vl:"):
                    response = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "params": {"filter": {"operator": "is", "field": "title", "value": "%s"}, "properties": ["title", "setid", "file"]}, "method": "VideoLibrary.GetMovies", "id": "libMovies"}' % param[17:])
                    
                    try:
                        moviepath = json.loads(response)['result']['movies'][0]['file']
                        self.player.play(moviepath)

                    except:
                        self._log("error in json.loads")
                    
                    self.id_chat = jresult['id']
"""                    

=========================================================================================

TeamWatch is an addo-on for chatting with friends watching the TV

TeamWatch is a Kodi add-on that will change the way you watch TV, your TV becomes 'social' allowing you to comment live with 
friends what you see on the screen. TeamWatch also gives you the opportunity to display on the TV screen tweets regarding the 
program you are watching!

Just install the add-on, add the feeds you want to follow and start commenting the show via the web page at www.teamwatch.tk.

Setting in the config the same "Player control ID" with your friends is it possible to synch the video

=========================================================================================
TeamWatch è un add-on per Kodi che rivoluzionerà il tuo modo di guardare la TV,
la TV diventa 'social' permettendoti di commentare  in diretta con i tuoi amici
quello che vedete sullo schermo. Inoltre TeamWatch ti da la possibilità di
visualizzare sullo schermo della TV i tweet che riguardano il programma che stai
guardando!

Per iniziare a commentare quello che stai guardando basta installare l'add-on,
inserire i feeds che vuoi seguire e inviare messaggi dalla pagina www.teamwatch.tk, 
tutti gli utenti che seguono il feed riceveranno i messaggi che invii tramite la pagina.

TeamWatch permette anche di sincronizzare il video con i tuoi amici, potrete inviare 
i comandi play, pausa e vai all'inizio a tutti gli add-on che condividono lo stesso 
Player control ID.
=========================================================================================
L'addon si chiama TeamWatch, permette di impostare dei "feed" e ricevere in sovraimpressione 
al video che si sta guardando messaggi inviati dalla pagina www.teamwatch.tk a quei feeds 
oltre ad i tweet relativi agli stessi feeds (è possibilie disabilitare la ricezione dei tweet).

Inoltre da la possibilità di "sincronizzare" il video fra due o più mediacenter in modo da 
guardare un film insieme con gli amici e poter commentare "in diretta" (tutti devono avere 
lo stesso file o lo stesso file in streaming).

L'addon si può scaricare da https://github.com/…/service.maxxam.team…/archive/master.zip
=========================================================================================
[ilaria]
TeamWatch is an add-on for Kodi that will change your way to watch television; 
TV will become "social" allowing you to comment live with your friends what you are 
watching on the screen. Furthermore, TeamWatch allows you to see on the TV screen 
all tweets regarding the program you are watching.

[google]
It allows you to set the "feeds" you want to follow, and receive overlayed to
the video you are watching the messages sent to those feeds from www.teamwatch.tk
as well as the tweets related to the same feeds (tweets can be disabled).

In addition gives the opportunity to "synchronize" the video between two or more 
mediacenter so as to watch a movie together with friends and could not comment "live" 
(everyone must have the same video file or the same video streaming).
