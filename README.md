# Revised Geneva Score Calculator

A clinical pretest probability calculator for pulmonary embolism (PE) in patients with suspected PE. Implements the eight-variable **Revised Geneva Score**, not the original Geneva score or the simplified score.

The static browser app runs without Python, external services, cookies, analytics, or a server. No clinical inputs are sent over the network by the browser calculator.

## Clinical scoring

| Criterion | Points |
| --- | ---: |
| Age >65 years | 1 |
| Previous deep-vein thrombosis or PE | 3 |
| Surgery or fracture within one month | 2 |
| Active malignancy | 2 |
| Unilateral lower-limb pain | 3 |
| Hemoptysis | 2 |
| Heart rate 75–94 bpm | 3 |
| Heart rate ≥95 bpm | 5 |
| Deep-vein tenderness on palpation **and** unilateral edema | 4 |

The heart-rate rows are mutually exclusive, so the maximum score is **22**.

- **Low:** 0–3 points
- **Intermediate:** 4–10 points
- **High:** 11–22 points

This is a *pretest probability classification*, **not a percentage risk estimate, diagnostic result, or standalone clinical management algorithm**. Evaluation must follow the appropriate PE diagnostic pathway and clinical judgment. Incomplete criteria are rejected rather than assumed absent.

**Clinical reference:** Le Gal G, Righini M, Roy PM, et al. Prediction of pulmonary embolism in the emergency department: the revised Geneva score. *Ann Intern Med.* 2006;144:165–171. [PubMed](https://pubmed.ncbi.nlm.nih.gov/16461960/).

## Browser application

Open `web/index.html` in a modern browser. Select an explicit Yes/No answer for each clinical finding, enter age and heart rate, then choose **Calculate score**. The result displays the points, risk category, and scoring breakdown. **Clear form** discards the entered values.

The production GitHub Pages workflow publishes only `web/index.html`, `web/calculator.js`, and `web/ui.js`. Check the repository's deployment status for the public URL; publication is not a prerequisite for offline use.

## Python installation and command line

Python 3.10+ is supported. The core `geneva.py` calculation uses only the standard library.

```bash
python -m pip install -e '.[dev]'
python geneva.py single --age 66 --heart-rate 95 --previous-dvt-pe --hemoptysis
python geneva.py batch --input sample.csv --output results.csv
python -m pytest -q
node --test web/calculator.test.cjs
```

The example single case is 11 points (high). Individual criterion switches in the CLI default to false; age and heart rate are mandatory. For all-criteria-explicit evaluation, supply a JSON object with the eight fields:

```bash
python geneva.py single --json '{"age":66,"heart_rate":95,"previous_dvt_pe":true,"surgery_or_fracture_1mo":false,"active_malignancy":false,"unilateral_leg_pain":false,"hemoptysis":true,"deep_vein_tenderness_and_unilateral_edema":false}'
```

The CSV input requires these exact columns: `age`, `heart_rate`, `previous_dvt_pe`, `surgery_or_fracture_1mo`, `active_malignancy`, `unilateral_leg_pain`, `hemoptysis`, and `deep_vein_tenderness_and_unilateral_edema`. Use `true/false`, `yes/no`, or `1/0` for binary inputs. Additional columns are retained. Exported free-text cells that could be treated as spreadsheet formulas are escaped.

## Optional local API

Start the local FastAPI server:

```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/` for the same application. `POST /api/geneva` accepts the eight clinical fields as JSON, with actual JSON booleans for binary criteria, and returns `score`, `tier`, and `detail`. Interactive API docs are available at `/docs`.

The original `cli.py audit/chat/batch/verify-audit` commands and legacy `/api/audit`, `/api/chat`, `/metrics`, and `/api/audit/logs` endpoints remain for compatibility. **These legacy prototype features are unrelated to the Revised Geneva score and must not be used to make clinical decisions.** The legacy HMAC audit log is process-local, not a durable compliant audit system. Do not expose the legacy server publicly without additional access controls.

## Privacy, security, and compatibility

The **static browser application** processes clinical criteria entirely in the user's browser without persistence or third-party requests. It does not ask for identifying data. The optional API processes request data on the host running the server; deployment, access control, and data governance are the operator's responsibility. No regulatory compliance or PHI de-identification is claimed.

The browser application uses standard JavaScript and requires a current version of Chrome, Firefox, Safari, or Edge. No Pyodide/PyScript is needed. Python API dependencies are declared in `pyproject.toml`; the GitHub Actions matrix tests Python 3.10–3.12 and Node.js.

## License

[MIT](LICENSE).
