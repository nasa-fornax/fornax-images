---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.7
kernelspec:
  display_name: notebook
  language: python
  name: python3
---

# Shutdown-Mode Test Suite

This notebook helps verify shutdown modes of Fornax.  Three tests are included.

1. Stay alive if there is **CPU activity**, even with browser closed or internet dropped.
2. Stay alive if there is **network I/O** (e.g. Astroquery calls)
3. Terminate after **15 minutes of idle** (no CPU, no I/O)  


These tests need to be run **interactively**, step by step.  Assuming a user runs these interactively and updates variables, a table is generated at the end of this code to show a summary of the shutdown findings

```{code-cell} ipython3
!pip install psutil astroquery
```

```{code-cell} ipython3
import time
import logging
import os
import requests
from astroquery.ipac.irsa import Irsa
import astropy.units as u
from astropy.coordinates import SkyCoord
import shutil
import warnings
import pandas as pd
import astropy.constants as const
import astropy.units as u
import astroquery.exceptions
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.table import Table
from astropy.table import vstack
from astroquery.mast import Observations
from specutils import Spectrum1D
import itertools

coords = []
coords.append(SkyCoord("09 54 49.40 +09 16 15.9", unit=(u.hourangle, u.deg)))
coords.append(SkyCoord("12 45 17.44 27 07 31.8", unit=(u.hourangle, u.deg)))
coords.append(SkyCoord("14 01 19.92 -33 04 10.7", unit=(u.hourangle, u.deg)))
coords.append(SkyCoord(233.73856, 23.50321, unit=u.deg))
coords.append(SkyCoord(150.091, 2.2745833, unit=u.deg))
coords.append(SkyCoord(150.1024475, 2.2815559, unit=u.deg))
coords.append(SkyCoord("150.000 +2.00", unit=(u.deg, u.deg)))
coords.append(SkyCoord("+53.15508 -27.80178", unit=(u.deg, u.deg)))
coords.append(SkyCoord("+53.15398 -27.80095", unit=(u.deg, u.deg)))
coords.append(SkyCoord("+150.33622 +55.89878", unit=(u.deg, u.deg)))


# configure logging
logging.basicConfig(filename='shutdown_test.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')
```

## Test 1: CPU running tests.
The Fornax policy is that the kernel will not shutdown if CPU is active, even beyond the 15 min. idle cutoff time.  We want this to be the case because we want notebooks to be able to run longer than 15 min asynchronously.

```{code-cell} ipython3
def cpu_busy_test(duration_minutes=30):
    """
    Spin the CPU nonstop for `duration_minutes`.
    If the session is *not* shut down, this will complete and log PASS.
    """
    logging.info("Starting CPU-busy test for %d minutes", duration_minutes)
    print(
        f"▶ CPU-busy test started: running for {duration_minutes} min. "
        "NOW close your browser , wait 25 full minutes, then go to science-console and open compute"
    )
    end = time.time() + duration_minutes*60
    # tight loop to generate CPU load
    while time.time() < end:
        _ = sum(i*i for i in range(10000))
    print("✅ Kernel stays alive if there is CPU working")
    logging.info("Kernel stays alive if their is CPU working: CPU-busy browser close test PASS")
```

### 1.1 Does the kernel stay running if the CPU is working?

Instructions:
1. One at a time, test this with a) closing the browser and b) turning off internet

2. start cell, start stopwatch

3. either close the browser or turn off internet, wait 25 minutes (less than duration_minutes, more than 15 minutes)

4. restart browser/internet. check science-console to see if it still has a compute instance.

5. go to science console dashboard and open back up compute\
    things to check:\
      a) is the kernel is busy (as indicated in the foother)? \
      b) are results printed to the screen, and logged to a file?\ 
      c) does output from previous cells return when I open a new browser window?

```{code-cell} ipython3
# Run this cpu_busy test twice
# once with closing the browswer, once with turning off internet
cpu_busy_test(30)
```

```{code-cell} ipython3
#save the results of these two tests but assaigning the correct values below
# after observing the results of the above test, change TRUE/FALSE to be accurate

#Is the kernel alive after closing the browser
kernel_alive_cpu_busy_close_browser = True  #checked 5/1/25 JK
kernel_alive_cpu_busy_close_internet = True #checked 5/1/25 JK
```

## Test 2: Network-I/O running tests

Uses coordinates to exercise Astroquery’s JWST query (all I/O, limited CPU).  This is a real life example from one of fornax-demo-notebooks, hence why it is a bit longer/more complicated than the other tests.

