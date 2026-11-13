# Inspection evidence reports

See [ROADMAP.md](ROADMAP.md) for proposed review-queue, validation and reporting improvements.

Review suspicious drone frames, retain human decisions and export self-contained
HTML reports with evidence images, heatmaps and model provenance. Linux containers
and native Python are supported. No trained model or real inspection data is bundled.

## Local demo

```sh
python -m venv .venv
python -m pip install -r requirements.txt
python reports.py demo --output outputs/demo
python -m streamlit run app.py
python reports.py export outputs/demo --output outputs/demo-report.html
python -m unittest discover -v
```

Activate `.venv` first (`source .venv/bin/activate` on Linux or
`.venv\Scripts\Activate.ps1` on Windows). All generated output paths must be new.
The demo contains simulated cracks and scores, not learned detections.

## Linux container

```sh
docker compose build
docker compose run --rm review python reports.py demo --output outputs/demo
docker compose up -d
```

Open http://localhost:8505. The bind-mounted outputs directory must be writable by
container UID 10001 on Linux. The app is a local tool with no authentication.
Do not expose its port on a public interface. `docker compose down` preserves files.

## Drone pipeline integration

Copy a complete `drone-inspection-heatmaps` run under `outputs/`, then enter its
directory in the interface. Both uint8 NPY grids and packed `maps.bin` grids with
manifest byte offsets are supported. Run inputs require `run.json`, `frames.jsonl`,
and the heatmap/evidence assets referenced by each row. Assets must remain inside
the run directory. Failed/incomplete/legacy status is displayed rather than hidden.

Reviews are immutable JSON records under `<run>/reviews/`, tied to metadata,
manifest, exact heatmap bytes and source evidence hashes. Changing an input makes
earlier reviews stale. All valid reviews are shown; conflicting reviews are not
silently resolved. Human assessments do not establish structural safety.

Reports embed image thumbnails and heatmaps, so they can be moved without a source
folder. They contain evidence and reviewer notes: distribute them deliberately.
Source frame paths and model metadata may include identifying information. HTML
content is escaped. PDF export, reviewer authentication, digital signatures and
formal inspection standards are outside this first version.
