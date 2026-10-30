"""English/French presentation only; never translates protocol commands or private file contents."""
import re
_language = "en"

FR = {' bytes': ' octets',
 ' bytes · Format verified': ' octets  ·  Format vérifié',
 ' checked tags': ' amiibo cochés',
 ' duplicates skipped': ' doublon(s) ignoré(s)',
 ' files rejected': ' fichier(s) refusé(s)',
 ' imported · ': ' importé(s) · ',
 ' in your library': ' dans la bibliothèque',
 ' public entries cached. Your library remains available offline.': ' entrées publiques mises en cache. La '
                                                                    'bibliothèque reste utilisable hors '
                                                                    'ligne.',
 ' read back': ' relus',
 ' sent': ' transmis',
 ' shown · ': ' affiché(s) · ',
 ' stored tags · active #': ' amiibo enregistrés · actif n°',
 ' tags': ' amiibo',
 ' tags verified; first tag active, ejected.': ' amiibo vérifiés ; premier amiibo actif, retiré.',
 ' verified': ' vérifiés',
 ' · Presented: ': ' · Présenté : ',
 '. Sources are available online. These entries do not represent hardware tests of every figure.': '. Les '
                                                                                                   'sources '
                                                                                                   'restent '
                                                                                                   'consultables '
                                                                                                   'en '
                                                                                                   'ligne. '
                                                                                                   'Ces '
                                                                                                   'fiches '
                                                                                                   'ne sont '
                                                                                                   'pas des '
                                                                                                   'résultats '
                                                                                                   'de tests '
                                                                                                   'sur '
                                                                                                   'chaque '
                                                                                                   'figurine.',
 '0.2.0 preview: checked playlists and five-second cycling; physical qualification pending.': 'Aperçu 0.2.0 '
                                                                                              ': listes '
                                                                                              'cochées et '
                                                                                              'changement '
                                                                                              'par appui de '
                                                                                              'cinq secondes '
                                                                                              '; essai '
                                                                                              'physique à '
                                                                                              'effectuer.',
 '1 · Choose your Pico and amiibo': '1 · Choisir le Pico et l’amiibo',
 '1. Connect the Pico to the PC using a USB data cable.\n2. After startup, hold BOOTSEL for 2 seconds and release.\n3. The LED flashes quickly and the configuration port appears.\n\nHolding BOOTSEL before connecting opens RPI-RP2 for firmware recovery. It is not the amiibo import channel.': '1. '
                                                                                                                                                                                                                                                                                                    'Branche '
                                                                                                                                                                                                                                                                                                    'le '
                                                                                                                                                                                                                                                                                                    'Pico '
                                                                                                                                                                                                                                                                                                    'au '
                                                                                                                                                                                                                                                                                                    'PC '
                                                                                                                                                                                                                                                                                                    'avec '
                                                                                                                                                                                                                                                                                                    'un '
                                                                                                                                                                                                                                                                                                    'câble '
                                                                                                                                                                                                                                                                                                    'USB '
                                                                                                                                                                                                                                                                                                    'de '
                                                                                                                                                                                                                                                                                                    'données.\n'
                                                                                                                                                                                                                                                                                                    '2. '
                                                                                                                                                                                                                                                                                                    'Après '
                                                                                                                                                                                                                                                                                                    'le '
                                                                                                                                                                                                                                                                                                    'démarrage, '
                                                                                                                                                                                                                                                                                                    'maintiens '
                                                                                                                                                                                                                                                                                                    'BOOTSEL '
                                                                                                                                                                                                                                                                                                    'pendant '
                                                                                                                                                                                                                                                                                                    '2 '
                                                                                                                                                                                                                                                                                                    'secondes '
                                                                                                                                                                                                                                                                                                    'et '
                                                                                                                                                                                                                                                                                                    'relâche.\n'
                                                                                                                                                                                                                                                                                                    '3. '
                                                                                                                                                                                                                                                                                                    'La '
                                                                                                                                                                                                                                                                                                    'LED '
                                                                                                                                                                                                                                                                                                    'clignote '
                                                                                                                                                                                                                                                                                                    'rapidement '
                                                                                                                                                                                                                                                                                                    'et '
                                                                                                                                                                                                                                                                                                    'le '
                                                                                                                                                                                                                                                                                                    'port '
                                                                                                                                                                                                                                                                                                    'de '
                                                                                                                                                                                                                                                                                                    'configuration '
                                                                                                                                                                                                                                                                                                    'apparaît.\n'
                                                                                                                                                                                                                                                                                                    '\n'
                                                                                                                                                                                                                                                                                                    'Maintenir '
                                                                                                                                                                                                                                                                                                    'BOOTSEL '
                                                                                                                                                                                                                                                                                                    'avant '
                                                                                                                                                                                                                                                                                                    'le '
                                                                                                                                                                                                                                                                                                    'branchement '
                                                                                                                                                                                                                                                                                                    'ouvre '
                                                                                                                                                                                                                                                                                                    'RPI-RP2, '
                                                                                                                                                                                                                                                                                                    'qui '
                                                                                                                                                                                                                                                                                                    'sert '
                                                                                                                                                                                                                                                                                                    'au '
                                                                                                                                                                                                                                                                                                    'firmware '
                                                                                                                                                                                                                                                                                                    'et '
                                                                                                                                                                                                                                                                                                    'non '
                                                                                                                                                                                                                                                                                                    'au '
                                                                                                                                                                                                                                                                                                    'chargement '
                                                                                                                                                                                                                                                                                                    'des '
                                                                                                                                                                                                                                                                                                    'amiibo.',
 '2 · Save and read back': '2 · Enregistrer et relire',
 '8-Bit Link': 'Link 8 bits',
 'A compatible controller is present. Hold BOOTSEL on your Pico for 2 seconds to expose its loading port.': 'Une '
                                                                                                            'manette '
                                                                                                            'compatible '
                                                                                                            'est '
                                                                                                            'présente. '
                                                                                                            'Maintiens '
                                                                                                            'BOOTSEL '
                                                                                                            '2 '
                                                                                                            'secondes '
                                                                                                            'sur '
                                                                                                            'ton '
                                                                                                            'Pico '
                                                                                                            'pour '
                                                                                                            'faire '
                                                                                                            'apparaître '
                                                                                                            'son '
                                                                                                            'port '
                                                                                                            'de '
                                                                                                            'chargement.',
 'A verified transfer does not confirm recognition in the game.': 'Un transfert ne vaut pas une '
                                                                  'reconnaissance dans le jeu.',
 'Add to favorites': 'Ajouter aux favoris',
 'After a verified readback, the guide helps you connect the Pico to your console. You must confirm the result in the game.': 'Après '
                                                                                                                              'une '
                                                                                                                              'relecture '
                                                                                                                              'réussie, '
                                                                                                                              'l’assistant '
                                                                                                                              't’accompagne '
                                                                                                                              'pour '
                                                                                                                              'connecter '
                                                                                                                              'le '
                                                                                                                              'Pico '
                                                                                                                              'à '
                                                                                                                              'la '
                                                                                                                              'console. '
                                                                                                                              'Le '
                                                                                                                              'résultat '
                                                                                                                              'dans '
                                                                                                                              'le '
                                                                                                                              'jeu '
                                                                                                                              'reste '
                                                                                                                              'à '
                                                                                                                              'confirmer '
                                                                                                                              'par '
                                                                                                                              'toi.',
 'All series': 'Toutes les séries',
 'Amiibo files (*.bin)': 'Fichiers amiibo (*.bin)',
 'Amiibo on the Pico': 'Amiibo sur le Pico',
 'Amiibo rewards · Tears of the Kingdom': 'Récompenses amiibo · Tears of the Kingdom',
 'Ancient Blade · Ancient Sheikah Fabric': 'Lame ancestrale · tissu sheikah',
 'Another short tap removes the tag. A two-second hold opens PC configuration.': 'Un autre appui bref retire '
                                                                                 'le tag. Deux secondes '
                                                                                 'ouvrent la configuration '
                                                                                 'PC.',
 'Application:': 'Application :',
 'Application: ': 'Application : ',
 'Artificial test Link': 'Test artificiel Link',
 'Awakening armor · Egg Fabric': 'Tenue de l’Éveil · tissu œuf',
 'BOOTSEL / RPI-RP2 mode': 'Mode BOOTSEL / RPI-RP2',
 'BOOTSEL cannot send A on this version. Use your regular controller to confirm.': 'BOOTSEL ne sait pas '
                                                                                   'envoyer A sur cette '
                                                                                   'version. Utilise ta '
                                                                                   'manette habituelle pour '
                                                                                   'valider.',
 'Before you start': 'Avant de commencer',
 'Bokoblin Fabric · Boko equipment': 'Tissu bokoblin · équipement boko',
 'Bonus materials': 'Bonus de matériaux',
 'Bows · Ancient Blade · Tunic of Memories Fabric': 'Arcs · lame ancestrale · tissu des souvenirs',
 'Cancel operation': 'Annuler l’opération',
 'Cancellation requested. Read the Pico again if verification does not finish.': 'Interruption demandée. Le '
                                                                                 'contenu du Pico devra être '
                                                                                 'relu si la vérification ne '
                                                                                 'se termine pas.',
 'Cannot open': 'Ouverture impossible',
 'Cannot open local PicoAmiibo Manager data. Check the permissions of your user data folder.': 'Impossible '
                                                                                               'd’ouvrir les '
                                                                                               'données '
                                                                                               'locales de '
                                                                                               'PicoAmiibo '
                                                                                               'Manager. '
                                                                                               'Vérifie les '
                                                                                               'autorisations '
                                                                                               'de ton '
                                                                                               'dossier de '
                                                                                               'données.',
 'Cannot write this log. Choose a writable folder.': 'Impossible d’écrire ce journal. Choisis un dossier '
                                                     'accessible.',
 'Catalog too large': 'Catalogue trop volumineux',
 'Catalog unavailable': 'Catalogue indisponible',
 'Champion Leathers Fabric · mushrooms': 'Tissu de la tunique de Link · champignons',
 'Check for playlist': 'Cocher pour la liste',
 'Checked amiibo playlist': 'Liste des amiibo cochés',
 'Checked order': 'Ordre des amiibo cochés',
 'Checking communication…': 'Vérification de la communication…',
 'Checking playlist capability': 'Vérification de la capacité multi-amiibo',
 'Choose an amiibo': 'Choisir un amiibo',
 'Choose the correct Pico port on the Load page.': 'Choisis le port du bon Pico dans la page Charger.',
 'Choose what to load': 'Choisir le chargement',
 'Clear checked': 'Tout décocher',
 'Close': 'Fermer',
 'Common drop pool': 'Tirage courant',
 'Common materials': 'Matériaux ordinaires',
 'Comparing data': 'Comparaison des données',
 'Complete Great Sky Island': 'Terminer l’île',
 'Connect it to your Switch 2 dock using a USB data cable.': 'Branche-le en USB de données au dock de la '
                                                             'Switch 2.',
 'Connect your Pico': 'Connecter le Pico',
 'Connect your Pico to the PC using a USB data cable, then hold BOOTSEL for two seconds after startup.': 'Branche '
                                                                                                         'ton '
                                                                                                         'Pico '
                                                                                                         'au '
                                                                                                         'PC '
                                                                                                         'avec '
                                                                                                         'un '
                                                                                                         'câble '
                                                                                                         'USB '
                                                                                                         'de '
                                                                                                         'données, '
                                                                                                         'puis '
                                                                                                         'maintiens '
                                                                                                         'BOOTSEL '
                                                                                                         'deux '
                                                                                                         'secondes '
                                                                                                         'après '
                                                                                                         'son '
                                                                                                         'démarrage.',
 'Connect your Pico to the PC with a USB data cable.': 'Branche ton Pico au PC avec un câble USB de données.',
 'Connection and protocol': 'Connexion et protocole',
 'Continue to Switch 2': 'Continuer vers la Switch 2',
 'Controller mode · unidentified': 'Mode manette · à identifier',
 'Corrupted': 'Corrompu',
 'Data comparison failed. The load is not verified; reconnect the Pico and retry using the original file.': 'La '
                                                                                                            'comparaison '
                                                                                                            'des '
                                                                                                            'données '
                                                                                                            'a '
                                                                                                            'échoué. '
                                                                                                            'Le '
                                                                                                            'chargement '
                                                                                                            "n'est "
                                                                                                            'pas '
                                                                                                            'validé '
                                                                                                            '; '
                                                                                                            'reconnecte '
                                                                                                            'le '
                                                                                                            'Pico '
                                                                                                            'puis '
                                                                                                            'réessaie '
                                                                                                            'avec '
                                                                                                            "l'original.",
 'Detailed item pools. ✨ = pristine weapon. Numbers are <b>relative weights within a table</b>, not per-scan drop chances.': 'Liste '
                                                                                                                             'détaillée '
                                                                                                                             ': '
                                                                                                                             'noms '
                                                                                                                             'anglais '
                                                                                                                             'des '
                                                                                                                             'objets '
                                                                                                                             'conservés '
                                                                                                                             'pour '
                                                                                                                             'éviter '
                                                                                                                             'des '
                                                                                                                             'traductions '
                                                                                                                             'ambiguës. '
                                                                                                                             '✨ '
                                                                                                                             '= '
                                                                                                                             'arme '
                                                                                                                             'intacte. '
                                                                                                                             'Les '
                                                                                                                             'nombres '
                                                                                                                             'sont '
                                                                                                                             'des '
                                                                                                                             '<b>poids '
                                                                                                                             'relatifs '
                                                                                                                             'dans '
                                                                                                                             'une '
                                                                                                                             'table</b>, '
                                                                                                                             'pas '
                                                                                                                             'des '
                                                                                                                             'chances '
                                                                                                                             'de '
                                                                                                                             'recevoir '
                                                                                                                             'l’objet '
                                                                                                                             'à '
                                                                                                                             'chaque '
                                                                                                                             'scan.',
 'Diagnostics': 'Diagnostic',
 'Diagnostics and settings': 'Diagnostic et paramètres',
 'Disconnect the Pico from the PC. It cannot be connected to two USB hosts.': 'Débranche le Pico du PC. Il '
                                                                              'ne peut pas rester connecté à '
                                                                              'deux hôtes.',
 'Documented fallback for other amiibo; an unlisted identifier does not confirm authenticity or an exclusive reward.': 'Profil '
                                                                                                                       'de '
                                                                                                                       'repli '
                                                                                                                       'documenté '
                                                                                                                       'pour '
                                                                                                                       'les '
                                                                                                                       'autres '
                                                                                                                       'amiibo '
                                                                                                                       '; '
                                                                                                                       'l’identifiant '
                                                                                                                       'non '
                                                                                                                       'répertorié '
                                                                                                                       'ne '
                                                                                                                       'confirme '
                                                                                                                       'ni '
                                                                                                                       'l’authenticité '
                                                                                                                       'ni '
                                                                                                                       'une '
                                                                                                                       'récompense '
                                                                                                                       'exclusive.',
 'Documented internal table; no released figure is automatically assigned to this profile.': 'Table interne '
                                                                                             'documentée ; '
                                                                                             'aucune '
                                                                                             'figurine '
                                                                                             'distribuée ne '
                                                                                             'lui est '
                                                                                             'attribuée '
                                                                                             'automatiquement '
                                                                                             'ici.',
 'Dusk Bow · Princess of Twilight Fabric': 'Arc du Crépuscule · tissu de la princesse du Crépuscule',
 'Dusk Claymore · Demon King Fabric': 'Épée du Crépuscule · tissu du roi démon',
 'Enable online metadata and artwork (optional)': 'Activer les métadonnées et illustrations en ligne '
                                                  '(facultatif)',
 'Epona': 'Épona',
 'Epona · Twilight armor · Mirror of Twilight Fabric': 'Épona · tenue du Crépuscule · tissu du miroir',
 'Epona: a special first-scan case in a location where horses can appear. Later scans do not guarantee another horse. The Manager cannot read game progress or scan history.': 'Épona '
                                                                                                                                                                               ': '
                                                                                                                                                                               'cas '
                                                                                                                                                                               'spécial '
                                                                                                                                                                               'du '
                                                                                                                                                                               'premier '
                                                                                                                                                                               'scan '
                                                                                                                                                                               'd’un '
                                                                                                                                                                               'tag, '
                                                                                                                                                                               'dans '
                                                                                                                                                                               'une '
                                                                                                                                                                               'zone '
                                                                                                                                                                               'où '
                                                                                                                                                                               'les '
                                                                                                                                                                               'chevaux '
                                                                                                                                                                               'peuvent '
                                                                                                                                                                               'apparaître. '
                                                                                                                                                                               'Les '
                                                                                                                                                                               'scans '
                                                                                                                                                                               'suivants '
                                                                                                                                                                               'ne '
                                                                                                                                                                               'promettent '
                                                                                                                                                                               'pas '
                                                                                                                                                                               'un '
                                                                                                                                                                               'nouveau '
                                                                                                                                                                               'cheval. '
                                                                                                                                                                               'Le '
                                                                                                                                                                               'Manager '
                                                                                                                                                                               'ne '
                                                                                                                                                                               'lit '
                                                                                                                                                                               'pas '
                                                                                                                                                                               'la '
                                                                                                                                                                               'progression '
                                                                                                                                                                               'ni '
                                                                                                                                                                               'l’historique '
                                                                                                                                                                               'du '
                                                                                                                                                                               'jeu.',
 'Explore all TOTK rewards': 'Explorer toutes les récompenses TOTK',
 'Export diagnostics': 'Exporter le diagnostic',
 'Export failed': 'Export impossible',
 'Export log': 'Exporter le journal',
 'FIRMWARE GUIDE · ': 'GUIDE FIRMWARE · ',
 'Failed · reported': 'Échec · déclaré',
 'Favorites': 'Favoris',
 'Fierce Deity armor and sword · Majora Mask Fabric': 'Tenue du Dieu démon · épée du Dieu démon · tissu '
                                                      'Majora',
 'Files rejected': 'Fichiers refusés',
 'Find the Pico': 'Rechercher le Pico',
 'Firmware capability': 'Capacité du firmware',
 'Fish · Soldier and Knight weapons': 'Poissons · armes de soldat et de chevalier',
 'Format and BCC verified. Amiibo authenticity must be tested in the game.': 'Format et BCC vérifiés. '
                                                                             "L'authenticité amiibo doit "
                                                                             'être testée dans le jeu.',
 'Format verified': 'Format vérifié',
 'From PC to Switch 2': 'Du PC à la Switch 2',
 'Game': 'Jeu',
 'Gems · Hyrule-Princess Fabric': 'Gemmes · tissu de la princesse hylienne',
 'Generation:': 'Génération :',
 'Generation: ': 'Génération : ',
 'Generic Link · internal table': 'Link générique · table interne',
 'Generic Zelda · internal table': 'Zelda générique · table interne',
 'Gerudo-King Fabric · Gloom Sword': 'Tissu du roi gerudo · sabre miasmatique',
 'Goddess Fabric · gems': 'Tissu de la déesse · gemmes',
 'Guardian · BOTW': 'Gardien · BOTW',
 'Guide version: unknown': 'Version du guide : inconnue',
 'Hero Shield · Bygone-Royal Fabric': 'Bouclier du Héros · tissu de l’ancienne famille royale',
 'Hero armor and sword · Pixel Fabric': 'Tenue du Prélude · épée du Héros · tissu pixel',
 'Hold BOOTSEL for five seconds to select the next tag, wrapping to the first. The new tag stays ejected.': 'Maintiens '
                                                                                                            'BOOTSEL '
                                                                                                            'cinq '
                                                                                                            'secondes '
                                                                                                            'pour '
                                                                                                            'sélectionner '
                                                                                                            'le '
                                                                                                            'suivant, '
                                                                                                            'puis '
                                                                                                            'revenir '
                                                                                                            'au '
                                                                                                            'premier '
                                                                                                            'en '
                                                                                                            'fin '
                                                                                                            'de '
                                                                                                            'liste. '
                                                                                                            'Le '
                                                                                                            'nouveau '
                                                                                                            'tag '
                                                                                                            'reste '
                                                                                                            'retiré.',
 'Hold BOOTSEL for two seconds to enter configuration mode.': 'Passe ton Pico en configuration avec BOOTSEL '
                                                              'pendant deux secondes.',
 'Home': 'Accueil',
 'How to connect your Pico': 'Comment connecter mon Pico',
 'Identical readback': 'Relecture identique',
 'Identical readback · ': 'Relecture identique · ',
 'Identifying the Pico': 'Identification du Pico',
 'If scanning fails': 'Si le scan n’aboutit pas',
 'If the console asks for A, quickly tap BOOTSEL twice.': 'Si la console demande A : deux appuis brefs '
                                                          'rapides sur BOOTSEL.',
 'Import': 'Importer',
 'Import an amiibo into your library': 'Importe un amiibo dans la bibliothèque',
 'Import files': 'Importer des fichiers',
 'Import your amiibo': 'Importer mes amiibo',
 'In TOTK, Wolf Link provides meat and a fabric; it does not summon the wolf companion from BOTW.': 'Dans '
                                                                                                    'TOTK, '
                                                                                                    'Link '
                                                                                                    'loup '
                                                                                                    'fournit '
                                                                                                    'des '
                                                                                                    'viandes '
                                                                                                    'et un '
                                                                                                    'tissu ; '
                                                                                                    'il ne '
                                                                                                    'fait '
                                                                                                    'pas '
                                                                                                    'apparaître '
                                                                                                    'le '
                                                                                                    'compagnon '
                                                                                                    'loup de '
                                                                                                    'BOTW.',
 'In controller mode, release BOOTSEL after 2 seconds and before 5 seconds to open configuration.': 'En mode '
                                                                                                    'manette, '
                                                                                                    'relâche '
                                                                                                    'BOOTSEL '
                                                                                                    'après 2 '
                                                                                                    'secondes '
                                                                                                    'et '
                                                                                                    'avant 5 '
                                                                                                    'secondes '
                                                                                                    'pour '
                                                                                                    'ouvrir '
                                                                                                    'la '
                                                                                                    'configuration.',
 'In your library': 'Dans ta bibliothèque',
 'Inconsistent Pico state': 'État du Pico incohérent',
 'Inconsistent readback CRC': 'CRC de relecture incohérent',
 'Inconsistent readback size': 'Taille de relecture incohérente',
 'Invalid': 'Invalide',
 'Invalid public image': 'Image publique non valide',
 'Invalid size or structure, or inaccessible file:': 'Taille ou structure invalide, ou fichier inaccessible '
                                                     ':',
 'JSON log (*.json)': 'Journal JSON (*.json)',
 'JordanBTucker · datamined drop tables': 'JordanBTucker · tables extraites du jeu',
 'Keep the Pico connected during this operation.': 'Ne débranche pas le Pico pendant cette opération.',
 'Language': 'Langue',
 'Last verification': 'Dernière vérification',
 'Library': 'Bibliothèque',
 'Link Archer · BOTW': 'Link archer · BOTW',
 'Link Rider · BOTW': 'Link cavalier · BOTW',
 'Load': 'Charger',
 'Load an amiibo and verify its readback before connecting to the console.': 'Charge un amiibo et vérifie sa '
                                                                             'relecture avant de passer sur '
                                                                             'la console.',
 'Load and verify': 'Charger et vérifier',
 'Load checked playlist': 'Charger la liste cochée',
 'Load checked tags': 'Charger les amiibo cochés',
 'Load history': 'Historique des chargements',
 'Load not verified': 'Chargement non vérifié',
 'Load onto the Pico': 'Charger sur le Pico',
 'Load selection': 'Charger la sélection',
 'Load your Pico here. Continue on your Switch 2.': 'Charge ton Pico ici. La suite se passe sur ta Switch 2.',
 'Loading playlist': 'Chargement de la liste',
 'Local USB · one active tag': 'USB local · un seul tag actif',
 'Local USB · one active tag\nNo account required': 'USB local · un amiibo actif\nAucun compte nécessaire',
 'Local USB · one tag\nNo account required': 'USB local · un seul tag\nAucun compte nécessaire',
 'Local catalog': 'Catalogue local',
 'Local file': 'Fichier local',
 'Loftwing': 'Célestrier',
 'Looking for your Pico…': 'Recherche du Pico…',
 'Manual reference: the figure ID is absent from the public catalog used here. A compatible game version is required.': 'Fiche '
                                                                                                                        'consultable '
                                                                                                                        'manuellement '
                                                                                                                        ': '
                                                                                                                        'identifiant '
                                                                                                                        'de '
                                                                                                                        'figurine '
                                                                                                                        'absent '
                                                                                                                        'du '
                                                                                                                        'catalogue '
                                                                                                                        'public '
                                                                                                                        'utilisé '
                                                                                                                        '; '
                                                                                                                        'aucune '
                                                                                                                        'identification '
                                                                                                                        'automatique '
                                                                                                                        'inventée. '
                                                                                                                        'Version '
                                                                                                                        'du '
                                                                                                                        'jeu '
                                                                                                                        'compatible '
                                                                                                                        'requise.',
 'Materials and food · no exclusive Zelda rewards': 'Matériaux et nourriture · aucune récompense Zelda '
                                                    'exclusive',
 'Maximum 64 tags; reduce the checked selection.': 'Maximum 64 amiibo ; réduis la sélection cochée.',
 'Meat · Mirror of Twilight Fabric (no wolf companion)': 'Viandes · tissu du miroir du Crépuscule (aucun '
                                                         'compagnon loup)',
 'Mineru Construct · TOTK': 'Golem de Mineru · TOTK',
 'Mode: ': 'Mode : ',
 'Multi-slot firmware 0.2.0 is required for multiple tags.': 'Le firmware multi-amiibo 0.2.0 est nécessaire '
                                                             'pour plusieurs amiibo.',
 'Multiple Pico devices detected': 'Plusieurs Pico détectés',
 'Mushrooms · swords · Hylian-Hood Fabric': 'Champignons · épées · tissu de la capuche hylienne',
 'My tag': 'Mon tag',
 'Next step': 'Étape suivante',
 'Nintendo · using amiibo in TOTK': 'Nintendo · utilisation des amiibo dans TOTK',
 'No Pico in configuration mode': 'Aucun Pico en configuration',
 'No amiibo imported': 'Aucun amiibo importé',
 'No device detected.': 'Aucun périphérique détecté.',
 'No entries': 'Aucune fiche',
 'No entries match your search.': 'Aucune fiche ne correspond à cette recherche.',
 'No game result reported.': 'Aucun résultat de jeu déclaré.',
 'No stored tag': 'Aucun amiibo enregistré',
 'None yet': 'Aucune pour le moment',
 'Not confirmed': 'Non confirmé',
 'Not verified': 'Non vérifié',
 'Offline reference · reviewed on ': 'Référence consultable hors ligne · vérifiée le ',
 'On 0.1.1 only': 'Sur 0.1.1 uniquement',
 'On 0.1.1 only, holding for about one second sends L+R. This gesture is absent from 0.1.2.': 'Sur 0.1.1 '
                                                                                              'uniquement, '
                                                                                              'un maintien '
                                                                                              "d'environ une "
                                                                                              'seconde émet '
                                                                                              'L+R. Ce geste '
                                                                                              'est absent de '
                                                                                              '0.1.2.',
 'One active tag at a time. Hold 5 seconds to advance; short tap to present.': 'Un amiibo actif à la fois. '
                                                                               'Maintiens 5 secondes pour '
                                                                               'passer au suivant ; appui '
                                                                               'court pour présenter.',
 'One amiibo. One click.': 'Un amiibo, un clic.',
 'Only a public catalog and public images are downloaded. Amiibo files are never uploaded. Cached images remain available offline.': 'Seuls '
                                                                                                                                     'un '
                                                                                                                                     'catalogue '
                                                                                                                                     'public '
                                                                                                                                     'et '
                                                                                                                                     'ses '
                                                                                                                                     'illustrations '
                                                                                                                                     'sont '
                                                                                                                                     'téléchargés. '
                                                                                                                                     'Aucun '
                                                                                                                                     'fichier '
                                                                                                                                     'amiibo '
                                                                                                                                     'n’est '
                                                                                                                                     'envoyé. '
                                                                                                                                     'Les '
                                                                                                                                     'images '
                                                                                                                                     'déjà '
                                                                                                                                     'en '
                                                                                                                                     'cache '
                                                                                                                                     'restent '
                                                                                                                                     'utilisables '
                                                                                                                                     'hors '
                                                                                                                                     'ligne.',
 'Open data folder': 'Ouvrir le dossier de données',
 'Open recovery firmware folder': 'Ouvrir les firmwares de secours',
 'Open the Switch 2 guide': 'Ouvrir l’assistant Switch 2',
 'Open the amiibo scan in your game, present and remove the tag using the gestures for your firmware version, and use a USB data cable. Return to the PC to read the stored data if needed. A successful readback does not establish cryptographic authenticity.': 'Vérifie '
                                                                                                                                                                                                                                                                   'que '
                                                                                                                                                                                                                                                                   'le '
                                                                                                                                                                                                                                                                   'scan '
                                                                                                                                                                                                                                                                   'amiibo '
                                                                                                                                                                                                                                                                   'est '
                                                                                                                                                                                                                                                                   'ouvert '
                                                                                                                                                                                                                                                                   'dans '
                                                                                                                                                                                                                                                                   'le '
                                                                                                                                                                                                                                                                   'jeu, '
                                                                                                                                                                                                                                                                   'présente '
                                                                                                                                                                                                                                                                   'puis '
                                                                                                                                                                                                                                                                   'retire '
                                                                                                                                                                                                                                                                   'le '
                                                                                                                                                                                                                                                                   'tag '
                                                                                                                                                                                                                                                                   'avec '
                                                                                                                                                                                                                                                                   'les '
                                                                                                                                                                                                                                                                   'gestes '
                                                                                                                                                                                                                                                                   'de '
                                                                                                                                                                                                                                                                   'ta '
                                                                                                                                                                                                                                                                   'version, '
                                                                                                                                                                                                                                                                   'et '
                                                                                                                                                                                                                                                                   'utilise '
                                                                                                                                                                                                                                                                   'un '
                                                                                                                                                                                                                                                                   'câble '
                                                                                                                                                                                                                                                                   'USB '
                                                                                                                                                                                                                                                                   'de '
                                                                                                                                                                                                                                                                   'données. '
                                                                                                                                                                                                                                                                   'Si '
                                                                                                                                                                                                                                                                   'nécessaire, '
                                                                                                                                                                                                                                                                   'reviens '
                                                                                                                                                                                                                                                                   'au '
                                                                                                                                                                                                                                                                   'PC '
                                                                                                                                                                                                                                                                   'pour '
                                                                                                                                                                                                                                                                   'relire '
                                                                                                                                                                                                                                                                   'le '
                                                                                                                                                                                                                                                                   'contenu '
                                                                                                                                                                                                                                                                   'du '
                                                                                                                                                                                                                                                                   'Pico. '
                                                                                                                                                                                                                                                                   'Une '
                                                                                                                                                                                                                                                                   'relecture '
                                                                                                                                                                                                                                                                   'réussie '
                                                                                                                                                                                                                                                                   'ne '
                                                                                                                                                                                                                                                                   'garantit '
                                                                                                                                                                                                                                                                   'pas '
                                                                                                                                                                                                                                                                   'la '
                                                                                                                                                                                                                                                                   'validité '
                                                                                                                                                                                                                                                                   'cryptographique '
                                                                                                                                                                                                                                                                   'du '
                                                                                                                                                                                                                                                                   'fichier.',
 'Open your game, enable its amiibo feature, and start scanning.': 'Ouvre ton jeu, active sa fonction amiibo '
                                                                   'et lance le scan.',
 'Operation cancelled': 'Opération annulée',
 'Operation cancelled. Reconnect the Pico to check its contents before trying again.': 'Opération '
                                                                                       'interrompue. '
                                                                                       'Reconnecte le Pico '
                                                                                       'pour vérifier son '
                                                                                       'contenu avant un '
                                                                                       'nouvel essai.',
 'Operation in progress': 'Opération en cours',
 'Other amiibo · generic rewards': 'Autres amiibo · récompenses génériques',
 'Other name': 'Autre nom',
 'PA1 protocol: confirmed': 'Protocole PA1 : confirmé',
 'PREVIEW · New multi-slot firmware requires a separate physical test.': 'APERÇU · Le nouveau firmware '
                                                                         'multi-amiibo nécessite un essai '
                                                                         'physique séparé.',
 'Pico disconnected': 'Pico absent',
 'Pico identified · ': 'Pico identifié · ',
 'Pico not detected': 'Pico non détecté',
 'Pico readback is unavailable': 'Relecture du Pico indisponible',
 'Plants · gems': 'Plantes · gemmes',
 'Playlist': 'Liste',
 'Playlist order': 'Ordre de la liste',
 'Playlist saved and verified': 'Liste enregistrée et vérifiée',
 'Port: ': 'Port : ',
 'Possible TOTK rewards': 'Récompenses TOTK possibles',
 'Possible rewards, not guaranteed drops. Results depend on game progress, previously obtained items, and game version. Normally, each amiibo can be used once per day. The PC cannot see the loot received on the console.': 'Récompenses '
                                                                                                                                                                                                                              'possibles, '
                                                                                                                                                                                                                              'pas '
                                                                                                                                                                                                                              'une '
                                                                                                                                                                                                                              'promesse '
                                                                                                                                                                                                                              'à '
                                                                                                                                                                                                                              'chaque '
                                                                                                                                                                                                                              'scan. '
                                                                                                                                                                                                                              'Le '
                                                                                                                                                                                                                              'tirage '
                                                                                                                                                                                                                              'dépend '
                                                                                                                                                                                                                              'de '
                                                                                                                                                                                                                              'la '
                                                                                                                                                                                                                              'progression, '
                                                                                                                                                                                                                              'des '
                                                                                                                                                                                                                              'objets '
                                                                                                                                                                                                                              'déjà '
                                                                                                                                                                                                                              'obtenus '
                                                                                                                                                                                                                              'et '
                                                                                                                                                                                                                              'de '
                                                                                                                                                                                                                              'la '
                                                                                                                                                                                                                              'version '
                                                                                                                                                                                                                              'du '
                                                                                                                                                                                                                              'jeu. '
                                                                                                                                                                                                                              'En '
                                                                                                                                                                                                                              'général '
                                                                                                                                                                                                                              ': '
                                                                                                                                                                                                                              'une '
                                                                                                                                                                                                                              'utilisation '
                                                                                                                                                                                                                              'par '
                                                                                                                                                                                                                              'jour '
                                                                                                                                                                                                                              'et '
                                                                                                                                                                                                                              'par '
                                                                                                                                                                                                                              'amiibo. '
                                                                                                                                                                                                                              'Le '
                                                                                                                                                                                                                              'PC '
                                                                                                                                                                                                                              'ne '
                                                                                                                                                                                                                              'peut '
                                                                                                                                                                                                                              'pas '
                                                                                                                                                                                                                              'connaître '
                                                                                                                                                                                                                              'le '
                                                                                                                                                                                                                              'butin '
                                                                                                                                                                                                                              'obtenu '
                                                                                                                                                                                                                              'sur '
                                                                                                                                                                                                                              'la '
                                                                                                                                                                                                                              'console.',
 'Preferences and local data': 'Préférences et données locales',
 'Presented:': 'Présenté :',
 'Previous': 'Précédent',
 'Princess Zelda Fabric · plants and gems': 'Tissu de Zelda · plantes et gemmes',
 'Private nam': 'Nom priv',
 'Private name': 'Nom privé',
 'Pro Controller 2 · Pico identity not confirmed': 'Manette Pro Controller 2 · identité Pico non confirmée',
 'Progress measures the bytes actually transmitted and read back.': 'La progression vient des octets '
                                                                    'réellement transmis et relus.',
 'Rare drop pool': 'Tirage rare',
 'Readback compared and verified': 'Relecture comparée et vérifiée',
 'Reading back from the Pico': 'Relecture depuis le Pico',
 'Reading back playlist': 'Relecture de la liste',
 'Recognized · reported': 'Reconnu · déclaré',
 'Recovery and versions': 'Récupération et versions',
 'Recovery firmware': 'Firmwares de secours',
 'Refresh metadata': 'Actualiser les métadonnées',
 'Release a 2-to-5-second hold to enter configuration.': 'Relâche un maintien entre 2 et 5 secondes pour '
                                                         'ouvrir la configuration.',
 'Remove from favorites': 'Retirer des favoris',
 'Requires a game version supporting the new sages (1.4.0 or later).': 'Nécessite une version du jeu prenant '
                                                                       'en charge les nouveaux sages (1.4.0 '
                                                                       'ou ultérieure).',
 'Returning to controller mode was not confirmed. Disconnect and reconnect the Pico to restart it.': 'Le '
                                                                                                     'retour '
                                                                                                     'en '
                                                                                                     'mode '
                                                                                                     'manette '
                                                                                                     'n’a '
                                                                                                     'pas '
                                                                                                     'été '
                                                                                                     'confirmé. '
                                                                                                     'Débranche/rebranche '
                                                                                                     'le '
                                                                                                     'Pico '
                                                                                                     'pour '
                                                                                                     'le '
                                                                                                     'redémarrer.',
 'Sage of Fire Fabric · Goron weapons': 'Tissu du sage du feu · armes gorons',
 'Sage of Lightning Fabric · Gerudo equipment': 'Tissu de la sage de la foudre · équipement gerudo',
 'Sage of Spirit Fabric · Zonaite and Construct bows': 'Tissu du sage de l’esprit · sonium et arcs de Golem',
 'Sage of Water Fabric · Zora spears': 'Tissu du sage de l’eau · lances zoras',
 'Sage of Wind Fabric · bows and arrows': 'Tissu du sage du vent · arcs et flèches',
 'Save confirmed': 'Enregistrement confirmé',
 'Saved and verified': 'Enregistré et vérifié',
 'Saved and verified on the Pico': 'Enregistré et vérifié sur le Pico',
 'Saving to flash…': 'Enregistrement dans la flash…',
 'Search amiibo or characters…': 'Rechercher un amiibo, un personnage…',
 'Search amiibo or rewards…': 'Rechercher un amiibo ou une récompense…',
 'Search: Epona, armor, fabric, Link…': 'Rechercher : Épona, tenue, tissu, Link…',
 'Select all shown': 'Cocher les amiibo affichés',
 'Select the correct Pico explicitly': 'Sélectionne explicitement le bon Pico',
 'Select up to 64 amiibo.': 'Sélectionne jusqu’à 64 amiibo.',
 'Selected amiibo rewards': 'Récompenses de la sélection',
 'Sending to the Pico': 'Transmission vers le Pico',
 'Sheik Mask · Sheik Fabric': 'Masque de Sheik · tissu de Sheik',
 'Show TOTK rewards': 'Afficher les récompenses TOTK',
 'Single amiibo (replace playlist)': 'Un seul amiibo (remplace la liste)',
 'Size:': 'Taille :',
 'Size: ': 'Taille : ',
 'Sky armor · White Sword of the Sky · Sword-Spirit Fabric': 'Tenue du ciel · épée céleste · tissu de Fay',
 'Sources and limitations': 'Sources et portée',
 'Start by loading an amiibo and verifying its readback on the Load page.': 'Commence par charger un amiibo '
                                                                            'et faire vérifier sa relecture '
                                                                            'dans la page Charger.',
 'Step ': 'Étape ',
 'Switch 2 guide': 'Assistant Switch 2',
 'Synthetic test': 'Test synthétique',
 'TEST · Isolated profile, artificial data, USB access disabled': 'TEST · Profil isolé, données '
                                                                  'artificielles, accès USB désactivé',
 'TEST · Offline reference · no USB access': 'TEST · Référence hors ligne · aucun accès USB',
 'TOTK rewards': 'Récompenses TOTK',
 'Tag loaded:': 'Amiibo chargé :',
 'Tag loaded: ': 'Tag chargé : ',
 'Test communication': 'Tester la communication',
 'The LED confirms a change, not a tag name.': 'La LED confirme le changement, pas le nom de l’amiibo.',
 'The Manager cannot observe the Switch 2. Confirm the scan result yourself below.': 'Le Manager ne peut pas '
                                                                                     'observer la Switch 2. '
                                                                                     'Confirme toi-même le '
                                                                                     'résultat du scan '
                                                                                     'ci-dessous.',
 'The PC cannot': 'Le PC ne peut pas',
 'The Pico did not confirm the save. Read the tag state again before continuing.': "Le Pico n'a pas confirmé "
                                                                                   "l'enregistrement. L'état "
                                                                                   'du tag doit être relu '
                                                                                   'avant de continuer.',
 'The Pico did not respond in time. Hold BOOTSEL for two seconds to enter configuration, then retry.': 'Le '
                                                                                                       'Pico '
                                                                                                       "n'a "
                                                                                                       'pas '
                                                                                                       'répondu '
                                                                                                       'à '
                                                                                                       'temps. '
                                                                                                       'Reviens '
                                                                                                       'en '
                                                                                                       'configuration '
                                                                                                       'avec '
                                                                                                       'BOOTSEL '
                                                                                                       'pendant '
                                                                                                       'deux '
                                                                                                       'secondes, '
                                                                                                       'puis '
                                                                                                       'réessaie.',
 'The Pico is in its bootloader. Manually install your firmware, then restart it to load an amiibo.': 'Le '
                                                                                                      'Pico '
                                                                                                      'est '
                                                                                                      'dans '
                                                                                                      'son '
                                                                                                      'bootloader. '
                                                                                                      'Installe '
                                                                                                      'manuellement '
                                                                                                      'ton '
                                                                                                      'firmware '
                                                                                                      'puis '
                                                                                                      'redémarre-le '
                                                                                                      'pour '
                                                                                                      'charger '
                                                                                                      'un '
                                                                                                      'amiibo.',
 'The Pico is ready to receive an amiibo.': 'Le Pico est prêt à recevoir un amiibo.',
 'The USB port is disconnected, busy, or inaccessible. Reconnect the Pico and close other tools using this port.': 'Le '
                                                                                                                   'port '
                                                                                                                   'USB '
                                                                                                                   'est '
                                                                                                                   'déconnecté, '
                                                                                                                   'occupé '
                                                                                                                   'ou '
                                                                                                                   'inaccessible. '
                                                                                                                   'Rebranche '
                                                                                                                   'le '
                                                                                                                   'Pico '
                                                                                                                   'et '
                                                                                                                   'ferme '
                                                                                                                   'les '
                                                                                                                   'autres '
                                                                                                                   'outils '
                                                                                                                   'qui '
                                                                                                                   'utilisent '
                                                                                                                   'ce '
                                                                                                                   'port.',
 'The amiibo was recognized': 'L’amiibo a été reconnu',
 'The file must contain 540 or 572 bytes.': 'Le fichier doit contenir 540 ou 572 octets.',
 'The final state does not match the verified data': "L'état final ne correspond pas aux données vérifiées",
 'The firmware folder is not included in this copy. Use the complete portable distribution.': 'Le dossier '
                                                                                              'firmware '
                                                                                              'n’est pas '
                                                                                              'présent dans '
                                                                                              'cette copie. '
                                                                                              'Utilise la '
                                                                                              'distribution '
                                                                                              'portable '
                                                                                              'complète.',
 'The local file has changed or is corrupted. Import the original again.': 'Le fichier local a changé ou est '
                                                                           "corrompu. Réimporte l'original.",
 'The old single-tag firmware still supports single loads.': 'L’ancien firmware reste compatible avec le '
                                                             'chargement d’un seul amiibo.',
 'The operation was not verified. Check the connection and file format, then retry.': "L'opération n'a pas "
                                                                                      'été vérifiée. Vérifie '
                                                                                      'la connexion et le '
                                                                                      'format du fichier, '
                                                                                      'puis réessaie.',
 'The port does not respond to the PicoAmiibo protocol.': 'Le port ne répond pas au protocole PicoAmiibo.',
 'The public source is unavailable or its format has changed. Your local amiibo remain usable; no private files were uploaded.': 'La '
                                                                                                                                 'source '
                                                                                                                                 'publique '
                                                                                                                                 'ne '
                                                                                                                                 'répond '
                                                                                                                                 'pas '
                                                                                                                                 'ou '
                                                                                                                                 'son '
                                                                                                                                 'format '
                                                                                                                                 'a '
                                                                                                                                 'changé. '
                                                                                                                                 'Tes '
                                                                                                                                 'amiibo '
                                                                                                                                 'locaux '
                                                                                                                                 'restent '
                                                                                                                                 'utilisables '
                                                                                                                                 '; '
                                                                                                                                 'aucun '
                                                                                                                                 'fichier '
                                                                                                                                 'privé '
                                                                                                                                 'n’a '
                                                                                                                                 'été '
                                                                                                                                 'envoyé.',
 'The scan failed': 'Le scan a échoué',
 'This amiibo is no longer in the library.': "Cet amiibo n'existe plus dans la bibliothèque.",
 'This confirmation is saved as your observation. The PC cannot read the Pico while it is connected to the console.': 'Cette '
                                                                                                                      'confirmation '
                                                                                                                      'est '
                                                                                                                      'enregistrée '
                                                                                                                      'comme '
                                                                                                                      'ton '
                                                                                                                      'observation. '
                                                                                                                      'Le '
                                                                                                                      'PC '
                                                                                                                      'ne '
                                                                                                                      'peut '
                                                                                                                      'pas '
                                                                                                                      'lire '
                                                                                                                      'le '
                                                                                                                      'Pico '
                                                                                                                      'lorsqu’il '
                                                                                                                      'est '
                                                                                                                      'branché '
                                                                                                                      'à '
                                                                                                                      'la '
                                                                                                                      'console.',
 'This firmware does not support playlists. No tag data was sent.': 'Ce firmware ne gère pas les listes. '
                                                                    'Aucune donnée amiibo n’a été envoyée.',
 'This port did not confirm its PicoAmiibo identity. No load has been verified.': "Ce port n'a pas confirmé "
                                                                                  'son identité PicoAmiibo. '
                                                                                  "Aucun chargement n'est "
                                                                                  'validé.',
 'Time armor · Biggoron Sword · Lon Lon Ranch Fabric': 'Tenue du temps · épée Biggoron · tissu du ranch',
 'Toon Link · Super Smash Bros.': 'Link cartoon · Super Smash Bros.',
 'Toon Link · The Wind Waker': 'Link cartoon · The Wind Waker',
 'Toon Zelda · The Wind Waker': 'Zelda cartoon · The Wind Waker',
 'Transfer in progress': 'Transfert en cours',
 'Tulin': 'Babil',
 'Tulin · TOTK': 'Babil / Tulin · TOTK',
 'UNKNOWN VERSION': 'VERSION INCONNUE',
 'USB configuration': 'Configuration USB',
 'USB identity:': 'Identité USB :',
 'USB identity: ': 'Identification USB : ',
 'Unidentified': 'Non identifié',
 'Unidentified amiibo': 'Amiibo non identifié',
 'Unknown firmware version: do not assume 0.1.1 or 0.1.2 gestures. Return to PC configuration to identify the USB version.': 'Version '
                                                                                                                             'non '
                                                                                                                             'identifiée '
                                                                                                                             ': '
                                                                                                                             'ne '
                                                                                                                             'suppose '
                                                                                                                             'pas '
                                                                                                                             'les '
                                                                                                                             'gestes '
                                                                                                                             'de '
                                                                                                                             '0.1.1 '
                                                                                                                             'ou '
                                                                                                                             '0.1.2. '
                                                                                                                             'Reviens '
                                                                                                                             'en '
                                                                                                                             'configuration '
                                                                                                                             'PC '
                                                                                                                             'pour '
                                                                                                                             'identifier '
                                                                                                                             'la '
                                                                                                                             'version '
                                                                                                                             'USB.',
 'Unknown result': 'Résultat inconnu',
 'Unrecognized public catalog format': 'Format du catalogue public non reconnu',
 'Unsupported reported size': 'Taille déclarée incompatible',
 'Vah Medoh Divine Helm · Rito-Champion Fabric': 'Heaume de Medoh · tissu Revali',
 'Vah Naboris Divine Helm · Gerudo-Champion Fabric': 'Heaume de Naboris · tissu Urbosa',
 'Vah Rudania Divine Helm · Goron-Champion Fabric': 'Heaume de Rudania · tissu Daruk',
 'Vah Ruta Divine Helm · Zora-Champion Fabric': 'Heaume de Ruta · tissu Mipha',
 'Verification': 'Vérification',
 'Verified readback': 'Relecture vérifiée',
 'Version 0.1.0: a short tap presents or removes the tag; a one-second hold sends L+R.': 'Version 0.1.0 : un '
                                                                                         'appui bref '
                                                                                         'présente/retire le '
                                                                                         'tag ; le maintien '
                                                                                         "d'une seconde émet "
                                                                                         'L+R.',
 'Version from USB serial:': 'Version annoncée en USB :',
 'Version from USB serial: ': 'Version via série USB : ',
 'Visit the Depths': 'Avoir visité les Profondeurs',
 'Wait for verification to finish or use Cancel operation before closing.': 'Attends la fin de la '
                                                                            'vérification ou utilise « '
                                                                            'Annuler l’opération » avant de '
                                                                            'fermer.',
 'Waiting for a response from the Pico…': 'En attente de la réponse du Pico…',
 'Waiting to load': 'En attente du chargement',
 'What did you observe in the game?': 'Qu’as-tu observé dans le jeu ?',
 'While the game waits for a scan, briefly tap BOOTSEL once and wait about half a second.': 'Pendant '
                                                                                            "l'attente du "
                                                                                            'scan : un appui '
                                                                                            'bref sur '
                                                                                            'BOOTSEL, puis '
                                                                                            'attends environ '
                                                                                            'une '
                                                                                            'demi-seconde.',
 'Wind armor · Sea-Breeze Boomerang · King of Red Lions Fabric': 'Tenue du vent · boomerang · tissu du Lion '
                                                                 'rouge',
 'Windows USB enumeration is unavailable': 'Énumération USB Windows indisponible',
 'Windows USB enumeration was interrupted': 'Énumération USB Windows interrompue',
 'Wolf Link': 'Link loup',
 'YOUR LIBRARY, READY TO GO': 'TA BIBLIOTHÈQUE, PRÊTE À PARTIR',
 'You reported a failed scan. See the troubleshooting tips below.': 'Échec du scan déclaré. Consulte les '
                                                                    'pistes de dépannage ci-dessous.',
 'You reported successful recognition in the game.': 'Reconnaissance en jeu confirmée par toi.',
 'Young Link · Super Smash Bros.': 'Link enfant · Super Smash Bros.',
 'Your Pico': 'Ton Pico',
 'Your amiibo was saved on the Pico and read back byte for byte.': 'Ton amiibo a été enregistré et relu à '
                                                                   "l'identique sur le Pico.",
 'Your library starts here.\nImport your 540-byte or 572-byte .bin files. Unidentified files remain usable.': 'Ta '
                                                                                                              'bibliothèque '
                                                                                                              'commence '
                                                                                                              'ici.\n'
                                                                                                              'Importe '
                                                                                                              'tes '
                                                                                                              'fichiers '
                                                                                                              '.bin '
                                                                                                              'de '
                                                                                                              '540 '
                                                                                                              'ou '
                                                                                                              '572 '
                                                                                                              'octets. '
                                                                                                              'Les '
                                                                                                              'fichiers '
                                                                                                              'non '
                                                                                                              'identifiés '
                                                                                                              'restent '
                                                                                                              'utilisables.',
 'Your library, your Pico, your next adventure.': 'Ta bibliothèque, ton Pico, ta prochaine aventure.',
 'Zelda Wiki · TOTK amiibo drop tables': 'Zelda Wiki · tableaux amiibo TOTK',
 'Zelda and Loftwing': 'Zelda et Célestrier',
 'changed': 'changé',
 'do not assume': 'ne suppose pas',
 'does not summon': 'ne fait pas apparaître',
 'not detected': 'non détecté',
 'not per-scan': 'pas des chances',
 'protocol': 'protocole',
 'quickly tap BOOTSEL twice': 'deux appuis brefs',
 'unavailable': 'indisponible',
 'unidentified': 'à identifier',
 'unknown': 'inconnue',
 'unknown version': 'version inconnue',
 '· Windows x64\nThe Manager never flashes firmware. Recovery: hold BOOTSEL while connecting the Pico to the PC, confirm the correct RPI-RP2 drive, then manually copy the recovery UF2.\n0.1.1: release preceding the reported Epona success. 0.1.2: version without L+R; separate console qualification.': '· '
                                                                                                                                                                                                                                                                                                             'Windows '
                                                                                                                                                                                                                                                                                                             'x64\n'
                                                                                                                                                                                                                                                                                                             'Le '
                                                                                                                                                                                                                                                                                                             'Manager '
                                                                                                                                                                                                                                                                                                             'ne '
                                                                                                                                                                                                                                                                                                             'remplace '
                                                                                                                                                                                                                                                                                                             'jamais '
                                                                                                                                                                                                                                                                                                             'le '
                                                                                                                                                                                                                                                                                                             'firmware. '
                                                                                                                                                                                                                                                                                                             'Pour '
                                                                                                                                                                                                                                                                                                             'récupérer '
                                                                                                                                                                                                                                                                                                             'le '
                                                                                                                                                                                                                                                                                                             'Pico '
                                                                                                                                                                                                                                                                                                             ': '
                                                                                                                                                                                                                                                                                                             'le '
                                                                                                                                                                                                                                                                                                             'rebrancher '
                                                                                                                                                                                                                                                                                                             'au '
                                                                                                                                                                                                                                                                                                             'PC '
                                                                                                                                                                                                                                                                                                             'avec '
                                                                                                                                                                                                                                                                                                             'BOOTSEL '
                                                                                                                                                                                                                                                                                                             'déjà '
                                                                                                                                                                                                                                                                                                             'maintenu, '
                                                                                                                                                                                                                                                                                                             'confirmer '
                                                                                                                                                                                                                                                                                                             'le '
                                                                                                                                                                                                                                                                                                             'bon '
                                                                                                                                                                                                                                                                                                             'RPI-RP2, '
                                                                                                                                                                                                                                                                                                             'puis '
                                                                                                                                                                                                                                                                                                             'copier '
                                                                                                                                                                                                                                                                                                             'manuellement '
                                                                                                                                                                                                                                                                                                             'son '
                                                                                                                                                                                                                                                                                                             'UF2 '
                                                                                                                                                                                                                                                                                                             'de '
                                                                                                                                                                                                                                                                                                             'secours.\n'
                                                                                                                                                                                                                                                                                                             '0.1.1 '
                                                                                                                                                                                                                                                                                                             ': '
                                                                                                                                                                                                                                                                                                             'livraison '
                                                                                                                                                                                                                                                                                                             'précédant '
                                                                                                                                                                                                                                                                                                             'Épona, '
                                                                                                                                                                                                                                                                                                             'selon '
                                                                                                                                                                                                                                                                                                             'l’utilisateur. '
                                                                                                                                                                                                                                                                                                             '0.1.2 '
                                                                                                                                                                                                                                                                                                             ': '
                                                                                                                                                                                                                                                                                                             'variante '
                                                                                                                                                                                                                                                                                                             'sans '
                                                                                                                                                                                                                                                                                                             'L+R, '
                                                                                                                                                                                                                                                                                                             'qualification '
                                                                                                                                                                                                                                                                                                             'console '
                                                                                                                                                                                                                                                                                                             'séparée.',
 '· quantity ': '· quantité ',
 '· weight ': '· poids '}
_keys=sorted(FR,key=len,reverse=True)
_pattern=re.compile("|".join(
    (r"(?<!\w)" if k[0].isalnum() else "")+re.escape(k)+(r"(?!\w)" if k[-1].isalnum() else "")
    for k in _keys))

def set_language(code):
    global _language
    _language=code if code in ("en","fr") else "en"

def language():return _language

def t(text):
    value=str(text)
    return _pattern.sub(lambda m:FR[m.group(0)],value) if _language=="fr" else value
