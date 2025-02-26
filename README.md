# Race Line Optimization

A repo focused solely on race-line optimization  

## Setup

1. Create the virtual environment by running:

```bash
python3 -m venv venv
```

2. Activate the virtual environment by running:

```bash
source venv/bin/activate
```

3. Install the required packages by running:

```bash
pip install -r requirements.txt
```

4. Run the script to extract the track edges from from the PGM file:
```bash
python src/claude_track_from_pgm.py ./maps/cdc_2024/cdc_2024_edited.pgm
```