```{code-cell} ipython3
def coords_to_sample_table(coords, labels=None):
    """
    Build an astropy Table with columns 'coord', 'label', and 'objectid'
    suitable for JWST_get_spec_helper.

    Parameters
    ----------
    coords : list of astropy.coordinates.SkyCoord
        List of source coordinates.
    labels : list of str, optional
        Human-readable labels for each source. If None, defaults to 'obj0', 'obj1', etc.

    Returns
    -------
    astropy.table.Table
        Table with columns:
        - coord : SkyCoord
        - label : str
        - objectid : str
    """
    n = len(coords)
    # Generate default labels if not provided
    if labels is None:
        labels = [f"obj{i}" for i in range(n)]
    elif len(labels) != n:
        raise ValueError("Length of labels must match length of coords.")
    # Create objectids by combining label and index
    objectids = [f"{label}_{i}" for i, label in enumerate(labels)]

    tbl = Table()
    tbl['coord'] = coords
    tbl['label'] = labels
    tbl['objectid'] = objectids
    return tbl




def JWST_get_spec_helper(sample_table, search_radius_arcsec, datadir, verbose,
                         delete_downloaded_data=True):
    """
    Retrieve JWST spectra for a list of sources.

    Parameters
    ----------
    sample_table : astropy.table.Table
        Table with the coordinates and journal reference labels of the sources.
    search_radius_arcsec : float
        Search radius in arcseconds.
    datadir : str
        Data directory where to store the data. Each function will create a
        separate data directory (for example "[datadir]/JWST/" for JWST data).
    verbose : bool
        Verbosity level. Set to True for extra talking.
    delete_downloaded_data : bool, optional
        If True, delete the downloaded data files.

    Returns
    -------
    MultiIndexDFObject
        The spectra returned from the archive.
    """

    # Create directory
    if not os.path.exists(datadir):
        os.mkdir(datadir)
    this_data_dir = os.path.join(datadir, "JWST/")


    for stab in sample_table:

        print("Processing source {}".format(stab["label"]))

        # Query results
        search_coords = stab["coord"]
        # If no results are found, this will raise a warning. We explicitly handle the no-results
        # case below, so let's suppress the warning to avoid confusing notebook users.
        warnings.filterwarnings("ignore", message='Query returned no results.',
                                category=astroquery.exceptions.NoResultsWarning,
                                module="astroquery.mast.discovery_portal")
        query_results = Observations.query_criteria(
            coordinates=search_coords, radius=search_radius_arcsec * u.arcsec,
            dataproduct_type=["spectrum"], obs_collection=["JWST"], intentType="science",
            calib_level=[2, 3, 4], instrument_name=['NIRSPEC/MSA', 'NIRSPEC/SLIT'],
            dataRights=['PUBLIC'])
        print("Number of search results: {}".format(len(query_results)))

        if len(query_results) == 0:
            print("Source {} could not be found".format(stab["label"]))
            continue

        # Retrieve spectra
        data_products = [Observations.get_product_list(obs) for obs in query_results]
        data_products_list = vstack(data_products)
        
        # Filter
        data_products_list_filter = Observations.filter_products(
            data_products_list, productType=["SCIENCE"], extension="fits",
            calib_level=[2, 3, 4],  # only calibrated data
            productSubGroupDescription=["X1D"],  # only 1D spectra
            dataRights=['PUBLIC'])  # only public data
        print("Number of files to download: {}".format(len(data_products_list_filter)))

        if len(data_products_list_filter) == 0:
            print("Nothing to download for source {}.".format(stab["label"]))
            continue

        # Download
        download_results = Observations.download_products(
            data_products_list_filter, download_dir=this_data_dir, verbose=False)

        # Create table
        # NOTE: `download_results` has NOT the same order as `data_products_list_filter`.
        # We therefore have to "manually" get the product file names here and then use
        # those to open the files.
        keys = ["filters", "obs_collection", "instrument_name", "calib_level",
                "t_obs_release", "proposal_id", "obsid", "objID", "distance"]
        tab = Table(names=keys + ["productFilename"], dtype=[str,
                    str, str, int, float, int, int, int, float]+[str])
        for jj in range(len(data_products_list_filter)):
            # Match query 'obsid' to product 'parent_obsid' (not 'obsID') because products may
            # belong to a different group than the observation.
            idx_cross = np.where(query_results["obsid"] ==
                                 data_products_list_filter["parent_obsid"][jj])[0]
            tmp = query_results[idx_cross][keys]
            tab.add_row(list(tmp[0]) + [data_products_list_filter["productFilename"][jj]])

        # Create multi-index object
        for jj in range(len(tab)):

            # find correct path name:
            # Note that `download_results` does NOT have same order as `tab`!!
            file_idx = np.where([tab["productFilename"][jj] in download_results["Local Path"][iii]
                                for iii in range(len(download_results))])[0]

            # open spectrum
            # Note that specutils returns the wrong units. Use Table.read() instead.
            filepath = download_results["Local Path"][file_idx[0]]
            spec1d = Table.read(filepath, hdu=1)

            dfsingle = pd.DataFrame(dict(
                wave=[spec1d["WAVELENGTH"].data * spec1d["WAVELENGTH"].unit],
                flux=[spec1d["FLUX"].data * spec1d["FLUX"].unit],
                err=[spec1d["FLUX_ERROR"].data *
                     spec1d["FLUX_ERROR"].unit],
                label=[stab["label"]],
                objectid=[stab["objectid"]],
                mission=[tab["obs_collection"][jj]],
                instrument=[tab["instrument_name"][jj]],
                filter=[tab["filters"][jj]],
            )).set_index(["objectid", "label", "filter", "mission"])

        if delete_downloaded_data:
            shutil.rmtree(this_data_dir)

    return dfsingle


def network_access_test(sample_table, duration_minutes=30):
    """
    Loop JWST_get_spec_helper calls over entries in `sample_table` repeatedly
    for `duration_minutes`. Exits cleanly when elapsed time reaches the duration.

    Parameters
    ----------
    sample_table : astropy.table.Table
        Table built via coords_to_sample_table() for JWST_get_spec_helper.
    duration_minutes : int
        Total wall-clock minutes to run the test.
    """
    logging.info('Starting network-I/O JWST test for %d minutes', duration_minutes)
    print(f'▶ JWST network test started: running for {duration_minutes} min. NOW close your browser tab!')
    start = time.time()
    # cycle through table rows indefinitely
    for row in itertools.cycle(sample_table):
        elapsed = time.time() - start
        if elapsed >= duration_minutes * 60:
            break
        try:
            df_jwst = JWST_get_spec_helper(
                sample_table=[row],
                search_radius_arcsec=150,
                datadir="./data/",
                verbose=False,
                delete_downloaded_data=True
            )
            n = len(df_jwst) if df_jwst is not None else 0
            print(f'[{time.ctime()}] {row["label"]}: {n} records')
            logging.info('Queried %s → %d records', row['label'], n)
        except Exception as e:
            print(f'[{time.ctime()}] ERROR {e}')
            logging.error('Error querying %s: %s', row['label'], e)
    print('✅ JWST network test complete: kernel still running.')
    logging.info('JWST network test PASS: kernel stayed alive.')
```

