# Implementation Notes

This document contains advisory implementation notes for `ocrone`. It may guide code development, but it is not a guard rail and must not override the governing planning documents.

Use this document as a suggestion layer during implementation. Binding product behavior belongs in `user_intent.md`; development rules belong in `development_governance.md`; documentation rules belong in `documentation_principle.md`; coding principles belong in `design_and_coding_principle.md`.

---

## Repository Structure

```
ocrone/
|-- requirements.txt            # Package dependencies
|-- build_exe.ps1               # Reproducible PyInstaller build script
|-- planning_and_spec/
|   |-- design_and_coding_principle.md  # Architectural and coding principles
|   |-- development_governance.md       # Workflow and build governance
|   |-- documentation_principle.md      # Rules for editing specs
|   |-- implementation_note.md          # Advisory implementation notes
|   |-- role_and_responsibility.md     # AI agent SDLC roles and self-calibration
|   `-- user_intent.md                  # Binding application behavior
|-- main.py                     # Entry point and CLI orchestrator
`-- src/
    |-- __init__.py
    |-- engine.py               # Orchestrator flow
    |-- config.py               # Configuration management
    |-- ocr/
    |   |-- __init__.py
    |   |-- base.py             # Abstract OCR interfaces and shared dataclasses
    |   `-- easyocr_engine.py   # EasyOCR adapter and word-line grouping
    |-- layout/
    |   |-- __init__.py
    |   |-- doclayout_detector.py # DocLayout-YOLO layout-region adapter
    |   `-- preprocessor.py     # OCR-oriented contrast normalization and deskew
    |-- pdf/
    |   |-- __init__.py
    |   `-- builder.py          # ReportLab searchable PDF builder
    `-- utils/
        |-- __init__.py
        |-- file_handler.py     # Natural sort and sequence gap validator
        |-- logger.py           # Logging engine
        `-- reporter.py         # Structured JSON execution log generator
```

---

## 1. System Requirements & Installation

1. **Python**: Python 3.10 or 3.11 recommended.
2. **PyTorch Runtime**: EasyOCR and DocLayout-YOLO both depend on PyTorch. CPU execution is valid but slower. The fast binary must be built from a CUDA-enabled PyTorch environment.
3. **Dependencies**: Install via pip from the project virtual environment:

   ```bash
   python -m pip install -r requirements.txt
   ```

### End-User Environment Build

To run from source, create a virtual environment and install from `requirements.txt`:

```powershell
py -3.11 -m venv ocrone-env
.\ocrone-env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py -i <input_images_directory>
```

OCR and layout model files may be downloaded by their upstream libraries on first use. Development runs should keep virtual environments and caches local to the project workspace or another developer-owned location, not checked into Git.
When a project-local `.venv` exists, source runs should place OCR/model caches under `.venv/cache/`. `OCRONE_CACHE_DIR` may override the cache root.

For users who do not need source execution, distribute the packaged executable instead:

```powershell
.\dist\ocrone.exe -i <input_images_directory>
```

The build step also places a sample configuration file at `dist/ocrone_sample_config.properties`. It lists every supported configuration property at its default value and can be copied or edited before passing it with `--config`.

### Optional Docker Environment

Docker may be used to create a reproducible source runtime. A minimal Dockerfile should install the dependency set from `requirements.txt`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .
ENTRYPOINT ["python", "main.py"]
```

Build and run:

```powershell
docker build -t ocrone .
docker run --rm -v ${PWD}:/work ocrone -i /work/<input_images_directory>
```

Developer environment ownership rules are defined in `planning_and_spec/development_governance.md`.

---

## 2. Configuration (`src/config.py`)

Centralized parameters for processing:

