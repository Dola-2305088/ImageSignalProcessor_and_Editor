# Spatial-domain test images

Synthetic images with exact known structure, so PSNR numbers mean something.
All 256x256 unless noted. Drop into `test_images/`.

| Image | Use with | Why |
|---|---|---|
| `edges_shapes.png` | Edge Detector | Square = pure H+V edges, triangle = diagonals, circle = all orientations. Each Sobel mode isolates a different part. |
| `resolution_chart.png` | Blur & Sharpen | Converging line pairs, Siemens star, single-pixel impulses. An impulse convolved with a kernel *is* the kernel — the cleanest visual check. |
| `zoneplate.png` | Image Resizer | sin(r^2): frequency rises with radius. Downsampling folds high frequencies into fake low-frequency rings. |
| `checker_fine.png` | Image Resizer | 3px checker. Nearest downsampling produces strong moire; anti-aliasing flattens it to grey. |
| `smooth_scene.png` | Noise Cleaner | Flat patches (noise obvious), gradients (over-smoothing obvious), hard + curved edges (mean vs median differ). |
| `text_grid.png` | Motion Blur -> Restoration | Text and bar gratings make direction obvious; the impulse grid shows the blur kernel directly. |
| `color_blocks.png` | any RGB path | Pure R/G/B/Y blocks. If channels swap anywhere, you see it instantly. |
| `small_scene.png` | Separable Blur | 128x128, for timing runs. |
| `small_text.png` | Restoration | 128x128. |
| `small_chart.png` | Blur & Sharpen | 128x128. |

## Measured on this set

Verified against the actual algorithms in `algorithms/spatial/`.

**Noise Cleaner** — `smooth_scene.png`

    salt & pepper   noisy 18.15   mean 25.88   median 39.57 dB
    gaussian        noisy 22.28   mean 28.60   gaussian 29.05 dB

Median beats mean by ~14 dB on impulse noise; on Gaussian noise the two are
within 0.5 dB. That contrast is the whole point of the feature.

**Image Resizer** — 256 -> 64, pixel std-dev of the result

    zoneplate   nearest 89.9   bilinear 76.2   anti-aliased 27.3
    checker     nearest 111.7  bilinear 75.6   anti-aliased 1.4

The checker collapsing to std 1.4 (near-uniform grey) is correct: at 64x64
the alternating pattern cannot be represented, so pre-filtering averages it away.

**Motion Blur -> Restoration** — `text_grid.png`, length 15, angle 0

    clean blur    blurred 16.0   inverse 30.5   wiener 24.3 dB

With no noise, naive inverse filtering wins. Add noise and it collapses:

    sigma   blurred  inverse   best wiener
    2       16.0     13.6      20.5  (K=0.001)
    5       15.9      7.6      18.1  (K=0.01)
    10      15.7      5.4      16.6  (K=0.02)

Inverse filtering loses 8-10 dB as noise rises while Wiener stays stable, and
the optimal K grows with the noise level. Use sigma=5, K=0.01 for the demo:
inverse drops to 7.6 dB, Wiener holds 18.1 dB — a 10.5 dB gap on screen.

**Separable Blur** — `small_scene.png`, 7x7, sigma 1.5

    full 2D 0.2s | separable 0.1s | 1.80x

## Size warning

Your existing `Test1`-`Test6` images are 1536x1024 to 2048x2048. Manual
convolution is O(pixels x K^2) in pure Python — a 2048x2048 image is 64x more
work than 256x256, which turns a 1-second operation into over a minute. Use
256x256 for interactive testing and 128x128 for timing comparisons.
