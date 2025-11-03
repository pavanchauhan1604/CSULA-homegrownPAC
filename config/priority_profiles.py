
high_priority_ua2 = {

    "5": {
        "1": "Specifying the PDF/UA version in metadata is fundamental for ensuring that the document can be recognized and properly processed by assistive technologies",
        "2": "Correctly indicating the part number of the PDF/UA standard in the document metadata is crucial for compatibility with assistive technologies, as it informs the technology about the specific version of accessibility standards the document adheres to."

    },
    "8.2.1": {
        "1": "High priority. A properly defined structure hierarchy is essential for accessibility, enabling assistive technologies to understand and navigate the document effectively.",
        "2": "High priority. The presence of a parent entry in structure element dictionaries is crucial for maintaining the document's logical structure, which is vital for accessibility as it ensures that the content can be navigated and understood in its intended order."
    },

    "8.2.2": {
        "1": "High priority. Marking non-essential content as artifacts is fundamental to ensure that screen readers and other assistive technologies can ignore it, focusing on the content that is relevant for understanding the document's purpose and structure."
    },
    "8.2.4": {
        "1": "High priority. Ensuring all structure elements are mapped to standard namespaces is critical for interoperability and accessibility, as it guarantees that the document structure is understood by a wide range of assistive technologies.",
        "4": "High priority. Maintaining standard structure types without improper remapping is essential for ensuring the document's accessibility features are predictable and correctly interpreted by assistive technologies, directly impacting the document's usability."
    },
    "8.2.5.2": {
        "1": "High priority. The presence of a single Document structure element as the sole child of the structure tree root is fundamental for defining the document's overall structure, ensuring that the content is accessible and navigable in a logical and coherent manner.",
        "2": "High priority. Specifying the namespace for the Document structure element as PDF 2.0 ensures compatibility with the latest accessibility standards, directly influencing the document's accessibility and the effectiveness of assistive technologies in interpreting its content."
    },

    "8.2.8.8": {
        "1": "High priority. Ensuring that each table of contents item (TOCI) correctly identifies its reference target is crucial for navigational accessibility, allowing users to understand and interact with the document's structure effectively."
    },

    "8.2.5.14": {
        "2": "High priority. Correct referencing between content and footnotes or endnotes ensures navigational coherence and accessibility, making this rule of high priority for document usability."
    },
    "8.2.5.20": {
        "1": "High priority. Proper enclosure of link annotations within Link or Reference elements is crucial for ensuring that interactive elements are accessible and navigable, directly impacting user experience.",
        "2": "High priority. Separating link annotations targeting different locations into distinct structure elements is vital for clarity and usability, ensuring users can effectively navigate and interact with the document."
    },
    "8.2.5.23": {
        "1": "High priority. Ensuring the correct structure of Ruby annotations is critical for textual clarity and accessibility, particularly for languages where Ruby is used to provide pronunciation guides."
    },
    "8.2.5.24": {
        "1": "High priority. Correct tagging of Warichu content is essential for the accurate representation and accessibility of this specific textual formatting, ensuring that the document is accessible and navigable."
    },
    "8.2.5.25": {
        "2": "High priority. Properly enclosing real content within LI elements in LBody ensures that the list is structured and accessible, crucial for users to understand and navigate list content effectively."
    },
    "8.2.5.26": {
        "1": "High priority. Ensuring tables are regular and cells do not intersect is vital for the readability and navigability of table content, directly affecting the accessibility for users relying on assistive technologies.",
        "2": "High priority. Maintaining regularity in table and row groupings is crucial for ensuring that tables are accessible and easily interpretable by assistive technologies, enhancing the document's overall accessibility.",
        "3": "High priority. Uniformity in the number of columns per row, accounting for column spans, is essential for the structural integrity and accessibility of tables, ensuring content is navigable and understandable.",
        "4": "High priority. Ensuring each row spans the same number of columns is critical for table accessibility, allowing users to accurately interpret and navigate the information presented.",
        "6": "High priority. Providing clear semantic connections between table header cells and other cells is vital for accessibility, ensuring that all users can understand table structure and content relationships."
    },
    "8.2.5.28.2": {
        "1": "High priority. Providing alternate descriptions or replacement text for figures is crucial for making visual content accessible to users who rely on assistive technologies."
    },
    "8.2.5.29": {
        "1": "High priority. Ensuring math content is properly nested within a Formula element is essential for the correct interpretation and accessibility of mathematical expressions."
    },
    "8.4.3": {
        "1": "High priority. Providing ActualText or Alt entries for content using Unicode Private Use Areas (PUA) values is critical to ensure that the content is accessible and understandable, especially for assistive technologies.",
        "2": "High priority. Ensuring the ActualText entry is free of Private Use Area (PUA) values is essential for the accurate and accessible representation of text to all users, including those using assistive technologies.",
        "3": "High priority. Avoiding Private Use Area (PUA) values in the Alt entry is crucial to ensure that alternate text descriptions are universally interpretable and accessible."
    },
    "8.4.4": {
        "1": "High priority. Specifying the default natural language in the document's catalog is essential for text interpretation and accessibility, enabling assistive technologies to provide appropriate language support.",
        "2": "High priority. Using proper language identifiers ensures that language-specific content is correctly processed and interpreted by assistive technologies, significantly impacting accessibility."
    },
    "8.4.5.3.2": {
        "1": "High priority. The presence and correctness of the CIDToGIDMap entry in Type 2 CIDFonts are crucial for accurate glyph mapping, directly affecting text rendering and accessibility."
    },
    "8.4.5.4": {
        "1": "High priority. Embedding CMaps not listed in the standard table ensures that all character mappings are available within the file, crucial for the accurate rendering and accessibility of text content.",
        "2": "High priority. Consistency between WMode values in the CMap dictionary and embedded CMap stream affects text rendering direction, impacting readability but not directly hindering accessibility.",
        "3": "High priority. Restricting CMap references to those listed in the standard ensures that character mappings are universally recognized and accessible, critical for text rendering and accessibility."
    },
    "8.4.5.5.1": {
        "1": "High priority. Embedding font programs is essential for ensuring that text is accurately rendered and accessible across different platforms and devices, a fundamental aspect of document accessibility.",
        "2": "High priority. Ensuring all referenced glyphs are defined in embedded fonts is critical for accurate text rendering, crucial for readability and accessibility, except in cases where text is used solely for non-visual purposes (rendering mode 3)."
    },
    "8.4.5.6": {
        "1": "High priority. Consistency between glyph width information in the font dictionary and the embedded font program is essential for correct text layout and rendering, directly impacting the document's readability and accessibility."
    },
    "8.4.5.7": {
        "1": "High priority. Including specific 'cmap' subtables in TrueType fonts is crucial for ensuring that the font can be accurately mapped and rendered across different systems, directly affecting text accessibility.",
        "2": "High priority. Adhering to specific encoding standards and ensuring glyph names in Differences arrays align with the Adobe Glyph List are critical for text interpretability and rendering accuracy, impacting accessibility.",
        "4": "High priority. Including specific 'cmap' encodings in symbolic TrueType fonts ensures that the font's symbols are accurately mapped and accessible, crucial for the font's correct use and rendering in documents."
    },
    "8.4.5.8": {
        "1": "High priority. Defining a map to Unicode values for all character codes in fonts is crucial for text extraction and accessibility, enabling content to be accurately interpreted by assistive technologies.",
        "2": "High priority. Ensuring Unicode values specified by ToUnicode CMaps are valid and not reserved characters is essential for the correct interpretation and processing of text, affecting accessibility and text extraction accuracy."
    },
    "8.4.5.9": {
        "1": "High priority. Avoiding references to the .notdef glyph is crucial for ensuring all text is intentionally represented and accessible, as references to this glyph indicate missing or unrecognized characters, directly impacting readability and accessibility."
    },
    "8.5.1": {
        "1": "High priority. Enclosing non-textual content within Figure or Formula elements, when it lacks alternate textual representation, is essential for accessibility, ensuring all content is perceivable and navigable."
    },
    "8.6": {
        "1": "High priority. Avoiding Unicode Private Use Areas (PUA) in human-readable text ensures the content is universally accessible and interpretable, enhancing document accessibility and compatibility."
    },
    "8.7": {
        "1": "High priority. Ensuring that all optional content configuration dictionaries have a non-empty Name entry is crucial for document structure clarity and user interaction, facilitating accessibility and document navigation."
    },
    "8.8": {
        "1": "High priority. Using structure destinations for internal document targets is essential for ensuring that navigation is compatible with accessibility requirements, facilitating better document usability for all users.",
        "2": "High priority. Ensuring GoTo actions target structure destinations within the document is crucial for accessibility, allowing for meaningful navigation that supports assistive technologies."
    },
    "8.9.2.1": {
        "1": "High priority. Incorporating annotations into the structure tree enhances document navigation and accessibility, ensuring that all interactive and annotative elements are accessible to users with disabilities, except where specific exceptions apply."
    },
    "8.9.2.3": {
        "1": "High priority. Enclosing markup annotations within Annot structure elements is essential for ensuring that annotations are properly recognized and accessible within the document's structure, facilitating interaction and accessibility.",
        "2": "High priority. Ensuring textual equivalence between RC and Contents entries in markup annotations aids in maintaining consistency and clarity in annotation content, impacting document usability and accessibility."
    },
    "8.9.2.4.8": {
        "1": "High priority. Including a Contents entry for Ink annotations is crucial to communicate the author's intent, directly impacting the clarity and accessibility of annotated content for all users."
    },
    "8.9.2.4.9": {
        "1": "High priority. Excluding Popup annotations from the structure tree aligns with accessibility guidelines, ensuring that non-essential, interactive elements do not disrupt the document's accessible navigation."
    },
    "8.9.2.4.10": {
        "1": "High priority. Including an AFRelationship entry in file specification dictionaries referenced by file attachment annotations is crucial for defining the relationship of the attached file to the document content, affecting document integrity and accessibility."
    },
    "8.9.2.4.11": {
        "1": "High priority. The prohibition of Sound annotations in documents conforming to PDF/UA-2 ensures compatibility with accessibility standards, as these annotations may not be accessible or interpretable by all users.",
        "2": "High priority. Excluding Movie annotations from PDF/UA-2 conforming documents ensures that all content is accessible and compatible with accessibility standards, avoiding reliance on multimedia content that may not be fully accessible."
    },
    "8.9.2.4.12": {
        "1": "High priority. Requiring a Contents entry for Screen annotations is crucial for providing textual descriptions of the annotation's function or content, enhancing accessibility for users relying on assistive technologies."
    },
    "8.9.2.4.13": {
        "1": "High priority. Ensuring that zero-height and zero-width widget annotations are marked as artifacts is essential for correctly interpreting their role and preventing them from affecting layout or rendering."
    },
    "8.9.2.4.14": {
        "1": "High priority. Ensuring that printer's mark annotations are marked as artifacts is essential for correctly interpreting their role and preventing them from affecting layout or rendering."
    },
    "8.9.2.4.15": {
        "1": "High priority. Ensuring that trap network annotations are not used is crucial for PDF/UA-2 conformance, as they may not be supported by all viewers and could lead to accessibility issues."
    },
    "8.9.2.4.16": {
        "1": "High priority. Ensuring that Watermark annotations are enclosed within Annot structure elements when used as real content is important for maintaining the document's structural integrity and accessibility."
    },
    "8.9.3.3": {
        "1": "High priority. The presence of the Tabs entry in the page dictionary ensures proper navigation and accessibility for users relying on assistive technologies. Without it, users may encounter difficulties in navigating the document effectively."
    },
    "8.10.1": {
        "1": "High priority. Ensuring that each widget annotation is enclosed by a Form structure element is crucial for proper accessibility. Form structure elements provide logical grouping for form fields, which is essential for assistive technologies to interpret the content correctly.",
        "3": "High priority. XFA forms are not supported in PDF/UA documents and can cause accessibility issues. Their presence can lead to incorrect or incomplete rendering of form fields and their associated labels, instructions, and actions by assistive technologies."
    },
    "8.10.3.3": {
        "1": "High priority. Ensuring the presence and equivalence of RV and V entries for text fields is crucial for accessibility. These entries provide users with disabilities with the text content of the field, allowing screen readers and other assistive technologies to properly convey the information contained within the text field."
    },
    "8.11.1": {
        "1": "High priority. The dc:title entry in the Metadata stream provides important metadata about the document, including its title. This information is crucial for accessibility tools and users to understand the content and purpose of the document."
    }


}