- `DEFAULT_DPI`: DPI used for PDF point calculations.
- `DEFAULT_LANGUAGES`: EasyOCR language code defaults.
- `ocr_device`: Device selection for EasyOCR and DocLayout-YOLO. `auto` should choose CUDA when PyTorch reports CUDA availability and print the resolved device at startup.
- `ocr_canvas_size`: EasyOCR detector long-side canvas limit for each submitted OCR fragment. Default should be `1024`.
- `ocr_mag_ratio`: EasyOCR detector magnification ratio. Default should be `1.0`.
- `ocr_batch_size`: EasyOCR recognizer batch size. Default should be `1` because EasyOCR's batched recognition path can become slower on layout-region crops when batches are padded to the widest detected text crop.
- `deskew_enabled`: Enables OCR-oriented deskewing before recognition.
- `layout_enabled`: Enables DocLayout-YOLO layout region analysis.
- `CONFIDENCE_THRESHOLD`: OCR confidence limit below which warnings are triggered.
- `ocrone_sample_config.properties`: Generated into `dist/` during the build step. Contains every supported configuration property set to its default value.

---

## 3. Core Software Components Specification

### A. Image Preprocessor (`src/layout/preprocessor.py`)

- Applies contrast normalization to improve text visibility before OCR.
- Applies bounded deskewing when enabled.
- Rotation should use high-quality interpolation and a white border so deskewing does not smear content or crop page edges.
- Preprocessing is intended to improve OCR accuracy, not to create the final visual style of the page.

### B. Layout Detector (`src/layout/doclayout_detector.py`)

- Wraps DocLayout-YOLO behind a project-owned adapter.
- DocLayout-YOLO should be used for document layout regions, reading-order hints, and text/non-text classification.
- Load the DocStructBench checkpoint explicitly through `huggingface_hub.hf_hub_download()` and pass the downloaded `.pt` file path to `YOLOv10(...)`. Prefer the local Hugging Face cache first so normal runs do not make avoidable network checks after the model has already been downloaded.
- Use the resolved OCR device for prediction. In `auto` mode, CUDA should be used when PyTorch can see it; if `cuda` is explicitly requested and unavailable, fail clearly instead of silently using CPU.
- Do not treat DocLayout-YOLO as the source of word bounding boxes. EasyOCR provides the word-level geometry used for the searchable PDF text layer.
- Layout detection must run on the same preprocessed image that OCR sees so coordinates remain aligned.

### C. OCR Engine Wrapper (`src/ocr/easyocr_engine.py`)

- Wraps EasyOCR behind `BaseOCREngine`.
- Pass an explicit GPU flag to EasyOCR based on the resolved OCR device; do not rely on EasyOCR's default device behavior.
- Uses EasyOCR word boxes and recognized text as the primary OCR geometry.
- When DocLayout-YOLO returns usable layout regions, OCR those cropped regions with a small margin and translate EasyOCR boxes back into full-page coordinates. Fall back to full-page EasyOCR only when no usable layout regions are available or region OCR yields no words.
- Pass configured `canvas_size`, `mag_ratio`, and `batch_size` values into EasyOCR. `canvas_size` controls detector resize limits for each fragment; `batch_size` controls recognizer throughput after EasyOCR has detected text crops.
- Groups adjacent EasyOCR word boxes into physical text lines. The grouped line text should contain explicit spaces between words, including larger gaps when visual spacing indicates a column or large word gap.
- Associates OCR lines with DocLayout-YOLO regions when useful, while keeping a sane text default if no matching layout region is available.

### D. PDF Builder (`src/pdf/builder.py`)

- Uses `reportlab.pdfgen.canvas` to write output pages.
- Each page draws the original color page image at standard margins, applying the same deskew transform as the OCR image when deskewing is active. Do not apply contrast, background whitening, grayscale conversion, or other visual cleanup to the final PDF page image unless the user explicitly adds a new requirement.
- Embed page images as JPEG by default to produce smaller PDFs. Keep PNG/lossless embedding available through configuration for users who prefer exact image preservation over file size.
- Shows a `tqdm` progress bar while composing original color page images and the invisible text layer into the final PDF.
- The searchable text layer must be sandwiched over the page image using physical line-level invisible text objects with normal spaces between words.
- Do not place an entire paragraph or layout block as one PDF text object, because selection can collapse to the last line or copy text from the wrong visible position.
- Do not place adjacent words as separate PDF text objects without separators, because PDF viewers can copy merged words such as `youprioritize`.
- Prefer EasyOCR-derived line boxes for text-layer geometry. OpenCV may be used only as a fallback line-box estimator inside an existing OCR block crop.
- Apply configurable text-layer box alignment after OCR geometry is selected: `text_layer_vertical_offset` shifts the invisible line box by a fraction of the original line height, and `text_layer_height_scale` scales the invisible line box height. Defaults should move text boxes upward by 30% of a line height and shrink height to 90%.
- **Page Margin and White Space Trimming**:
  - Automatically crops each page to its content boundaries plus customizable padding.
  - Maintains a consistent width across all pages by using the maximum needed width across all processed pages, keeping reader zoom locked and stable.
  - Page heights remain variable to cleanly crop out empty margins at the top and bottom of the page.
