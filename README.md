# 3D Pen Skeleton

Upload a photo, get a printable template for a 3D-pen frame of the main object:

- **Profile**: the object's outline, with numbered lines where each rib attaches and lettered lines for the rings.
- **Ribs**: front-view cross sections, numbered and color-coded, stacked on a shared center line by default.
- **Rings**: top-view cross sections, lettered.
- **Ticks** on ribs and rings mark where pieces cross, drawn in the other piece's color.
- **Scale bar**: 50 mm, so you can confirm the print came out at 100%.

Trace every piece on paper with the 3D pen, peel them off, and stand the ribs up on the profile at their numbered lines.

## Run

```powershell
.\start.cmd          # builds the frontend, serves everything at http://127.0.0.1:8000
```

`start.cmd` runs `start.ps1` with a one-off execution-policy bypass. Windows blocks `.ps1` scripts by default, so `.\start.ps1` on its own fails.

The first upload downloads the background-removal model (~180 MB, cached in `~\.rembg`).

Development (hot reload):

```powershell
cd backend;  .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
cd frontend; npm run dev        # http://localhost:5173, proxies /api to :8000
```

Command line:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.cli photo.jpg -o template.pdf --detail 3 --size 15
```

Tests: `cd backend; .\.venv\Scripts\python.exe -m pytest`

## How it works

1. **Cut-out** (`segment.py`): rembg (`isnet-general-use`) removes the background. PNGs that are already transparent skip this step. The largest object is kept and small holes are filled.
2. **Inflate** (`inflate.py`): solves `lap(u) = -1` inside the outline and takes `h = sqrt(4u)`. A disk becomes an exact sphere and a strip becomes a round tube, so thin parts stay thin. The object is assumed mirror-symmetric front to back.
3. **Slice** (`slicer.py`): each rib is the loop `|depth| < h(x, y)` at a fixed x. Rings are the same at a fixed y. Parts that split (legs, ears) give several loops.
4. **Clean up** (`curves.py`): resample, smooth, and simplify each curve.
5. **Layout** (`pipeline.py`, `layout.py`): scale to real millimetres, label, and first-fit pack onto A4 or Letter pages.
6. **Render** (`render.py`): SVG for the live preview, PDF (reportlab) for printing.

The **Detail** slider (1–5) sets the rib and ring counts, smoothing, simplification, and the smallest part kept. **Thickness** scales the depth. **Advanced** lets you override the rib and ring counts.

## Tips and limits

- Use a **side view** on a plain background. The photo becomes the profile.
- Depth is estimated, not measured. Use **Thickness** if the object is flatter or fatter than it looks.
- Parts that overlap in the photo (an arm in front of the body) merge into one outline.
- A piece larger than the page triggers a warning with the largest size that fits.