### 2.1 Does the kernel stay running if the I/O is ongoing?
Instructions
1. One at a time, test this with a) closing the browser and b) turning off internet

2. start cell, start stopwatch

3. either close the browser or turn off internet, wait 25 minutes (less than duration_minutes, more than 15 minutes)

4. restart browser/internet. check science-console to see if it still has a compute instance.

5. go to science console dashboard and open back up compute\
    things to check:\
      a) is the kernel is busy (as indicated in the foother)? \
      b) are results printed to the screen, and logged to a file?\ 
      c) does output from previous cells return when I open a new browser window?

```{code-cell} ipython3

```

```{code-cell} ipython3
#make the sample into a table for input to network_access_test
sample_table = coords_to_sample_table(coords)

#run test
network_access_test(sample_table, duration_minutes=30)
```

```{code-cell} ipython3
#save the results of these two tests by assaigning the correct values below
# after observing the results of the above test, change TRUE/FALSE to be accurate

#Is the kernel alive after running these two tests
kernel_alive_IO_busy_close_browser = False   #checked 5/1/25 JK
kernel_alive_IO_busy_close_internet = False   #checked 5/1/25 JK
```

## 3: Idle Timeout tests
Fornax policy is to shutdown if the browswer has been closed or internet connection lost for >15 minutes.

+++

### 3.1: Does closing the browser for 25 Minutes kill the kernel?

Instructions:
- with no cpu usage
- close the browser
- wait 25 minutes
- re-open the browser, go to science console
- does it say 0 servers are running or > 0?

```{code-cell} ipython3
kernel_alive_idle_timeout_close_browser = False  #checked 5/1/25 JK
```

### 3.2: Does dropping internet for 25 Minutes kill the kernel?

Instructions:
- with no cpu usage
- turn off internet
- wait 25 minutes
- re-open the browser, go to science console
- does it say 0 servers are running or > 0?

```{code-cell} ipython3
kernel_alive_idle_timeout_close_internet = False  #checked 5/1/25 JK
```

## 4. Collate results into a table

```{code-cell} ipython3
# your boolean-to-string mapping
mapping = {True: "alive", False: "shutdown"}

# build your table
data = {
    'CPU running': [
        mapping[kernel_alive_cpu_busy_close_browser],
        mapping[kernel_alive_cpu_busy_close_internet]
    ],
    'I/O running': [
        mapping[kernel_alive_IO_busy_close_browser],
        mapping[kernel_alive_IO_busy_close_internet]
    ],
    'Idle': [
        mapping[kernel_alive_idle_timeout_close_browser],
        mapping[kernel_alive_idle_timeout_close_internet]
    ],
}
index = ['Close browser (25 min)', 'Internet disconnected (25 min)']

df = pd.DataFrame(data, index=index)
# Display with more spacing
print(df.to_string(col_space=20))
```

```{code-cell} ipython3
#high tech test to see if the kernel is running/busy
print("hello")
```

```{code-cell} ipython3

```
