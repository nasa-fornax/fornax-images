
# c = get_config() assumed called.

# cull terminals
c.TerminalManager.cull_inactive_timeout = 3600
c.TerminalManager.cull_interval = 300

# for nbconvert
c.PDFExporter.latex_command = ['tectonic', '{filename}']
c.PDFExporter.bib_command = ['/bin/true', '{filename}']