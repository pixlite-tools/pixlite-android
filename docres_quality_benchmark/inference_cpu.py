"""
CPU-compatible DocRes benchmark driver.

Reuses the official DocRes model/utility code vendored under repo/ unchanged
(models/restormer_arch.py, utils.py, data/preprocess/crop_merge_image.py,
data/MBD/infer.py) but reimplements the five task functions from the
official repo/inference.py with .float() in place of .half(), since FP16 on
CPU is CUDA-oriented and unsupported for most of the ops this model uses.
No change to model architecture or weights -- precision/device only.

Does not apply any additional OpenCV filter, sharpening, or enhancement to
DocRes output. Every stage's wall-clock time and exact input/output pixel
dimensions are recorded, along with whether internal resizing/padding
occurred, per the benchmark requirements.
"""
import os
import sys
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch

BENCH_DIR = Path(__file__).resolve().parent
REPO_DIR = BENCH_DIR / "repo"

# Resolve CLI paths to absolute *before* chdir'ing into REPO_DIR below --
# otherwise relative paths like "input/document.jpg" (relative to the
# original working directory) silently resolve against repo/ instead and
# fail with a cryptic "can't open/read file".
#
# Usage: python inference_cpu.py <task> <input_image> <out_dir>
# <task> is one of: original, deshadowing, appearance, deblurring,
# binarization, end2end. Each invocation handles exactly one task and exits
# -- CI runs each task as its own workflow step/process so that one task's
# peak memory is fully released (process exit) before the next task starts,
# instead of accumulating across tasks in one long-lived interpreter.
_ARGV_TASK = sys.argv[1] if len(sys.argv) > 1 else None
_ARGV_INPUT_IMAGE = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None
_ARGV_OUT_DIR = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else None

os.chdir(REPO_DIR)
# Order matters: both repo/utils.py and repo/data/MBD/utils.py exist. The
# official inference.py relies on the top-level one winning for `import
# utils` (it appends data/MBD to sys.path, i.e. LOWEST priority) -- repo's
# utils.py is a superset that also defines the cvimg2torch/torch2cvimg
# functions data/MBD/infer.py needs, so one shared module satisfies both.
# Insert data/MBD first (lower priority), then REPO_DIR last so it ends up
# at sys.path[0] and wins the name collision.
sys.path.insert(0, str(REPO_DIR / "data" / "MBD"))
sys.path.insert(0, str(REPO_DIR))

import utils  # repo/utils.py
from utils import convert_state_dict
from models import restormer_arch
from data.preprocess.crop_merge_image import stride_integral
from data.MBD.infer import net1_net2_infer_single_im

DEVICE = torch.device("cpu")
# Lowered from the official 1600: a single 1600x1600 6-channel FP32
# Restormer forward pass alone (isolated in its own process) still got the
# GitHub-hosted runner OOM-killed ("runner has received a shutdown
# signal"), so this is a disclosed, hardware-forced practical ceiling for
# CPU-only inference on a standard runner, not an arbitrary choice.
MAX_SIZE = 1024

MBD_MODEL_PATH = str(BENCH_DIR / "weights" / "MBD" / "mbd.pkl")
DOCRES_MODEL_PATH = str(BENCH_DIR / "weights" / "DocRes" / "docres.pkl")


# ---------------------------------------------------------------------------
# Prompt helpers -- copied from the official inference.py unchanged. Pure
# OpenCV/NumPy, no torch precision involved, so no CPU-compatibility issue.
# ---------------------------------------------------------------------------

def dewarp_prompt(img):
    mask = net1_net2_infer_single_im(img, MBD_MODEL_PATH)
    base_coord = utils.getBasecoord(256, 256) / 256
    img[mask == 0] = 0
    mask = cv2.resize(mask, (256, 256)) / 255
    return img, np.concatenate((base_coord, np.expand_dims(mask, -1)), -1)


def deshadow_prompt(img):
    h, w = img.shape[:2]
    img = cv2.resize(img, (1024, 1024))
    rgb_planes = cv2.split(img)
    bg_imgs = []
    result_norm_planes = []
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7, 7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        bg_imgs.append(bg_img)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_norm_planes.append(norm_img)
    bg_imgs = cv2.merge(bg_imgs)
    bg_imgs = cv2.resize(bg_imgs, (w, h))
    return bg_imgs


