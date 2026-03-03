from pyexpat import ExpatError
from lxml import etree
import xmltodict as xd
from copy import deepcopy


class Transcription():
    def __init__(
        self,
        transcription: etree._ElementTree,
        ns: dict[str, str] = {"tei": "http://www.tei-c.org/ns/1.0"}
    ) -> None:
        self.transcription_element = transcription
        self.ns_full = ns
        self.ns = ns["tei"]
        self.transcription_list = self.create_transcription_list()
        self.split_translation_grammer()
        self.lines = self.create_lines_dict()

    def extract_tag_lg(
        self,
        outer_element: etree._Element
    ) -> list[list[dict]]:
        """
        Takes an element and extract the information from the 'l' tag.

        Args:
            out_element(etree._Element): Element with an 'lg' tag.

        Returns:
            list[list[dict]]: Extracted words.
        """
        inner_element = outer_element.xpath(
            f'./tei:lg[@type="strophe"]',
            namespaces=self.ns_full
        )[0]

        lines = inner_element.xpath(f'./tei:l', namespaces=self.ns_full)
        line_list = []
        for line in lines:
            line_temp = []
            for child in line.getchildren():
                for child_of_child in child.getchildren():
                    line_temp.append(
                        xd.parse(etree.tostring(child_of_child).decode())
                    )
            line_list.append(line_temp)

        return line_list

    def extract_tag_s(
        self,
        outer_element: etree._Element
    ) -> list[list[dict]]:
        """
        Takes an element and extract the information from the 's' tag.

        Args:
            out_element(etree._Element): Element with an 's' tag.

        Returns:
            list[list[dict]]: Extracted words.
        """
        s_tags = outer_element.xpath(f'./tei:s', namespaces=self.ns_full)
        all_s = []
        for inner_element in s_tags:
            temp = []
            for child in inner_element.getchildren():
                if child.tag == f"{{{self.ns}}}s":
                    for inner_child in child.getchildren():
                        temp.append(
                            xd.parse(etree.tostring(inner_child).decode())
                        )
                else:
                    temp.append(xd.parse(etree.tostring(child).decode()))
            all_s.append(temp)

        return all_s

    def extract_tag_fw(
        self,
        outer_element: etree._Element
    ) -> dict[str, str]:
        """
        Takes an element and extract the information from the 'fw' tag.

        Args:
            out_element(etree._Element): Element with an 's' tag.

        Returns:
            dict[str, str]: Extracted words.
        """
        fw_dict = dict(outer_element.attrib)
        temp = outer_element.xpath('./tei:num', namespaces=self.ns_full)
        if temp:
            fw_dict["num"] = temp[0].text
        fw_dict["num"] = ""

        return fw_dict

    def create_transcription_list(self) -> list[dict]:
        """
        Takes the transcription XML tree and returns an ordered list
        of each child element.

        Args:
            None.

        Returns:
            list[dict]: A list of dict describing the transcription
        """
        # TODO: Schau ob es wirklich nur diese Tags sind
        transcription_list = []

        try:
            for outer_element in self.transcription_element.getchildren():
                if outer_element.tag == f"{{{self.ns}}}lg":
                    transcription_list.append(
                        {"lg": self.extract_tag_lg(outer_element=outer_element)}
                    )
                elif outer_element.tag == f"{{{self.ns}}}p":
                    #if outer_element.xpath('./tei:milestone', namespace=self.ns_full):
                    #    continue
                    transcription_list.append(
                        {"p": self.extract_tag_s(outer_element=outer_element)}
                    )
                elif outer_element.tag == f"{{{self.ns}}}fw":
                    transcription_list.append(
                        {"fw": self.extract_tag_fw(outer_element=outer_element)}
                    )
        except ExpatError as e:
            # print(f"Transcription loading error: {e}")
            pass

        return transcription_list

    def split_translation_grammer(self) -> None:
        should_modify = ("lg", "p")
        for idx, element in enumerate(self.transcription_list):
            if any(tag in element for tag in should_modify):
                key = next(iter(element))
                for line in element[key]:
                    for wi, word_wrapper in enumerate(line):
                        if "w" not in word_wrapper or isinstance(word_wrapper["w"], str):
                            continue

                        w = word_wrapper["w"]
                        # pull through your core attributes every time:
                        base = {k: v for k, v in w.items() if k in ("#text","@corresp","lb","supplied")}

                        if "@n" in w:
                            parts = w["@n"].split("\n")
                            # split into translation vs grammar
                            translation = ",".join(p for p in parts if p.startswith("“"))
                            grammar     = ",".join(p for p in parts if not p.startswith("“"))
                            base["translation"] = translation
                            base["grammar_info"] = grammar
                        else:
                            base["translation"] = ""
                            base["grammar_info"] = ""

                        # write _only_ base back
                        line[wi] = base

        # no need to reassign self.transcription_list; we mutated in place

    def create_lines_dict(self) -> dict[str, list[dict]]:
        lines = {}
        current_line = None

        for element in self.transcription_list:
            key = next(iter(element))
            if key == "fw":
                continue

            for word_list in element[key]:
                for word in word_list:
                    # if this word carries an explicit lb, start a new line
                    if "lb" in word and word["lb"] is not None:
                        try:
                            current_line = word["lb"]["@corresp"]
                            lines.setdefault(current_line, [])
                        except KeyError:
                            continue

                    # if we’ve never seen any lb yet, skip until the first one
                    if current_line is None:
                        continue

                    # append _every_ word (lb-bearing or not) to the active line
                    lines[current_line].append(word)

        return lines


