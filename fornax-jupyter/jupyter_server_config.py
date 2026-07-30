
# c = get_config() assumed called.

# cull terminals
c.TerminalManager.cull_inactive_timeout = 3600
c.TerminalManager.cull_interval = 300

# for nbconvert
c.PDFExporter.latex_command = ['tectonic', '{filename}']
c.PDFExporter.bib_command = ['/bin/true', '{filename}']

# Disable Build Check via Jupyter
c.ServerApp.tornado_settings = {
    "page_config_data": {
        "buildCheck": False,
        "buildAvailable": False
    }
}