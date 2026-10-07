import re


def chunk_text(pages: list[dict]) -> list[dict]:
    """
    Create chunks while preserving the page number
    from which each chunk came.
    """

    if not pages:
        raise ValueError("Pages cannot be empty")

    chunks = []

    # Find rules such as R1, R2, ... R12
    rule_pattern = re.compile(
        r"(?<![A-Za-z0-9])R(1[0-2]|[1-9])(?![A-Za-z0-9])",
        re.IGNORECASE,
    )

    for page_data in pages:

        page_number = page_data["page"]
        text = page_data["text"]

        matches = list(rule_pattern.finditer(text))

        # --------------------------------
        # Rule-based chunking
        # --------------------------------
        if matches:

            for i, match in enumerate(matches):

                start = match.start()

                if i + 1 < len(matches):
                    end = matches[i + 1].start()
                else:
                    end = len(text)

                chunk = text[start:end].strip()

                if not chunk:
                    continue

                # Separate reviewer notes
                if "Notes for Reviewers / Agent" in chunk:

                    rule_text, notes = chunk.split(
                        "Notes for Reviewers / Agent",
                        1,
                    )

                    if rule_text.strip():
                        chunks.append(
                            {
                                "page": page_number,
                                "text": rule_text.strip(),
                            }
                        )

                    if notes.strip():
                        chunks.append(
                            {
                                "page": page_number,
                                "text": "NOTES\n" + notes.strip(),
                            }
                        )

                else:
                    chunks.append(
                        {
                            "page": page_number,
                            "text": chunk,
                        }
                    )

        # --------------------------------
        # Fallback chunking
        # --------------------------------
        else:

            lines = [
                line.strip()
                for line in text.split("\n")
                if line.strip()
            ]

            current_chunk = []
            current_length = 0

            for line in lines:

                if (
                    current_length + len(line) > 800
                    and current_chunk
                ):
                    chunks.append(
                        {
                            "page": page_number,
                            "text": "\n".join(current_chunk),
                        }
                    )

                    current_chunk = [line]
                    current_length = len(line)

                else:
                    current_chunk.append(line)
                    current_length += len(line)

            if current_chunk:
                chunks.append(
                    {
                        "page": page_number,
                        "text": "\n".join(current_chunk),
                    }
                )

    return chunks