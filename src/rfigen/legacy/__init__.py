"""RFIGen legacy engine.

The original pandas/DataFrame-based RFIGen implementation, preserved intact.
It models radiometric scans as MP-3000A-style row tables and injects RFI from
source classes with azimuth/elevation angular coupling — a different data model
from the ndarray core in :mod:`rfigen`, kept because it carries capability the
core does not: RTTOV synthetic generation, XLSX export, and three GUIs.
"""