class Translation():
    def __init__(
        self,
        translation: etree._ElementTree
    ) -> None:
        self.translation_element = translation
        self.line_translation = self.create_translation_list()

    def create_translation_list(self):
        """
        Creates a list of the translation plus its sources for
        the lines in the document

        Args:
            None.

        Returns:
            list[dict]: List of translations and their sources.
        """
        dict_collection = []
        for outer_seg in self.translation_element.getchildren()[0]:
            temp_list = []
            for inner_seg in outer_seg.getchildren():
                temp_list.append(xd.parse(etree.tostring(inner_seg).decode()))

            correspond_temp = outer_seg.attrib["corresp"]
            dict_temp = {outer_seg.attrib["corresp"]: {
                "correspond_to_lines": correspond_temp.split(" "),
                "translation": temp_list
            }
            }
            dict_collection.append(dict_temp)

        return dict_collection


class Fragment():
    def __init__(
        self,
        fragment_xml: etree._Element,
        ns: dict[str, str] = {"tei": "http://www.tei-c.org/ns/1.0"}
    ) -> None:
        self.root = fragment_xml  # self.tree.getroot()
        self.ns = ns
        self.meta_data = self.get_fragment_metadata()
        self.transcription = self.return_transcription()
        self.translation = self.return_translation()

    def return_transcription(self) -> Transcription | None:
        """
        Returns the transcription if not empty, otherwise None

        Args:
            None

        Returns:
            Transcription | None: Transcription if not empty,
            otherwise None
        """
        path = ".//tei:text/tei:body/tei:div[@type='transcription']"
        if self.root.find(
            path,
            namespaces=self.ns
        ) is not None:
            return Transcription(
                self.root.find(
                    path,
                    namespaces=self.ns
                )
            )
        else:
            return None

    def return_translation(self) -> Translation | None:
        """
        Returns the translation if not empty, otherwise None

        Args:
            None

        Returns:
            Translation | None: Translation if not empty,
            otherwise None
        """
        path = ".//tei:text/tei:body/tei:div[@type='translation']"
        if self.root.find(
            path,
            namespaces=self.ns
        ) is not None:
            return Translation(
                self.root.find(
                    path,
                    namespaces=self.ns
                )
            )
        else:
            return None

    def get_fragment_metadata(self) -> dict:
        """
        Returns a dict containing metadata about the fragment.

        Args:
            None.

        Returns:
            dict: Dict containing the metadata.
        """
        metadata = {}
        metadata["frag_id"] = self.root.attrib[
            '{http://www.w3.org/XML/1998/namespace}id'
        ]
        metadata["frag_next"] = self.root.attrib.get("next")
        metadata["frag_prev"] = self.root.attrib.get("prev")
        fileDesc = self.root.find(
            ".//tei:teiHeader/tei:fileDesc",
            namespaces=self.ns
        )
        titleStmt = fileDesc.find(
            "tei:titleStmt",
            namespaces=self.ns
        )

        metadata["title"] = titleStmt.find(
            "tei:title",
            namespaces=self.ns
        ).text

        if titleStmt.find("tei:respStmt", namespaces=self.ns) is not None:
            respStmt = titleStmt.find("tei:respStmt", namespaces=self.ns)
            metadata["respStmt"] = {}
            if respStmt.find("tei:resp", namespaces=self.ns) is not None:
                metadata["respStmt"]["resp"] = respStmt.find(
                    "tei:resp",
                    namespaces=self.ns
                ).text
            if respStmt.find("tei:name", namespaces=self.ns) is not None:
                metadata["respStmt"]["name"] = respStmt.find(
                    "tei:name",
                    namespaces=self.ns
                ).text

        publicationStmt = fileDesc.find(
            "tei:publicationStmt",
            namespaces=self.ns
        )
        metadata["publisher"] = publicationStmt.find(
            "tei:publisher",
            namespaces=self.ns
        ).text
        metadata["public"] = publicationStmt.\
            find("tei:availability", namespaces=self.ns).\
            find("tei:p", namespaces=self.ns).text

        msDesc = fileDesc.find("tei:sourceDesc", namespaces=self.ns).\
            find("tei:msDesc", namespaces=self.ns)
        msIdentifier = msDesc.find("tei:msIdentifier", namespaces=self.ns)

        metadata["msIdentifier"] = {}
        if msIdentifier.find("tei:repository", namespaces=self.ns) is not None:
            metadata["msIdentifier"]["repository"] = (
                msIdentifier.find("tei:repository", namespaces=self.ns).text
            )
        if msIdentifier.find("tei:idno", namespaces=self.ns) is not None:
            metadata["msIdentifier"]["idno"] = (
                msIdentifier.find("tei:idno", namespaces=self.ns).text
            )
        if msIdentifier.find(
            "tei:altIdentifier",
            namespaces=self.ns
        ) is not None:
            if msIdentifier.find(
                "tei:altIdentifier", namespaces=self.ns
            ).find("tei:idno", namespaces=self.ns) is not None:
                metadata["msIdentifier"]["altIdentifier"] = msIdentifier.\
                    find("tei:altIdentifier", namespaces=self.ns).\
                    find("tei:idno", namespaces=self.ns).text
        if "altIdentifier" not in metadata["msIdentifier"]:
            metadata["msIdentifier"]["altIdentifier"] = None
        if msIdentifier.find("tei:msName", namespaces=self.ns) is not None:
            metadata["msIdentifier"]["msName"] = (
                msIdentifier.find("tei:msName", namespaces=self.ns).text
            )

        if msDesc.find("tei:msContents", namespaces=self.ns) is not None:
            metadata["title"] = (
                msDesc.find("tei:msContents", namespaces=self.ns).
                find("tei:msItem", namespaces=self.ns).
                find("tei:title", namespaces=self.ns).text
            )

        physDesc = msDesc.find("tei:physDesc", namespaces=self.ns)
        if physDesc is not None:
            objectDesc = physDesc.find(
                "tei:objectDesc",
                namespaces=self.ns
            )
            if objectDesc is not None:
                supportDesc = objectDesc.find(
                    "tei:supportDesc",
                    namespaces=self.ns
                )
                support = supportDesc.find(
                    "tei:support",
                    namespaces=self.ns
                )
                metadata["support"] = {}

                extent = supportDesc.find(
                    "tei:extent",
                    namespaces=self.ns
                )
                if extent is not None:
                    dimension = extent.find(
                        "tei:dimensions",
                        namespaces=self.ns
                    )
                    height = dimension.find(
                        "tei:height",
                        namespaces=self.ns
                    )
                    width = dimension.find(
                        "tei:width",
                        namespaces=self.ns
                    )
                    height = height.text if height is not None else None
                    width = width.text if width is not None else None
                    metadata["support"]["dimensions"] = {
                        "unit": dimension.attrib["unit"],
                        "height": height,
                        "width": width
                    }
                if support is not None:
                    material = support.find(
                        "tei:material",
                        namespaces=self.ns
                    )

                    objectType = support.find(
                        "tei:objectType",
                        namespaces=self.ns
                    )
                    if material is not None:
                        metadata["support"]["material"] = (
                            material.text
                        )
                    if objectType is not None:
                        metadata["support"]["objectType"] = (
                            support.find(
                                "tei:objectType",
                                namespaces=self.ns
                            ).text
                        )

                if objectDesc.find(
                    "tei:layoutDesc", namespaces=self.ns
                ) is not None:
                    metadata["layout"] = {}
                    layout = objectDesc.\
                        find("tei:layoutDesc", namespaces=self.ns).\
                        find("tei:layout", namespaces=self.ns)
                    measure = layout.find("tei:measure", namespaces=self.ns)
                    if measure is not None:
                        metadata["layout"]["measure"] = {
                            measure.attrib["type"]: measure.text
                        }
                    dimensions = layout.find(
                        "tei:dimensions",
                        namespaces=self.ns
                    )
                    if dimensions is not None:
                        temp_dict = dimensions.attrib
                        height = dimensions.find(
                            "tei:height",
                            namespaces=self.ns
                        )
                        if height is not None:
                            temp_dict["height"] = height.text
                        metadata["layout"]["dimensions"] = temp_dict

            if physDesc.find("tei:handDesc", namespaces=self.ns) is not None:
                handNote = physDesc.\
                    find("tei:handDesc", namespaces=self.ns).\
                    find("tei:handNote", namespaces=self.ns)
                metadata["handDesc"] = {}
                metadata["handDesc"]["handNote"] = handNote.attrib
            if physDesc.find("tei:scriptDesc", namespaces=self.ns) is not None:
                scriptNote = physDesc.\
                    find("tei:scriptDesc", namespaces=self.ns).\
                    find("tei:scriptNote", namespaces=self.ns)
                metadata["scriptDesc"] = {}
                metadata["scriptDesc"]["scriptNote"] = scriptNote.text

        history = msDesc.find("tei:history", namespaces=self.ns)
        if history is not None:
            provenance = history.find("tei:provenance", namespaces=self.ns)
            metadata["provenance"] = {}
            try:
                metadata["provenance"]["region"] = (
                    provenance.find("tei:region", namespaces=self.ns).text
                )
            except AttributeError:
                metadata["provenance"]["region"] = None
            try:
                metadata["provenance"]["placeName"] = (
                    provenance.find("tei:placeName", namespaces=self.ns).text
                )
            except AttributeError:
                metadata["provenance"]["placeName"] = None
            try:
                metadata["provenance"]["expedition_code"] = (
                    provenance.find("tei:rs", namespaces=self.ns).text
                )
            except AttributeError:
                metadata["provenance"]["expedition_code"] = None

        profileDesc = self.root.find(
            ".//tei:teiHeader/tei:profileDesc",
            namespaces=self.ns
        )
        if profileDesc is not None:
            metadata["profileDesc"] = {}
            textClass = profileDesc.find("tei:textClass", namespaces=self.ns)
            if textClass is not None:
                keywords = profileDesc.\
                    find("tei:textClass", namespaces=self.ns).\
                    find("tei:keywords", namespaces=self.ns)
                for child in keywords.getchildren():
                    if child.attrib["type"] not in metadata["profileDesc"]:
                        metadata["profileDesc"][child.attrib["type"]] = (
                            child.text
                        )
                    else:
                        metadata["profileDesc"][child.attrib["type"]] += (
                            f", {child.text}"
                        )
                if "genre" not in metadata["profileDesc"]:
                    metadata["profileDesc"]["genre"] = None
                if "subgenre" not in metadata["profileDesc"]:
                    metadata["profileDesc"]["subgenre"] = None
            langUsage = profileDesc.find("tei:langUsage", namespaces=self.ns)
            langUsage_dict = {}
            for child in langUsage.getchildren():
                ident = child.attrib["ident"]
                langUsage_dict[ident] = {}
                for note in child.getchildren():
                    langUsage_dict[ident][note.text] = note.attrib
                note = child.find("tei:note", namespaces=self.ns)
                if note is not None:
                    for note_child in note.getchildren():
                        langUsage_dict[ident][note_child.text]

            metadata["langUsage"] = langUsage_dict

        return metadata