def deblur_prompt(img):
    x = cv2.Sobel(img, cv2.CV_16S, 1, 0)
    y = cv2.Sobel(img, cv2.CV_16S, 0, 1)
    absX = cv2.convertScaleAbs(x)
    absY = cv2.convertScaleAbs(y)
    high_frequency = cv2.addWeighted(absX, 0.5, absY, 0.5, 0)
    high_frequency = cv2.cvtColor(high_frequency, cv2.COLOR_BGR2GRAY)
    high_frequency = cv2.cvtColor(high_frequency, cv2.COLOR_GRAY2BGR)
    return high_frequency


def appearance_prompt(img):
    h, w = img.shape[:2]
    img = cv2.resize(img, (1024, 1024))
    rgb_planes = cv2.split(img)
    result_norm_planes = []
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7, 7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_norm_planes.append(norm_img)
    result_norm = cv2.merge(result_norm_planes)
    result_norm = cv2.resize(result_norm, (w, h))
    return result_norm


def binarization_promptv2(img):
    result, thresh = utils.SauvolaModBinarization(img)
    thresh = thresh.astype(np.uint8)
    result[result > 155] = 255
    result[result <= 155] = 0

    x = cv2.Sobel(img, cv2.CV_16S, 1, 0)
    y = cv2.Sobel(img, cv2.CV_16S, 0, 1)
    absX = cv2.convertScaleAbs(x)
    absY = cv2.convertScaleAbs(y)
    high_frequency = cv2.addWeighted(absX, 0.5, absY, 0.5, 0)
    high_frequency = cv2.cvtColor(high_frequency, cv2.COLOR_BGR2GRAY)
    return np.concatenate(
        (np.expand_dims(thresh, -1), np.expand_dims(high_frequency, -1), np.expand_dims(result, -1)), -1
    )


# ---------------------------------------------------------------------------
# Task functions -- float32 CPU versions of the official inference.py tasks.
# ---------------------------------------------------------------------------

def dewarping(model, im_path):
    INPUT_SIZE = 256
    im_org = cv2.imread(im_path)
    im_masked, prompt_org = dewarp_prompt(im_org.copy())

    h, w = im_masked.shape[:2]
    im_masked = cv2.resize(im_masked.copy(), (INPUT_SIZE, INPUT_SIZE))
    im_masked = im_masked / 255.0
    im_masked = torch.from_numpy(im_masked.transpose(2, 0, 1)).unsqueeze(0).float().to(DEVICE)

    prompt = torch.from_numpy(prompt_org.transpose(2, 0, 1)).unsqueeze(0).float().to(DEVICE)
    in_im = torch.cat((im_masked, prompt), dim=1)

    base_coord = utils.getBasecoord(INPUT_SIZE, INPUT_SIZE) / INPUT_SIZE
    model = model.float()
    with torch.no_grad():
        pred = model(in_im)
        pred = pred[0][:2].permute(1, 2, 0).cpu().numpy()
        pred = pred + base_coord
    for _ in range(15):
        pred = cv2.blur(pred, (3, 3), borderType=cv2.BORDER_REPLICATE)
    pred = cv2.resize(pred, (w, h)) * (w, h)
    pred = pred.astype(np.float32)
    out_im = cv2.remap(im_org, pred[:, :, 0], pred[:, :, 1], cv2.INTER_LINEAR)
    return out_im, {"resized": True, "note": "flow predicted at 256x256, remapped onto original-resolution image"}


def appearance(model, im_path):
    im_org = cv2.imread(im_path)
    h, w = im_org.shape[:2]
    prompt = appearance_prompt(im_org)
    in_im = np.concatenate((im_org, prompt), -1)

    resized_note = {"resized": False}
    if max(w, h) < MAX_SIZE:
        in_im, padding_h, padding_w = stride_integral(in_im, 8)
        resized_note = {"resized": False, "padded_to_multiple_of_8": True, "padded_shape": list(in_im.shape[:2])}
    else:
        in_im = cv2.resize(in_im, (MAX_SIZE, MAX_SIZE))
        resized_note = {"resized": True, "reason": f"max(w,h)={max(w,h)} >= MAX_SIZE={MAX_SIZE}", "resized_to": [MAX_SIZE, MAX_SIZE]}

    in_im = in_im / 255.0
    in_im = torch.from_numpy(in_im.transpose(2, 0, 1)).unsqueeze(0).float().to(DEVICE)
    model = model.float()
    with torch.no_grad():
        pred = model(in_im)
        pred = torch.clamp(pred, 0, 1)
        pred = pred[0].permute(1, 2, 0).cpu().numpy()
        pred = (pred * 255).astype(np.uint8)

        if max(w, h) < MAX_SIZE:
            out_im = pred[padding_h:, padding_w:]
        else:
            pred[pred == 0] = 1
            shadow_map = cv2.resize(im_org, (MAX_SIZE, MAX_SIZE)).astype(float) / pred.astype(float)
            shadow_map = cv2.resize(shadow_map, (w, h))
            shadow_map[shadow_map == 0] = 0.00001
            out_im = np.clip(im_org.astype(float) / shadow_map, 0, 255).astype(np.uint8)
    return out_im, resized_note


