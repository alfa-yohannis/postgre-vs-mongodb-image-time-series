import re

with open("../paper/icct_alfa_yohannis_2.tex", "r") as f:
    text = f.read()

replacements = [
    (r"MongoDB fails completely at 6K due to memory exhaustion\.",
     r"MongoDB encountered processing failures at 6K due to cache pressure and document limits."),
    
    (r"None of these studies incorporate binary payloads exceeding a few kilobytes\.",
     r"These studies typically do not incorporate binary payloads exceeding a few kilobytes."),
    
    (r"the first systematic multi-resolution benchmark",
     r"a systematic multi-resolution benchmark"),
     
    (r"A 100-record warm-up phase pre-loads memory\. The insertion benchmark commits 1000 records in batches of 50 per run\.",
     r"A 10-record warm-up phase pre-loads memory. The insertion benchmark commits 100 records in batches of 50 per run."),
     
    (r"representing up to 1\.6~GB of raw transfer",
     r"representing up to 0.65~GB of raw transfer"),
     
    (r"at 6K, MongoDB fails entirely due to WiredTiger Out-Of-Memory \(OOM\) caching limits\.",
     r"at 6K, MongoDB fails to process the payload, likely due to severe WiredTiger cache pressure and internal document limits."),
     
    (r"the 1\.6~GB target across the network in 8\.2~s\.",
     r"the 0.65~GB target across the network in 8.2~s."),
     
    (r"explains the steep throughput decline observed between 1080p \(55 docs/s\) and 4K \(4\.2 docs/s\)",
     r"explains the steep throughput decline observed between 1080p (133.2 docs/s) and 4K (4.6 docs/s)"),
     
    (r"ultimately leading to the total engine failure observed at 6K resolution\.",
     r"contributing to the engine failure observed at 6K resolution."),
     
    (r"is decisively superior across all metrics",
     r"provides more stable performance across most metrics"),
     
    (r"total engine failure at 6K due to WiredTiger memory thrashing",
     r"engine failure at 6K under high memory pressure"),
     
    (r"is decisively superior for high-resolution vision streams",
     r"proves more robust for high-resolution vision streams")
]

for old, new in replacements:
    text = re.sub(old, new, text)

with open("../paper/icct_alfa_yohannis_2.tex", "w") as f:
    f.write(text)

print("Paper improved.")
