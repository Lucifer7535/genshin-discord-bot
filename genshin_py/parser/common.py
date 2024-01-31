import re

from bs4 import BeautifulSoup


def parse_html_content(html_text: str, length_limit: int = 500) -> str:
    html_text = html_text.replace('&lt;t class="t_lc"&gt;', "")
    html_text = html_text.replace('&lt;t class="t_gl"&gt;', "")
    html_text = html_text.replace("&lt;/t&gt;", "")

    soup = BeautifulSoup(html_text, features="html.parser")
    url_pattern = re.compile(r"\(\'(https?://.*)\'\)")

    result = ""
    text_length = 0
    for row in soup:
        if text_length > length_limit:
            return result + "..."

        if row.a is not None and (url := url_pattern.search(row.a["href"])):
            result += f"[{row.text}]({url.group(1)})\n"
            text_length += len(row.text)
        elif row.img is not None:
            url = row.img["src"]
            result += f"[>>Image<<]({url})\n"
        elif row.name == "div" and row.table is not None:
            for tr in row.find_all("tr"):
                for td in tr.find_all("td"):
                    result += "· " + td.text + " "
                    text_length += len(td.text)
                result += "\n"
        elif row.name == "ol":
            for i, li in enumerate(row.find_all("li")):
                result += f"{i+1}. {li.text}\n"
                text_length += len(li.text)
        elif row.name == "ul":
            for li in row.find_all("li"):
                result += "· " + li.text + "\n"
                text_length += len(li.text)
        else:
            text = row.text.strip() + "\n"
            result += text
            text_length += len(text)

    return result