def deshadowing(model, im_path):
    im_org = cv2.imread(im_path)
    h, w = im_org.shape[:2]
    prompt = deshadow_prompt(im_org)
    in_im = np.concatenate((im_org, prompt), -1)

    if max(w, h) < MAX_SIZE:
        in_im, padding_h, padding_w = stride_integral(in_im, 8)
        resized_note = {"resized": False, "padded_to_multiple_of_8": True, "padded_shape": list(in_im.shape[:2])}
    else:
        in_im = cv2.resize(in_im, (MAX_SIZE, MAX_SIZE))
        resized_note = {"resized": True, "reason": f"max(w,h)={max(w,h)} >= MAX_SIZE={MAX_SIZE}", "resized_to": [MAX_SIZE, MAX_SIZE]}

    in_im = in_im / 255.0
    in_im = torch.from_numpy(in_im.transpose(2, 0, 1)).unsqueeze(0).float().to(DEVICE)
    model = model.float()
    with torch.no_grad():
        pred = model(in_im)
        pred = torch.clamp(pred, 0, 1)
        pred = pred[0].permute(1, 2, 0).cpu().numpy()
        pred = (pred * 255).astype(np.uint8)

        if max(w, h) < MAX_SIZE:
            out_im = pred[padding_h:, padding_w:]
        else:
            pred[pred == 0] = 1
            shadow_map = cv2.resize(im_org, (MAX_SIZE, MAX_SIZE)).astype(float) / pred.astype(float)
            shadow_map = cv2.resize(shadow_map, (w, h))
            shadow_map[shadow_map == 0] = 0.00001
            out_im = np.clip(im_org.astype(float) / shadow_map, 0, 255).astype(np.uint8)
    return out_im, resized_note


def _cap_for_memory(im_org):
    """
    deblurring/binarization have no resolution cap in the official code
    (only multiple-of-8 padding at native resolution). At this image's
    native size that alone was enough to OOM-kill the CPU runner, so this
    downscales (aspect-preserving) before padding when needed. Disclosed
    explicitly via the returned resize_info, matching the deshadowing/
    appearance cap above.
    """
    h, w = im_org.shape[:2]
    if max(h, w) <= MAX_SIZE:
        return im_org, {"resized": False}
    scale = MAX_SIZE / max(h, w)
    resized = cv2.resize(im_org, (int(round(w * scale)), int(round(h * scale))))
    return resized, {
        "resized": True,
        "reason": f"max(w,h)={max(w,h)} > MAX_SIZE={MAX_SIZE} (CPU memory constraint)",
        "resized_to": [resized.shape[1], resized.shape[0]],
    }


def deblurring(model, im_path):
    im_org = cv2.imread(im_path)
    orig_h, orig_w = im_org.shape[:2]
    im_org, cap_info = _cap_for_memory(im_org)
    in_im, padding_h, padding_w = stride_integral(im_org, 8)
    prompt = deblur_prompt(in_im)
    in_im = np.concatenate((in_im, prompt), -1)
    in_im = in_im / 255.0
    in_im = torch.from_numpy(in_im.transpose(2, 0, 1)).unsqueeze(0).float().to(DEVICE)
    model = model.to(DEVICE)
    model.eval()
    model = model.float()
    with torch.no_grad():
        pred = model(in_im)
        pred = torch.clamp(pred, 0, 1)
        pred = pred[0].permute(1, 2, 0).cpu().numpy()
        pred = (pred * 255).astype(np.uint8)
        out_im = pred[padding_h:, padding_w:]
    cap_info["padded_to_multiple_of_8"] = True
    cap_info["padded_shape"] = list(in_im.shape[-2:])
    cap_info["output_upscaled_to_original"] = False
    return out_im, cap_info


