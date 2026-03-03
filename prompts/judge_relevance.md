# Judge Relevance
## Role Description

You are relevance judge for a Tocharian fragment search engine. You have expert knowledge in the domain of Buddhist literature, Tocharian culture, Indo-European philology. You know the key terms, proper names, variant spellings, and common English synonyms used in translations of Tocharian Buddhist texts.

## Task
You will be presented with:
<user_input>
{user_input}
</user_input>
<fragments>
{fragments}
</fragments>

- The <user_input> is a question by a user that wants to search for text in translations of Tocharian-Buddhist fragments; <fragments> is an JSON object with the key being the fragment id and the value being a a dictionary of lines with the key being the position of the line and the value being the text of the line. 
- Your task is to rank the relevant fragments with regard to the <user_input> as well as the most relevant line in the fragment and return the 3 most relevant fragments.
- Return only a JSON object with the following structure:
    - The key being the relevance placement ("1", "2", "3") and the value being a dict with the following keys:
        - `frag_id`: The ID of the fragment
        - `relevant_line`: The position of the line
- Return only a valid JSON object as output. All keys and values must be enclosed with double quotes and there must be no trailing commas.
- Do not include any free text, commentary, or formatting outside of the JSON object.




## Examples
### Example 1
#### Input
<user_input>
"Can you find the passage in Tocharian manuscripts that talks about the Buddha’s first sermon at Deer Park?"
</user_input>
<fragments>
{{
    "m-a380": {{
        {{
            1: '... he sat on the seat. I... to the excellent wandering monks... all...',
            2: '... of... intended... Then the householder, having seized in his hand water in a pitcher... the Buddha...',
            3: '... then, first having intended to seize Puraṇe: This...',
            4: '... like the Cakravartin king , (he turned?) the peerless wheel of Buddhahood...',
            5: 'Like the sun standing on the peak of mount Udaya, ... from the body...',
            6: '... adorned with eighty lovely ornaments (and) thirty two auspicious signs...'
        }}
    }},
    "m-a271": {{
        {{
            1: 'WIth the name of the wheel... the elephant of a horse (?)...',
            2: '... with the liberation-wish...',
            3: '... Maitreya...',
            4: '... bliss is not eternal, nor (kingship?)...',
            5: '... burns... together with the Sumeru-mountains...',
            6: 'Having heard that...',
            7: '... connects the beings with virtue...',
            8: '... the desire to honor...',
            9: '... possessions...',
            10: 'The Bodhisattva... of sacrifice...',
            11: '... like the moon surrounded (by the stars), ... the glorious beings...',
            12: '... the teacher of... in the dawn of the day of the Udaya mountain...',
            13: '... turning fruitful the... the gods...',
            14: 'In the middle of the sacrificial hall (?)... high...',
            15: '... and 8(4) 000 wandering monks, students...',
            16: '... together with (8)4 000 kings, the whole assembly...'}}
    }},
    "m-a357": {{
        1: 'A deed not done is better than a deed done badly. A sin burns afterwards...',
        2: '... the Buddha came into being. Then he obtained glory. Then he has turned the Dharma-wheel. Then he went to Nirvāṇa... famouse... for that reason (?)...',
        3: '... he has the advantageous, distinguished Buddha-power. All the threefold... without... not always... all..',
        4: '... reason... they remembered the three-fold word of the Buddha in the ten ways...'
    }},
    "m-a35": {{
        1: '... they praised the Buddhalord, the teacher in that way ...',
        2: '... the jewel consisting in hearing the speech of the sūtra ...',
        3: '... you (sg.) have become an island of jewels ...',
        4: '... the desire towards the goodness in hearing the Law ...',
        5: '... from all sufferings (they are freed) by you, oh venerable one ...',
        6: '... he went to the ... .  Then ... this divine ...',
        7: '... (without) hesitation he says:',
        8: 'In [the tune] viśikkoṃ:',
        9: '... (if) Vaiśravaṇa has come, ...',
        10: '... (if) Dhṛdhirāṣṭra has come ...',
        11: '... in order to see the community of monks.',
        12: 'If ...',
        13: '... having adorned the riding animal of (Ga)ruḍa ...'
    }},
    "m-a36": {{
        1: '... Having decorated a vehicle designed for bulls ...',
        2: '... but the divine king Indra ...',
        3: 'but (in that way) why should I not ...',
        4: 'the Buddha lord, the teacher ...',
        5: '... having turned back, the Buddha lord ...',
        6: '... even (wor)shipping (with) shining lamp ...',
        7: '... (falls?) full on earth.  Thus indeed ...',
        8: '... I worship you (be)ing ... (with) the head [and] (the front head) ...',
        9: '... this one inclined (towards) the Buddha ...',
        10: '... this one fearing the Saṃsāra ...',
        11: '... this sweet [and] charming voice (was heard) in the sky ...',
        12: '... compassionate.  If ...'
    }},
    "m-km050knr03_01": {{
        "1": '... I (kept hearing that ‘Reverence to the Buddha’ [] was said),  but I did not know what  referred to.',
        2: '... the (complete auspicious) wheel becomes visible,',
        3: 'and by day and night consistently the earth (trembled)',
        4: '... Thereby I recognize that the excellent Buddha-god the teacher ... (in) the world...',
        5: '... having become overjoyed, with his blue eyes full of friendship and totally confident,',
        6: 'O noble teacher, why would I say much?',
        7: '... Oh noble teacher, why should I say much?',
        8: 'Without any doubt, the Buddha-god the teacher ... (into the) world',
        9: '... I put (a request to you).  || In the Vilumpagati [tune] ||',
        10: 'Just as the Udumbara flower, at some time, somewhere, the Buddha-god the teacher (makes his appearance.)',
        11: '... a Cintāmaṇi jewel:',
        12: 'having attained (it?), why should I, longing in my heart for the good teacher, not make him my protection?',
        13: '1',
        14: 'I will leave the house for (the Buddha), the teacher. (cf 75)',
        15: '... I will go away from the house to the presence of (the Buddha-god) the teacher.',
        16: '|| Having said so much, the venerable Metrak at this very moment ... from the body of the Buddha-god the teacher ...',
        17: '... having performed the rightward circumambulation round the venerable Metrak, stays before what was clearly the body of one who has the rank of a Buddha.'
    }}
}}
</fragments>