medium_priority_ua2 = {

    "5": {
        "3": "Specifying the PDF/UA version in metadata is fundamental for ensuring that the document can be recognized and properly processed by assistive technologies",
        "4": "Similar to the 'part' property's namespace prefix, the correct namespace for the 'rev' property ensures technical compliance and aids in metadata processing, but its direct impact on accessibility for end users is less immediate.",
        "5": "Ensuring the 'rev' property is a four-digit year is important for document version control and standards compliance, but it has a secondary impact on the practical accessibility of the document's content for users with disabilities."
    },
    "8.2.4": {
        "2": "While circular mappings can complicate the document's structure and processing, they primarily affect the document's technical integrity rather than directly impacting the user's ability to access content.",
        "3": "Role mapping within the same namespace could lead to confusion in document structure interpretation but is less critical to immediate accessibility concerns like document navigation or content understanding by assistive technologies."
    },
    "8.2.5.14": {
        "1": "Restricting the Note structure type unless role-mapped correctly helps maintain standardized document structure, affecting accessibility with medium impact.",
        "3": "Ensuring the NoteType attribute is correctly set facilitates the proper identification and processing of notes, impacting document structure clarity but with a moderate direct effect on accessibility."
    },
    "8.2.5.20": {
        "3": "Grouping multiple link annotations targeting the same location enhances document navigation efficiency, but this issue has a moderate impact compared to the direct accessibility of content."
    },
    "8.2.5.25": {
        "1": "Including the ListNumbering attribute when Lbl elements are used enhances list structure clarity, but its absence primarily affects document semantic structure rather than direct accessibility."
    },
    "8.2.5.27": {
        "1": "Correct placement of the Caption element enhances document structure understanding, but its positioning has a moderate impact on the overall document accessibility."
    },
    "8.4.5.3.1": {
        "1": "Ensuring compatibility between CIDSystemInfo entries and Encoding dictionaries in Type 0 fonts supports proper character mapping and rendering, affecting document readability and accessibility indirectly."
    },
    "8.4.5.7": {
        "3": "For symbolic TrueType fonts, omitting the Encoding entry avoids conflicts in character mapping, affecting technical compliance more than direct accessibility."
    },
    "8.7": {
        "2": "Omitting the AS key from optional content configuration dictionaries adheres to specification requirements, impacting document technical compliance rather than direct accessibility."
    },
    "8.9.2.2": {
        "1": "Making invisible annotations artifacts ensures they do not interfere with the document's accessible structure or navigation, aligning with accessibility best practices for non-visual content.",
        "2": "Treating annotations with NoView flags as artifacts, unless ToggleNoView is set, helps maintain the document's accessibility by excluding non-viewable content from the structure tree, aligning with accessibility guidelines."
    },
    "8.9.2.4.7": {
        "1": "Providing a Contents entry for rubber stamp annotations when the Name entry is not descriptive enough ensures that the annotation's intent is clear, enhancing document communication and accessibility"
    },
    "8.9.2.4.19": {
        "1": "Ensuring that 3D annotations include alternate descriptions in the Contents entry is important for accessibility purposes, allowing users with disabilities to understand the content of the annotation",
        "2": "Medium priority. Providing alternate descriptions for RichMedia annotations enhances accessibility by enabling users who cannot access the media content to understand its purpose and context"

    },
    "8.9.4.2": {
        "1": "Medium priority. Ensuring consistency between the Contents and Alt entries is important for accessibility as it provides alternative text for annotations. Inconsistencies could lead to confusion for users relying on assistive technologies.",

    },
    "8.10.1": {
        "2": "Medium priority. While it is important for a Form structure element to contain only one widget annotation for proper organization and clarity, having more than one widget annotation does not necessarily hinder accessibility. However, it can potentially confuse assistive technologies and users if there are multiple form fields within a single Form structure element."
    },
    "8.10.2.3": {
        "1": "Medium priority. Providing either a label or a Contents entry for a widget annotation enhances accessibility by offering users with disabilities meaningful information about the purpose and function of the annotation. Lack of such information can hinder their ability to interact with the document effectively.",
        "2": "Medium priority. Ensuring the presence of a Contents entry for a widget annotation with an additional action (AA) enhances accessibility by providing users with disabilities with information about the action associated with the widget. Lack of such information can make it difficult for users to understand the purpose and function of the widget."
    },
    "8.10.3.5": {
        "1":"Medium priority. Providing alternative text for graphics representing portions of signatures is important for accessibility, especially for individuals who rely on screen readers. However, the impact may vary depending on the context and importance of the signature within the document."
    },
    "8.11.2": {
        "1": "Medium priority. The presence of the ViewerPreferences dictionary with the DisplayDocTitle key set to true ensures that the document's title is displayed when the document is opened, which can enhance accessibility by providing users with important information about the document."
    },
    "8.14.1": {
        "1": "Medium priority. The Desc entry provides a textual description of the embedded file, which can be crucial for accessibility purposes. Its absence may hinder users who rely on assistive technologies to access and understand the content of the embedded file."
    }



}


low_priority_ua2 = {

    "8.2.5.12": {
        "1": "While using the H structure type goes against specific guidelines, its impact on accessibility might be less direct compared to issues that affect document navigation or content interpretation. The priority might vary based on the context of how H structure types are used within the document."
    }


}