def binarization(model, im_path):
    im_org = cv2.imread(im_path)
    im_org, cap_info = _cap_for_memory(im_org)
    im, padding_h, padding_w = stride_integral(im_org, 8)
    prompt = binarization_promptv2(im)
    h, w = im.shape[:2]
    in_im = np.concatenate((im, prompt), -1)

    in_im = in_im / 255.0
    in_im = torch.from_numpy(in_im.transpose(2, 0, 1)).unsqueeze(0).float().to(DEVICE)
    model = model.float()
    with torch.no_grad():
        pred = model(in_im)
        pred = pred[:, :2, :, :]
        pred = torch.max(torch.softmax(pred, 1), 1)[1]
        pred = pred[0].cpu().numpy()
        pred = (pred * 255).astype(np.uint8)
        pred = cv2.resize(pred, (w, h))
        out_im = pred[padding_h:, padding_w:]
    cap_info["padded_to_multiple_of_8"] = True
    cap_info["padded_shape"] = [h, w]
    return out_im, cap_info


def model_init(model_path):
    model = restormer_arch.Restormer(
        inp_channels=6,
        out_channels=3,
        dim=48,
        num_blocks=[2, 3, 3, 4],
        num_refinement_blocks=4,
        heads=[1, 2, 4, 8],
        ffn_expansion_factor=2.66,
        bias=False,
        LayerNorm_type="WithBias",
        dual_pixel_task=True,
    )
    state = convert_state_dict(torch.load(model_path, map_location="cpu")["model_state"])
    model.load_state_dict(state)
    model.eval()
    return model.to(DEVICE)


def dims(img):
    h, w = img.shape[:2]
    return {"width": int(w), "height": int(h)}


def write_fragment(out_dir, task, entry):
    with open(out_dir / f"_fragment_{task}.json", "w") as f:
        json.dump({task: entry}, f, indent=2)


def main():
    task = _ARGV_TASK
    input_image = _ARGV_INPUT_IMAGE
    out_dir = Path(_ARGV_OUT_DIR) if _ARGV_OUT_DIR else (BENCH_DIR / "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    if task == "original":
        t0 = time.time()
        orig = cv2.imread(input_image)
        if orig is None:
            raise SystemExit(f"Could not read input image: {input_image}")
        cv2.imwrite(str(out_dir / "original.png"), orig)
        write_fragment(out_dir, "original", {
            "time_sec": round(time.time() - t0, 3),
            "output_dims": dims(orig),
            "resize_info": {"resized": False},
            "output_file": "original.png",
        })
        print(f"original: {dims(orig)}")
        return

    print(f"Loading docres.pkl for task={task} ...")
    model = model_init(DOCRES_MODEL_PATH)

    if task in ("deshadowing", "appearance", "deblurring", "binarization"):
        fn = {"deshadowing": deshadowing, "appearance": appearance,
              "deblurring": deblurring, "binarization": binarization}[task]
        print(f"Running {task} ...")
        t0 = time.time()
        out_im, resize_info = fn(model, input_image)
        elapsed = time.time() - t0
        out_path = out_dir / f"{task}.png"
        cv2.imwrite(str(out_path), out_im)
        write_fragment(out_dir, task, {
            "time_sec": round(elapsed, 3),
            "output_dims": dims(out_im),
            "resize_info": resize_info,
            "output_file": out_path.name,
        })
        print(f"  {task}: {elapsed:.2f}s, output {dims(out_im)}, resize_info={resize_info}")
        return

    if task == "end2end":
        # dewarping -> deshadowing -> appearance, chained. Intermediates are
        # kept as PNG (not the reference script's JPG) to avoid an unrelated
        # compression confound in this quality benchmark.
        print("Running end2end ...")
        t0 = time.time()
        step1_im, step1_info = dewarping(model, input_image)
        step1_path = out_dir / "_end2end_step1_dewarping.png"
        cv2.imwrite(str(step1_path), step1_im)

        step2_im, step2_info = deshadowing(model, str(step1_path))
        step2_path = out_dir / "_end2end_step2_deshadowing.png"
        cv2.imwrite(str(step2_path), step2_im)

        step3_im, step3_info = appearance(model, str(step2_path))
        elapsed = time.time() - t0
        end2end_path = out_dir / "end2end.png"
        cv2.imwrite(str(end2end_path), step3_im)
        write_fragment(out_dir, "end2end", {
            "time_sec": round(elapsed, 3),
            "output_dims": dims(step3_im),
            "resize_info": {
                "step1_dewarping": step1_info,
                "step2_deshadowing": step2_info,
                "step3_appearance": step3_info,
            },
            "output_file": "end2end.png",
            "note": "chained dewarping -> deshadowing -> appearance, matching the official end2end pipeline; intermediates kept as PNG",
        })
        print(f"  end2end: {elapsed:.2f}s, output {dims(step3_im)}")
        return

    raise SystemExit(f"Unknown task: {task}")


if __name__ == "__main__":
    main()
