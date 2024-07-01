"""
1. xelatex으로 직접 compile 하는 옵션을 선택하면, 실제론 2번 compile 하게 되어 있음
    이건 hyperref가 한번의 compile로는 제대로 적용되지 않는 경우가 있기 때문

2. 여러 파일들이 상호 참조하는 경우 아래처럼 설정되어야 함.
    1. tex 파일과 pdf 파일이 모두 같은 폴더에 생성되도록 할 것 (md_path만 제공하면 자동으로 그리 됨)
    2. 모든 파일을 2번씩 export 할 것
        각 파일을 순차적으로 1번씩 export 하고, 그 이후 다시 1번씩 export 하면 됨.
        상호 참조는 참조 당하는 파일이 compile 시점에 이미 존재해야 정상적으로 기능하기 때문임.
        따라서, 정확히는 더 적게 export 해도 되나, 굳이 그걸 판단하게 하고 싶지 않음.

    만약 에러가 발생하는 경우
    1. 실제 Obsidian link 자체가 잘못된 경우
        Link를 생성한 이후, link의 target을 수정한 경우 (우클릭해서 다같이 수정 뭐 이런거 있음. 그거 안쓰고 걍 수정한 경우)
        link가 깨지게 됨. Obsidian은 적당히 파일까지만 쫓아가거나, 파일 이름이 바뀌었으면 같은 이름의 파일을 생성해서 이동함.
        그래서 link가 깨졌는지 모르고 지나쳤을 수 있으니, 다시한번 확인해보시길
    2. henrik@unist.ac.kr 로 보고
"""
import re
import sys
import subprocess
from pathlib import Path
from itertools import pairwise


CALLOUT_COLORS = {
    "note": "cyan",
    "info": "cyan",
    "todo": "cyan",

    "abstract": "teal",
    "summary": "teal",
    "tldr": "teal",

    "tip": "magenta",
    "hint": "magenta",
    "important": "magenta",

    "success": "green",
    "check": "green",
    "done": "green",

    "question": "orange",
    "help": "orange",
    "faq": "orange",
    "warning": "orange",
    "caution": "orange",
    "attention": "orange",

    "failure": "red",
    "fail": "red",
    "missing": "red",
    "danger": "red",
    "error": "red",
    "bug": "red",

    "example": "purple",
    "quote": "lightgray",
    "cite": "lightgray",
}


