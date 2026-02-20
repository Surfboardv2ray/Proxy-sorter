import os, random, re

input_file = 'output/converted.txt'
output_file = 'selector/random.txt'
num_lines_to_select = 100

os.makedirs(os.path.dirname(output_file), exist_ok=True)

protocol_re = re.compile(r'^(?:vless|vmess|trojan)://', re.I)
html_markers = ('<!doctype', '<html', 'please enable cookies', 'worker threw exception', 'cloudflare ray id')

with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
    raw_lines = [line.rstrip('\n') for line in f]

# Filter: keep only protocol lines and drop obvious HTML/error pages
clean_lines = [
    ln for ln in raw_lines
    if protocol_re.match(ln.strip())
    and not any(mark in ln.lower() for mark in html_markers)
]

if not clean_lines:
    # Helpful debug output so CI logs show what's wrong
    print(f"No protocol lines found after filtering. Total input lines: {len(raw_lines)}")
    # Optionally write a small debug sample of input to help troubleshooting
    debug_sample = raw_lines[:50]
    with open(output_file, 'w', encoding='utf-8') as fout:
        fout.write('\n'.join(debug_sample))
else:
    k = min(num_lines_to_select, len(clean_lines))
    selected = random.sample(clean_lines, k)
    with open(output_file, 'w', encoding='utf-8') as fout:
        fout.write('\n'.join(selected))

print(f"Wrote {min(num_lines_to_select, len(clean_lines))} lines to {output_file}")
