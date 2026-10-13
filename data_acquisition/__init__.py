"""Data acquisition layer for the European Bank Financial Data Reconciliation project.

Modules:
    waves           - the Pillar 3 publication calendar (when new data is expected)
    entities        - the LEI universe we track, and GLEIF-based enrichment
    gleif_client    - thin wrapper around the public GLEIF API
    eba_exercises   - EBA's Transparency Exercise/Stress Test bulk CSV downloads
    esef_client     - ESEF financial-statement filings via filings.xbrl.org
    edap_scraper    - Playwright scraper for the Pillar 3 Data Hub (P3DH) UI
    edap_downloader - the swappable adapter that actually fetches EBA Pillar 3 files
    run_update      - the script you schedule; downloads whatever is new since last run
    reconcile       - the package surface: get_financial_data() and friends
"""