class MdConvert:
    EXPORT_PATH = Path(".exported")  # cwd가 Vault 바닥이라고 가정
    IMG_PATH = Path("Attached_Files")  # cwd가 Vault 바닥이라고 가정
    PREAMBLE_PATH = Path("_others/preamble.tex")

    # =========================================================
    # ==================== Initial Set-ups ====================
    # =========================================================
    def __init__(self, md_path=None, temp_path=None, tex_path=None, pdf_path=None):
        self.md_path, self.temp_path, self.tex_path, self.pdf_path = (md_path, temp_path, tex_path, pdf_path)
        self._set_default_paths()

        with open(self.md_path, 'r', encoding='UTF-8') as file:
            self.lines = file.readlines()
        # file.readlines() 하면 각 원소 끝에 \n가 살아있고
        # file.read().splitlines() 하면 \n가 없고
        # file.read().splitlines(keepends=True) 하면 \n가 살아있음

        self.tex_full = ''

    def _set_default_paths(self):
        if self.md_path is None:
            if not (path := Path(sys.argv[-1])).exists():
                raise ValueError(f"{path} not found. Either 1) Correct sys.argv[-1] or 2) give md_path")
            self.md_path = path
        else:
            self.md_path = Path(self.md_path)

        if self.temp_path is None:
            if not self.EXPORT_PATH.exists():
                raise ValueError(f"{self.EXPORT_PATH} not found. Either 1) Correct the path or 2) give temp_path")
            self.temp_path = self.EXPORT_PATH / self.md_path.with_suffix(f'.temp.md').name
        else:
            self.temp_path = Path(self.temp_path)

        if self.tex_path is None:
            self.tex_path = self.temp_path.with_suffix('').with_suffix('.tex')
        else:
            self.tex_path = Path(self.tex_path)

        if self.pdf_path is None:
            self.pdf_path = self.temp_path.with_suffix('').with_suffix('.pdf')
        else:
            self.pdf_path = Path(self.pdf_path)

    # ==================================================
    # ==================== Converts ====================
    # ==================================================
    def convert(self):
        self.\
            convert_callouts().\
            convert_images().\
            strict_line_break().\
            no_empty_lines_in_math_blocks().\
            no_redundant_double_dollars()
        return self

    def convert_callouts(self):
        self.lines = convert_callouts(self.lines)
        return self

    def convert_images(self):
        self.lines = convert_images(self.lines, self.IMG_PATH.absolute())
        return self

    def strict_line_break(self):
        self.lines = strict_line_break(self.lines)
        return self

    def no_empty_lines_in_math_blocks(self):
        self.lines = no_empty_lines_in_math_blocks(self.lines)
        return self

    def no_redundant_double_dollars(self):
        self.lines = no_redundant_double_dollars(self.lines)
        return self

    # =====================================================
    # ==================== TeX Restyle ====================
    # =====================================================

    def restyle_tex(self):
        with open(self.tex_path, 'r', encoding='UTF-8') as file:
            self.tex_full = file.read()

        self.\
            full_horizontal_rules().\
            convert_footnotes().\
            convert_links().\
            convert_block_identifier().\
            comment_out_default_fonts()

        with open(self.tex_path, 'w', encoding='UTF-8') as file:
            file.write(self.tex_full)
        return self

    def full_horizontal_rules(self):
        self.tex_full = full_horizontal_rules(self.tex_full)
        return self

    def convert_footnotes(self):
        self.tex_full = convert_footnotes(self.tex_full)
        return self

    def comment_out_default_fonts(self):
        self.tex_full = comment_out_default_fonts(self.tex_full)
        return self

    def convert_links(self):
        self.tex_full = convert_links(self.tex_full, self.tex_path)
        return self

    def convert_block_identifier(self):
        self.tex_full = convert_block_identifier(self.tex_full)
        return self

    # =================================================
    # ==================== Exports ====================
    # =================================================
    def export(self, method='xelatex', verbose=False):
        if method == 'xelatex':
            self.\
                export_temp().\
                export_tex().\
                restyle_tex().\
                export_pdf_xelatex(verbose=verbose).\
                export_pdf_xelatex(verbose=verbose)
        else:
            self.\
                export_temp().\
                export_tex().\
                export_pdf_pandoc()
        return self

    def export_temp(self):
        with open(self.temp_path, 'w', encoding='UTF-8') as file:
            file.writelines(self.lines)
        print(f"Created {self.temp_path}")
        return self

    def export_tex(self):
        cmd = ['pandoc', str(self.temp_path.absolute()),
               '-s',
               '-o', str(self.tex_path),
               '-V', 'geometry:margin=0.5in',
               '-H', self.PREAMBLE_PATH.absolute().as_posix(),
               '--pdf-engine=' + 'xelatex']
        try:
            subprocess.call(cmd)
        except Exception as e:
            raise e
        else:
            print(f"Created {self.tex_path}")
        return self

    def export_pdf_pandoc(self):
        cmd = ['pandoc', str(self.temp_path.absolute()),
               '-o', str(self.pdf_path),
               '-V', 'geometry:margin=0.5in',
               '-H', 'preamble.tex',
               '--pdf-engine=' + 'xelatex']
        try:
            subprocess.call(cmd, stdout=subprocess.DEVNULL)
        except Exception as e:
            raise e
        else:
            print(f"Created {self.pdf_path}")
        return self

    def export_pdf_xelatex(self, verbose=False):
        cmd = ['xelatex',
               '-output-directory=' + self.pdf_path.parent.absolute().as_posix(),
               '-jobname=' + self.pdf_path.stem,
               self.tex_path.absolute().as_posix(),]
        try:
            stdout = None if verbose else subprocess.DEVNULL
            subprocess.call(cmd, stdout=stdout)
        except Exception as e:
            raise e
        else:
            print(f"Created {self.pdf_path}")
        return self


def count_depth(x: str, marker: str):
    depth = 0
    while x.startswith(marker, len(marker)*depth):
        depth += 1
    return depth


def line_type(line: str):
    q = re.search(r'^(\s*)(\d+\.)|^(\s*)([+-] )|^(#+)|^(\s*)$|^(---)|^(___)|^(\^[a-zA-Z\-0-9]+)', line)
    if not q:
        return "O"  # Others
    x = q.groups()
    if isinstance(x[0], str) and isinstance(x[1], str):
        return "L" if not x[0] else "IL"  # List or Indented List
    elif isinstance(x[2], str) and isinstance(x[3], str):
        return "L" if not x[2] else "IL"  # bulleted List or Indented bulleted List
    elif isinstance(x[4], str):
        return "H"  # Headings
    elif isinstance(x[5], str):
        return "E"  # Empty line
    elif isinstance(x[6], str) or isinstance(x[7], str):
        return "HR"  # Horizontal rule
    elif isinstance(x[8], str):
        return "BI"  # Block Identifier
    else:
        raise ValueError(f'Unexpected regex result: {line}')