- **Blank Page Skipping**: Automatically skips pages with zero detected text blocks by default to clean up blank scanning separators, logging them under `pages_skipped` with status `"SKIPPED_BLANK"`.
- Coordinate mapping formula maps pixel positions (origin top-left) to PDF canvas coordinates (origin bottom-left):

  $$x_{\text{pdf}} = \text{left} \times S$$
  $$y_{\text{pdf}} = H_{\text{pdf}} - [(\text{top} + \text{height}) \times S]$$

  where scale factor `S = 72 / DPI` and `H_pdf` is the scaled page height.

- Draws text invisibly using rendering mode `3` to allow copy-pasting without visibly painting OCR text over the scan.

### E. Sequence Validator (`src/utils/file_handler.py`)

- Checks for file gaps using regular expressions.
- In interactive mode, warnings must explain the practical problem before asking whether to continue.
- Aborts execution if the sequence is broken and the user does not grant override permission, or if `--non-interactive` is passed without `--ignore-missing-pages`.

### F. Structured JSON Reporter (`src/utils/reporter.py`)

- Generates a file called `<output_pdf_name>_worklog.json` listing:
  - Total elapsed time.
  - Mean OCR confidence score per page.
  - Detected skew angle per page.
  - Warnings and errors.

---

## 4. Usage Instructions

Run the application from the project root:

```bash
python main.py -i <input_images_directory> [options]
```

### Command Options

- `-c`, `--config`: Path to configuration properties file serving as the base configuration.
- `-i`, `--input-dir`: Directory containing images or a PDF file.
- `-o`, `--output-file`: Final searchable PDF output path. Defaults to the input path name with a `.pdf` suffix.
- `-l`, `--lang`: EasyOCR language code. Can be declared multiple times, such as `-l en -l es`.
- `--dpi`: Target PDF layout DPI.
- `--ocr-device`: OCR/layout device selection, one of `auto`, `cuda`, or `cpu`.
- `--ocr-canvas-size`: EasyOCR detector long-side canvas limit for each submitted OCR fragment.
- `--ocr-mag-ratio`: EasyOCR detector magnification ratio.
- `--ocr-batch-size`: EasyOCR recognizer batch size.
- `--no-deskew`: Disable deskew correction.
- `--no-layout`: Disable DocLayout-YOLO layout analysis and rely on EasyOCR word boxes alone.
- `--non-interactive`: Prevent console keyboard inputs. Auto-aborts on page sequence gaps unless `--ignore-missing-pages` is used.
- `--ignore-missing-pages`: Ignore missing sequence index errors and process what is available.
- `--export-debug-dir`: Path to export processed input images with text bounding boxes for quality checking.
- `--include-non-text`: Include OCR text within non-text objects like tables, figures, and graphics in the searchable PDF text overlay.
- `--no-trim`: Disable automatic page margin and white space trimming.
- `--trim-margin-chars`: Number of character widths of padding to leave around content when trimming.
- `--pdf-image-format`: Embedded page image compression format, either `jpeg` or `png`.
- `--pdf-jpeg-quality`: JPEG quality for embedded page images when `pdf_image_format=jpeg`.
- `--text-layer-vertical-offset`: Move invisible text boxes by a line-height ratio; negative values move upward.
- `--text-layer-height-scale`: Scale invisible text box height for PDF selection/highlight alignment.
- `--keep-blank-pages`: Keep blank pages in the output PDF instead of skipping them.
