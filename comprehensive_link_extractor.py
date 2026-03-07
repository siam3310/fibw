
name: Update Scraped Links

on:
  schedule:
    - cron: '0 * * * *' # Runs every hour
  workflow_dispatch:

jobs:
  update-links:
    runs-on: ubuntu-latest
    permissions:  # Add this block
      contents: write # Grant write permission
    steps:
      - name: Check out repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run script
        run: python comprehensive_link_extractor.py

      - name: Commit and push changes
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          if [ -f "scraped-links.json" ]; then
            git add scraped-links.json
          fi
          git diff --staged --quiet || (git commit -m "Update scraped links" && git push)