def convert_callouts(lines: list[str]):
    indent = "  "
    marker = "> "

    out = []
    depth = 0
    for line in lines:
        current_depth = count_depth(line, marker)
        if current_depth > depth:
            x = re.findall(marker + r'\[!(\w+)](.*)', line)
            typ, title = x[0] if x else ('note', '')
            color = CALLOUT_COLORS[typ.lower()]

            header = indent * depth
            header += r"\begin{tcolorbox}"
            header += f"[colframe={color}!25,colback={color}!10,coltitle={color}!20!black,title={{{title}}}]\n"
            out.append(header)

            depth += 1

            if not x:
                out.append(line.replace(marker, indent, depth))
            continue

        while current_depth < depth:
            depth -= 1
            tail = indent * depth
            tail += "\\end{tcolorbox}\n"
            out.append(tail)

        if depth:
            out.append(line.replace(marker, indent, depth))
        else:
            out.append(line.replace(marker, indent, depth))
    return out


def convert_images(lines: list[str], img_dir: Path):
    out = []
    for line in lines:
        if '![[' in line and ('.png' in line or '.jpg' in line):
            image_name = line[line.find('[[') + 2:line.find(']]')]
            if '|' in image_name:
                width = image_name.split('|')[1]
                image_name = image_name.split('|')[0]
            else:
                width = 500
            img_path: str = (img_dir / image_name).absolute().as_posix()
            out.append(f'\\includegraphics[width={width}pt]{{{img_path}}}\n')
        else:
            out.append(line)
    return out


def find_section_label(full: str, section: str):
    f = re.sub(r'\s', '', full)
    sec = re.sub(r'\s', '', section)

    reg = re.compile(r'(?:sub)*section(?:\[\S*?])?\{')
    for match in reg.finditer(f):
        opened = match.end() - 1
        closed = find_matching_brackets(f[opened+1:]) + 1 + opened
        if sec in f[opened+1:closed]:
            return re.findall(r'\\label\{(\S+?)}', f[closed+1:])[0]
    else:
        return re.findall(r'[a-zA-Z][\s\S]*', section)[0].lower().replace(' ', '-')


def convert_block_identifier(full):
    def repl(match):
        body, rest = match.groups()
        return rf'\label{{int.{body}}}' + ('\n\n' + rest.strip() if rest else '')
    reg = re.compile('\n+' + r'\\\^\{}([a-zA-Z0-9\-]+)(.*)')
    return reg.sub(repl, full)


def convert_links(full, tex_path: Path):
    filenames = {}

    def repl(match):
        # [[filename#heading^block|display]]
        filename, heading, block, display = [x.replace('\n', ' ') for x in match.groups()]

        body = display if display else block if block else heading if heading else filename if filename else ''
        if filename:
            if not (path := tex_path.with_name(filename + '.tex')).exists():
                return match.string[match.start():match.end()]

            idx = filenames.setdefault(filename, len(filenames) + 1)
            if heading:
                with open(path, 'r', encoding='UTF-8') as file:
                    label = find_section_label(file.read(), heading)
                return rf'\hyperref[file{idx}:{label}]{{{body}}}'

            elif block:
                return rf'\hyperref[file{idx}:int.{block}]{{{body}}}'

            else:
                return rf'\href{{run:./{filename}.pdf}}{{{body}}}'

        else:
            if heading:
                label = find_section_label(full, heading)
                return rf'\hyperref[{label}]{{{body}}}'

            elif block:
                return rf'\hyperref[int.{block}]{{{body}}}'
        raise ValueError(f'Unexpected pattern: {match}')

    reg = re.compile(r'(?:\{\[}\{\[}|\[\[)'
                     r'([^^#|\]\\]*)'
                     r'(?:(?:\\#)?|#?)'
                     r'([^^#|\]\\]*)'
                     r'(?:(?:\\\^\{})?|\^?)'
                     r'([^^#|\]\\]*)'
                     r'(?:(?:\\textbar )?|\|?)'
                     r'([^^#|\]\\]*)'
                     r'(?:\{]}\{]}|]])')
    new_full = reg.sub(repl, full)

    external_docs = "".join([f'\\externaldocument[file{idx}:]{{{filename}}}\n' for filename, idx in filenames.items()])
    return new_full.replace(r'\begin{document}', external_docs + '\n' + r'\begin{document}')


