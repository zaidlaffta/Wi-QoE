#normalizes the result to fit between 1 and 100 using a logistic (sigmoid) function.

import re
import math
import pandas as pd

def extract_qoe_metrics_from_text(file_path, output_csv="qoe_output.csv"):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    # Regex patterns
    patterns = {
        'bitrate': re.compile("Playing bitrate \\(a/v\\): \\d+ / (\\d+)", re.IGNORECASE),
        'vmaf': re.compile("Playing/Buffering vmaf: (\\d+)", re.IGNORECASE),
        'buffer_seconds': re.compile("Buffer size in Seconds \\(a/v\\): [\\d.]+ / ([\\d.]+)", re.IGNORECASE),
        'throughput': re.compile("Throughput: (\\d+)", re.IGNORECASE),
        'rebuffer': re.compile("Buffering state: (.+)", re.IGNORECASE),
        'dropped_frames': re.compile("Total Dropped Frames: (\\d+)", re.IGNORECASE)
    }

    # Parse blocks
    records = []
    current = {}
    for line in lines:
        if "MovieId:" in line and current:
            records.append(current)
            current = {}
        for key, pattern in patterns.items():
            match = pattern.search(line)
            if match:
                current[key] = match.group(1).strip()
    if current:
        records.append(current)

    # QoE parameters (as in SIGCOMM paper)
    λ = 1        # penalty for quality variation same sy Yin et al. 2015
    μ = 4.3      # penalty for rebuffering time same sy Yin et al. 2015
    μs = 2.66    # penalty for startup delay same sy Yin et al. 2015
    Ts = 1.5     # fixed startup delay in seconds as the avaerge startup time is

    data = []
    prev_q = None
    for rec in records:
        try:
            # Parse values
            q = int(rec['vmaf'])
            bitrate = int(rec['bitrate'])
            throughput = max(int(rec.get('throughput', bitrate)), 1)  # avoid divide-by-zero
            buf_sec = float(rec.get('buffer_seconds', 0))

            # Calculate rebuffer penalty
            rebuffer = max((bitrate / throughput) - buf_sec, 0)
            rebuffer = min(rebuffer, 2)  # cap to 2 seconds

            # Calculate quality variation
            delta_q = abs(q - prev_q) if prev_q is not None else 0
            prev_q = q

            # Raw SIGCOMM QoE formula
            qoe_raw = q - λ * delta_q - μ * rebuffer - μs * Ts

            # Normalize to [1, 100] using logistic transformation
            # You can adjust the 0.01 and 500 for scale sensitivity
            qoe_normalized = 1 + 99 / (1 + math.exp(-0.01 * (qoe_raw - 500)))
            rec['QoE_score'] = round(qoe_normalized, 2)

            data.append(rec)
        except Exception as e:
            print("Skipping record due to:", e)

    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)
    print("QoE metrics written to", output_csv)

extract_qoe_metrics_from_text("raw_data.txt", "qoe_output.csv")
