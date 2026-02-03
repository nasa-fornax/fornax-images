from pathlib import Path
import re


manifests = {
    'multi': {
        'folder': 'fornax-demo-notebooks/',
        'manifest': 'fornax-manifest.txt',
    },
    'irsa': {
        'folder': 'irsa-tutorials',
        'manifest': 'notebook_manifest_descriptions.txt',
    },
    'heasarc': {
        'folder': 'heasarc-tutorials',
        'manifest': 'fornax-manifest.yml',
    }
}

class Parser:

    def dir2cat(dirname):
        """Dir name to category"""
        return re.sub('[_-]+', ' ', dirname).title()
    
    def std_parse(lines, archive_name):
        """Parse lines of the form: path: title"""
        dir_name = manifests[archive_name]['folder']
        nb_desc = {}
        for line in lines:
            line = line.strip()
            if ':' not in line:
                continue
            path, desc = line.split(':')
            path = Path(path)
            cat = Parser.dir2cat(path.parts[0])
            if cat not in nb_desc:
                nb_desc[cat] = []
            nb_desc[cat].append(f'   - [{desc.strip()}]({dir_name}/{path})')
        
        md_desc = '\n'.join([f'- {cat}:\n' + ('\n'.join(vals)) for cat, vals in nb_desc.items()])

        return md_desc

    def parse_multi(manifest):
        """Parse Multi-archive manifest"""
        with open(manifest) as fp:
            lines = fp.readlines()
        return Parser.std_parse(lines, 'multi')
    
    def parse_irsa(manifest):
        """Parse IRSA manifest"""
        with open(manifest) as fp:
            lines = fp.readlines()
        # remove the extra level
        lines = [line.replace('irsa-tutorials/', '') for line in lines]
        return Parser.std_parse(lines, 'irsa')

    
    def parse_heasarc(manifest):
        """Parse HEASARC manifest"""
        # first put the manifest in standard form
        with open(manifest) as fp:
            lines = fp.readlines()
        new_lines = []
        for line in lines:
            if '- path:' in line:
                path = line.split(':')[1].strip()
            if 'title:' in line:
                path += f': {line.split(':')[1].strip()}'
                new_lines.append(path)
        return Parser.std_parse(new_lines, 'heasarc')
        

def main():
    """Parse manifest files in the archive repo"""

    intro_file = 'introduction.mdv'
    with open(intro_file, 'r') as fp:
        intro_txt = ''.join(fp.readlines())

    nb_desc = {}
    for archive_name, props in manifests.items():
        parser = getattr(Parser, f'parse_{archive_name}')
        folder = Path(props['folder'])
        manifest = folder / Path(props['manifest'])
        md_desc = parser(manifest)

        # add the notebook description to intro_file
        intro_txt = intro_txt.replace(f'<!-- {archive_name.upper()}_NOTEBOOKS -->', md_desc)
    
    with open(intro_file, 'w') as fp:
        fp.write(intro_txt)

if __name__ == '__main__':
    main()