def no_redundant_double_dollars(lines: list[str]):
    # TODO 이 함수는 post-mortem 방식으로 적용하는게 나을 것 같긴 함
    full = "".join(lines)
    auto_maths = ['equation', 'align']
    pattern = r'(\$\$\s*)' +\
              rf'(\\begin{{(?:{"|".join(auto_maths)})}})' +\
              r'(.*?)' +\
              rf'(\\end{{(?:{"|".join(auto_maths)})}})' +\
              r'(\s*\$\$)'
    reg = re.compile(pattern, flags=re.DOTALL)
    mod_full = reg.sub(r'\2\3\4', full)
    return mod_full.splitlines(keepends=True)


def no_empty_lines_in_math_blocks(lines: list[str]):
    out = []
    total = 0
    for i, line in enumerate(lines):
        total += line.count('$$')
        if (total % 2) and not line.strip():
            continue
        out.append(line)
    return out


def strict_line_break(lines: list[str]):
    """
    Case 1.
        "1."으로 시작
        "+ "로 시작
        "- "로 시작
    -> 윗 줄은 "#" "1." "+" "-" 중 하나로 시작하거나 empty line

    Case 2.
        "  1."
        "  + "
        "  - " 로 시작
    -> 윗 줄은 반드시 empty line

    저런 라인 덩어리가 끝나면 무조건 empty line 추가

    Case 3.
        "---"로 시작
    -> 위아래 줄은 반드시 empty line

    Case 4.
        "^"로 시작
    -> 아래줄은 empty line

    line type: "Others", "Empty", "Headings", "List", "Indented_List"
    """
    out = [lines[0]]
    line_types = [line_type(line) for line in lines]
    for (ptype, ctype), (prev, curr) in zip(pairwise(line_types), pairwise(lines)):
        match (ptype, ctype):
            case ("O"|"IL"|"BI", "L"):
                out.append('\n')
            case (_, "L"):
                pass
            case ("E", "IL"):
                pass
            case (_, "IL"):
                out.append('\n')
            case ("L"|"IL", x) if x != "E":
                out.append('\n')
            case ("HR", x) | (x, "HR") if x != "E":
                out.append('\n')
            case ("BI", x) if x != "E":
                out.append('\n')
        out.append(curr)
    return out


def full_horizontal_rules(full):
    return full.replace(r'\begin{center}\rule{0.5\linewidth}{0.5pt}\end{center}',
                        r'\begin{center}\rule{1.0\linewidth}{0.5pt}\end{center}')


def find_matching_brackets(full: str):
    count = 1
    for end, x in enumerate(full):
        if x == '{':
            count += 1
        elif x == '}':
            count -= 1
        if not count:
            return end


def convert_footnotes(full):
    full = full.replace('\\hypersetup{\n  hidelinks,\n  pdfcreator={LaTeX via pandoc}}',
                        '%\\hypersetup{\n  %hidelinks,\n  %pdfcreator={LaTeX via pandoc}}')

    reg = re.compile(r'\n\s\s')
    footnotes = {}
    splits = full.split(r'\footnote{')
    temp = [splits[0]]
    for i, split in enumerate(splits[1:], 1):
        end = find_matching_brackets(split)
        footnote = reg.sub(' ', split[:end])
        idx = footnotes.setdefault(footnote, len(footnotes)+1)
        temp.append(rf'\hyperref[^ref.{idx}]{{\textsuperscript{{[{idx}]}}}}')
        temp.append(split[end+1:])  # split[end] == '}', which has already taken above

    joined = "".join(temp)
    new = old = "\\section{References}\\label{references}\n"
    for footnote, idx in footnotes.items():
        new += f'[{idx}]  {footnote}\\label{{^ref.{idx}}}\n\n'
    return joined.replace(old, new)


def comment_out_default_fonts(full):
    olds = [#r'\usepackage{unicode-math}',
            r'\defaultfontfeatures{Scale=MatchLowercase}',
            r'\defaultfontfeatures[\rmfamily]{Ligatures=TeX,Scale=1}']

    new_full = full
    for old in olds:
        new_full = new_full.replace(old, '%'+old)
    return new_full


if __name__ == "__main__":
    MdConvert().convert().export()