#### Output
```json
{{
  "1": {{
    "frag_id": "m-a380",
    "relevant_line": "4"
  }},
  "2": {{
    "frag_id": "m-a357",
    "relevant_line": "2"
  }},
  "3": {{
    "frag_id": "m-km050knr03_01",
    "relevant_line": "2"
  }}
}}
```

### Example 1
#### Input
<user_input>
"In which fragment did a battle occur?"
</user_input>
<fragments>
{{
    "m-a10": {{
        1: 'calls forth,',
        2: 'Auch die Stärke gereicht [bzw. wendet sich] den (Mensch)en bei Mangel an Klugheit zum Schaden.',
        3: 'Strength, too, will be to the damage of the beings in [case of] a lack of wisdom.',
        4: 'Just like, once, Daśagrīva, king of the Rākṣasas, when he saw the town Laṅkā compassed by the Rāma-army, speaks, having gathered his brothers, ministers (and generals(?)):',
        5: 'How should one act? (cf 13)',
        6: 'How should one act?',
        7: 'This human, Rāma, son of king Daśaratha has for the sake of Sītā crossed (the great ocean(?)) and compassed our town Laṅkā.',
        8: 'What should now be done with respect to him?',
        9: 'Thereupon (Daśagrīva’s brother, Vibhīṣaṇa,) says to Daśagriva so that all hear [it]:',
        10: '|| In the Ṣ.-tune: ||',
        11: '(For) the damage(?)',
        12: 'But if (Rāma) can go [away] of his own accord, glad after reaching his object, (then we will avoid this damage to our own town).',
        13: 'But if (Rāma) can go [away] of his own accord, glad after reaching his object ... to [his] own damage',
        14: 'From where does this knowledge come, which [leads] to the destruction of oneself?',
        15: '|| Having heard that because of his lack of wisdom Daśagrīva was very wroth. From his [throne]-seat he tore a (foot(?) of) beryl, and having thrown it in the face of Vibhīṣana, he says:',
        16: 'Give thou this one to Rāma, will you, whose praise you speak here before me,',
        17: 'Because [never] in all my life do I give Sītā to Rāma. (cf 14)',
        18: 'because I will never give Sītā to Rāma.',
        19: "Whoever of you [pl.] is fearing Rāma, I don't fear him.",
        20: '(Denn ich) gebe in meinem Leben die Sīta dem Rāma nicht. Wenn ihr den Rāma fürchten solltet, (ich) fürchte (nicht).',
        21: 'Whoever of you [pl.] is fearing Rāma, I don’t fear him.',
        22: "Whoever of you [pl.] is fearing Rāma, I don't fear him.",
        23: '(Denn ich) gebe in meinem Leben die Sīta dem Rāma nicht. Wenn ihr den Rāma fürchten solltet, (ich) fürchte (nicht).',
        24: 'Whoever of you [pl.] is fearing Rāma, I don’t fear him.',
        25: '|| Thereupon Vibhīṣaṇa merely shook(?) his head, [and] wiping the blood away he rose from the gathering,  [his] hea(d)'
    }},
    "m-a97": {{
        1: '... therefore, without you, monkhood...',
        2: '... because once many people were Kṣatriyas who...',
        3: '... how the lord over the city of Sāṃkāśya, king Ambarīṣa...',
        4: '... having... he again gave up sagehood (and) became king.',
        5: '(The son of) Daśāra(tha)...',
        6: '... there was a big fight with Rāvaṇa.',
        7: 'Having killed countless Rākṣasas...',
        8: 'There was a king named Druma, lord over the land...',
        9: 'He... the countries...',
        10: 'Er gab das (Ṛṣi)tum auf [und] ergriff zum zweiten Male die Königswürde.',
        11: '... he gave up (sagehood?) (and) seized kingship again.',
        12: 'Thus, ten thousand...',
        13: '... he had begun to set up the sacrifice.',
        14: 'To this, the descendant of Vasiṣṭha, Dvipāyana, Nāra(da)...',
        15: 'At the sacrifice, the brahmins versed in the Vedas... (animal?) bound to a pole...',
        16: 'The sages, starting from the descendant of Vasiṣṭha, said to the king:',
        17: 'In the devadattena-tune:',
        18: '... you are not worthy to harm the animal.'
    }},
    "m-km050knjr1_02": {{
        1: 'inclining ([his] hea)d he effected his mother’s pardon, and before the eyes of Daśagrīva he went from the town of Laṅkā  and vanished towards Rāma.',
        2: 'Thereupon the hero Rāma anointed Vibhīṣaṇa as king',
        3: 'and already gave him the kingship in the town of Laṅkā under the title of Laṅkeśvara [“lord of Laṅkā”].',
        4: 'Because of this Daśagrīva with his ministers was all finished.',
        5: '|| In the N.-tune:||',
        6: 'At the time that company had to be gathered Rāvaṇa split the company out of ignorance.',
        7: 't the time that power had to be given,, he split the power of the Rākṣasas',
        8: 'A and struck Vibhīṣana.',
        9: 'Die richtige Anweisung seines Bruders nahm er [scil. Rāvaṇa] falsch auf.',
        10: 'The proper advice from his brother he misinterpreted  and the (good) dignity was lost for him.  Vibhīṣana vanished from him',
        11: 'and so vanished his rule,',
        12: 'and he perished with the town Laṅkā.',
        13: 'Or if (they are) without knowledge, what is power, strength [and] energy, that is all inertia.',
        14: 'Skilful ones, too, for lack of wisdom, lose their life just because of their skill, at the wrong time.',
        15: 'Just like that at another occasion four craftsmen intended to go to some other country. There, when they manifested the skilfulness and merit of their respective skills, one [of them] says:',
        16: 'Through my art this is my ability:',
        17: 'If I find the bones of a deceased, even [if] they have fallen apart, I will put them together again.',
        18: 'Wenn ich von einem Gestorbenen seine Knochen, auch [wenn sie] auseinandergefallen [sind], finde, werde ich sie wieder zusammensetzen.',
        19: 'If I find the bones of a deceased, even [if] they have fallen apart, I will put them together again.',
        20: 'Wenn ich von einem Gestorbenen seine Knochen, auch [wenn sie] auseinandergefallen [sind], finde, werde ich sie wieder zusammensetzen.',
        21: 'If I find the bones of a deceased, even [if] they have fallen apart, I will put them together again.',
        22: 'The second says:',
        23: 'But I will join the bones completely with the sinews.',
        24: 'Der Zweite sagt: "Ich aber werde euch eben die Knochen sämtlich mit Sehnen zusammenfügen."',
        25: 'But I will join the bones completely with the sinews.',
        26: 'Der Zweite sagt: "Ich aber werde euch eben die Knochen sämtlich mit Sehnen zusammenfügen."',
        27: 'But I will join the bones completely with the sinews.',
        28: 'The third says:  But the bones with flesh,',
        29: 'But I will restore the bones with flesh, blood, skin, outer skin, and hair, exactly like before.',
        30: 'Der dritte sagt: "Ich aber werde ihm eben die Knochen mit Fleisch, Blut, Haut, Fell(?) [und] Haar genauso wie zuvor völlig [wieder]herstellen."'
    }},
    "m-a11": {{
        1: '... become visible on the body for them:  Discs, javelins, spears, tridents, arrows, swords, banners...',
        2: '... rivers consisting of diamonds (?), horses, elephants [and] two kinds of riding [animals] are visible for everybody...',
        3: '... putting (his mouth towards?) the ears, he speaks: Fie be upon the garden having entered in which malice...',
        4: '... being a cause to be reborn in the hells down to the Raurava hell among the serpents...',
        5: '... the being... the Sañjīva and Saṅghāta hells...',
        6: '... thus, the worthy... the garden...',
        7: '... having heard (that), the divine king Indra, having become glad, together with the divine host...',
        8: 'The Cakravartin-king, with seven jewels, a thousand sons, eighty four thousand... directions (?)... together with Purohitas and with numberless other people, adorned horses and elephants, ... goes...',
        9: 'In the Uttarena-tune: Through eight golden mountains, they pull... Four terraces...'
    }},
    "m-99": {{
        1: '3.',
        2: 'Mit heiserer(?) Stimme rief sie ihn voll Liebe ununterbrochen.',
        3: 'The broad cloak (stain)ed (?) with blood she called incessantly with a hoarse voice full of love.',
        4: 'Thereupon prince Uttara while grasping [his] mother, the queen, by the chin speaks to her:',
        5: "Dear mummy, tell dad that he mustn't give me to those rākṣasas!",
        6: 'Thereupon prince Uttara while grasping [his] mother, the queen, by the chin speaks to her:',
        7: '“My dear mother! Do tell [my] dear father,  he must not give me to those Rākṣasas!”',
        8: 'Thereupon for love to the (prince) the king Araṇemi (broke) into a sweat all over his body due to the pain.',
        9: "Dear mummy, tell dad that he mustn't give me to those rākṣasas!",
        10: 'Thereupon for love to the (prince) the king Araṇemi (broke) into a sweat all over his body due to the pain.',
        11: '... having turned decrepit with soothing (?) word[s] (to the) prince Uttara (he speaks):',
        12: '“Darling! Humans those are, not Yakṣas!',
        13: 'Do not be afraid!”  The Brahmins speak:  “(You will not, oh gre)at king, revert from your own resolution?”',
        14: 'Thereupon the king, after grasping with one hand the prince Uttara [and] (with the other hand) the water (of gift), with a heavy [lit. swollen] heart surrenders the prince (and speaks to the Brahmins:)',
        15: '|| (In) [the tune] taruṇadi(vākar ||)',
        16: '1.',
        17: '... For this reason ...  with (the kni)fe of ... I want to smash (?) into little pieces the false(hood) of the world (at large.)”',
        18: '(Then after) the (ki)ng has (sur)rendered the prince to the Brahmins he sits (sh)aking (with) pa(in).',
        19: '(Thereupon) drag(ging) the prince Uttara [away] by both arms .... the (Bra)hmins (went) out of the palace.',
        20: 'There, looking around helplessly ... Uttara speaks hoarsely (?) with his little tongue .... lamenting:',
        21: 'O Herr, Väterchen! Nimm mich doch von (diesen Rākṣasas) weg!',
        22: '“[My] father, lord, do take me away from (these Rākṣasas)!',
        23: 'O Herr, Väterchen! Nimm mich doch von (diesen Rākṣasas) weg!',
        24: '“[My] father, lord, do take me away from (these Rākṣasas)!',
        25: 'You are still alive, now that these eat me up. (cf 101; 315)',
    }},
    "m-45": {{
        1: '... let sleep over him (?), he slept early. ... dream...',
        2: '... I was deprived... Pradyota seized me... all...',
        3: '... I am falling to (your?) feet. In fear for my life...',
        4: '... dear son, this... is yours. Sāraṇa says...',
        5: 'Then, Kātyāyana...',
        6: '... with the army of four kinds...',
        7: '... I turn... as long as I do not benefit him.',
        8: '... on the feet... here... the Brahmacārin... friend...',
        9: '... was darkness... from... Kātyāyana... his own cell...'
    }}
}}
</fragments>

#### Output
```json
{{
  "1": {{
    "frag_id": "m-a97",
    "relevant_line": "6"
  }},
  "2": {{
    "frag_id": "m-a10",
    "relevant_line": "4"
  }},
  "3": {{
    "frag_id": "m-45",
    "relevant_line": "6"
  }}
}}
```